"""LLM 供应商连通性自检

用法：
    python check_llm.py            # 测当前生效的供应商
    python check_llm.py glm        # 指定供应商
    python check_llm.py all        # 逐个测试所有已配置的供应商

会打印实际用到的 endpoint、模型、耗时、token 消耗和推理 token 占比，
方便确认 key 是否可用、max_tokens 预算是否够。
"""

import sys
import time

from dotenv import load_dotenv

load_dotenv()

import config as _cfg  # noqa: E402  必须在 load_dotenv 之后导入
from llm.common.base import Conversation  # noqa: E402
from llm.common.factory import LLMFactory  # noqa: E402

PROBE = '请用一句话说明六爻中的"世爻"是什么。'


def check(provider):
    print(f'\n===== {provider} =====')
    try:
        client = LLMFactory.create(provider)
    except Exception as e:
        print(f'  [FAIL] 客户端创建失败: {e}')
        return False

    print(f'  endpoint : {client.api_base}')
    print(f'  model    : {client.model}')
    if client.extra_params:
        print(f'  额外参数 : {client.extra_params}')

    started = time.time()
    try:
        response = client.chat_completion_sync(
            Conversation().get_messages() + [{'role': 'user', 'content': PROBE}],
            temperature=_cfg.LLM_TEMPERATURE,
            max_tokens=_cfg.LLM_MAX_TOKENS,
        )
        content = client._extract_content(response)
    except Exception as e:
        print(f'  [FAIL] 调用失败（耗时 {time.time() - started:.1f}s）: {e}')
        return False

    elapsed = time.time() - started
    usage = response.get('usage') or {}
    completion = usage.get('completion_tokens')
    reasoning = (usage.get('completion_tokens_details') or {}).get('reasoning_tokens')
    print(f'  [OK] 成功，耗时 {elapsed:.1f}s，正文 {len(content)} 字')
    print(f'  token    : prompt={usage.get("prompt_tokens")} completion={completion} 其中推理={reasoning}')
    if reasoning and completion:
        print(f'  推理占比 : {reasoning / completion:.0%}（预算 max_tokens={_cfg.LLM_MAX_TOKENS}）')
    print(f'  回复     : {content.strip()[:80]}')
    return True


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg == 'all':
        providers = list(_cfg.LLM_PROVIDERS)
    elif arg:
        providers = [arg]
    else:
        import dialog_manager
        providers = [dialog_manager.DialogManager.get_provider()]

    results = {p: check(p) for p in providers}
    print()
    for provider, ok in results.items():
        print(f'{provider}: {"可用" if ok else "不可用"}')
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
