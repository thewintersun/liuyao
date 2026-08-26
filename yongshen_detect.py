"""用神自动判定 —— 影子模式

只观察，不参与线上取用神。每次解卦后在后台线程里额外判定一次，
把「用户自己选的类别」和「系统判定的类别」一并记录，用于评估
自动判定的准确率，为将来撤掉分类选择页提供依据。

设计约束：绝不影响解卦主流程。判定在独立线程里跑，异常一律吞掉
只记日志；即使这里整个挂掉，用户侧也应当毫无感知。
"""

import logging
import random
import re
import threading
import time

import config as _cfg
from auth import record_yongshen_shadow
from llm.common.base import Conversation
from llm.common.factory import LLMFactory

logger = logging.getLogger(__name__)

# 判定结果的合法取值。「世爻」对应自占自身。
VALID_CHOICES = ('父母', '兄弟', '子孙', '妻财', '官鬼', '世爻')

# 用户选的类别与判定结果的对照口径：分类页的「自占自身」即取世爻
USER_CHOICE_ALIAS = {'自占自身': '世爻'}

DETECT_PROMPT = """你是六爻取用神助手。根据求测者的问题，判断应取哪个六亲为用神。

取用神规则：
- 父母：父母长辈、房屋、车辆、合同文书、证书、考试学业、搬迁
- 兄弟：兄弟姐妹、朋友同事、合作伙伴本人如何
- 子孙：子女晚辈、宠物、求平安消灾、看病能否治好、用药是否对症
- 妻财：钱财收入、工资、投资、生意、创业收益、买卖、要账；男性求测者问妻子或女友
- 官鬼：工作职位、求职升职、考核、官司、领导上司；女性求测者问丈夫或男友；疾病的病情
- 世爻：单纯问自己近期整体状态、运势走向，没有具体所指的事

注意：
- 凡问感情、婚姻、桃花、缘分，哪怕没有具体对象（如「今年会有新感情吗」），
  也要按性别取官鬼或妻财，不可取世爻。
- 感情类用神取决于求测者性别——女问男方取官鬼，男问女方取妻财。
  可从问题措辞推断（如「我男朋友」多为女性视角）；实在无从判断时默认取官鬼。
- 世爻只用于完全没有具体所指的整体运势问题。
- 若问题包含多件事，选其中最主要的那一件。

求测者的问题：{question}

严格按以下两行格式回答，不要有其他内容：
用神：<从 父母/兄弟/子孙/妻财/官鬼/世爻 中选一个>
理由：<十五字以内>"""

# 判定用的输出预算：只要两行，给小一点避免模型长篇大论
DETECT_MAX_TOKENS = 2048


def _parse(text):
    """从模型回复里取出用神与理由，取不到返回 (None, 原文片段)"""
    choice = None
    match = re.search(r'用神\s*[：:]\s*([一-龥]{2})', text)
    if match and match.group(1) in VALID_CHOICES:
        choice = match.group(1)
    else:
        # 回复没按格式来，退而求其次在全文里找一个合法取值
        for candidate in VALID_CHOICES:
            if candidate in text:
                choice = candidate
                break

    reason = ''
    match = re.search(r'理由\s*[：:]\s*(.+)', text)
    if match:
        reason = match.group(1).strip()[:60]
    elif not choice:
        reason = ' '.join(text.split())[:60]

    return choice, reason


def detect(question):
    """判定用神，返回 (choice, reason, elapsed_ms, provider, error)"""
    provider = None
    started = time.time()
    try:
        import dialog_manager
        provider = dialog_manager.DialogManager.get_provider()
        client = LLMFactory.create(provider)
        text = client.chat_sync(
            Conversation(),
            DETECT_PROMPT.format(question=question),
            temperature=_cfg.LLM_TEMPERATURE,
            max_tokens=DETECT_MAX_TOKENS,
        )
        choice, reason = _parse(text)
        elapsed = int((time.time() - started) * 1000)
        if choice is None:
            return None, reason, elapsed, provider, '无法从回复中解析出用神'
        return choice, reason, elapsed, provider, None
    except Exception as e:
        elapsed = int((time.time() - started) * 1000)
        return None, '', elapsed, provider, str(e)[:200]


def _run(session_id, user_id, question, user_choice):
    choice, reason, elapsed, provider, error = detect(question)
    normalized_user = USER_CHOICE_ALIAS.get(user_choice, user_choice)
    agreed = None
    if choice and normalized_user:
        agreed = 1 if choice == normalized_user else 0
    record_yongshen_shadow(
        session_id=session_id,
        user_id=user_id,
        question=question,
        user_choice=user_choice,
        llm_choice=choice,
        llm_reason=reason,
        agreed=agreed,
        elapsed_ms=elapsed,
        provider=provider,
        error=error,
    )
    logger.info(
        f'用神影子判定 session={session_id} 用户选={user_choice} '
        f'判定={choice} 一致={agreed} 耗时={elapsed}ms'
        + (f' 错误={error}' if error else '')
    )


def observe(session_id, user_id, question, user_choice):
    """在后台线程里判定并记录。任何异常都不得冒泡到调用方。"""
    if not _cfg.YONGSHEN_SHADOW_ENABLED:
        return
    if not question or not question.strip():
        return
    rate = _cfg.YONGSHEN_SHADOW_SAMPLE_RATE
    if rate < 1.0 and random.random() > rate:
        return
    try:
        thread = threading.Thread(
            target=_safe_run,
            args=(session_id, user_id, question.strip(), user_choice),
            daemon=True,
        )
        thread.start()
    except Exception as e:
        logger.warning(f'用神影子判定启动失败: {e}')


def _safe_run(session_id, user_id, question, user_choice):
    try:
        _run(session_id, user_id, question, user_choice)
    except Exception as e:
        logger.warning(f'用神影子判定失败: {e}')
        # 仍记一条，否则失败率无从统计
        try:
            record_yongshen_shadow(
                session_id=session_id, user_id=user_id, question=question,
                user_choice=user_choice, llm_choice=None, llm_reason='',
                agreed=None, elapsed_ms=None, provider=None, error=str(e)[:200],
            )
        except Exception:
            pass
