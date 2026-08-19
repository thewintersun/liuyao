import sys
import logging
from pathlib import Path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from llm.common.base import Conversation
from llm.common.config import SYSTEM_PROMPT
from llm.deepseek.client import DeepseekClient
import admin_service
import time
import uuid
from collections import OrderedDict
import config as _cfg

logger = logging.getLogger(__name__)

class DialogManager:

    TOKEN_LIMIT = _cfg.CONVERSATION_TOKEN_LIMIT

    def __init__(self):
        self.llm_client = DeepseekClient()
        self._conversation_dict = OrderedDict()
        self._max_conversations = _cfg.MAX_CONCURRENT_CONVERSATIONS
        self._conversation_timeout = _cfg.CONVERSATION_TIMEOUT_SECONDS

    def get_current_active_user_number(self):
        current_user_number = 0
        for conversation, current_time in self._conversation_dict.values():
            if time.time() - current_time > _cfg.ACTIVE_USER_WINDOW_SECONDS:
                continue
            current_user_number += 1
        return current_user_number

    def get_conversation(self, conversation_id: str, lang: str = None) -> Conversation:
        current_time = time.time()
        self._cleanup_expired_conversations(current_time)

        if conversation_id in self._conversation_dict:
            conversation, _ = self._conversation_dict[conversation_id]
            self._conversation_dict.pop(conversation_id)
            self._conversation_dict[conversation_id] = (conversation, current_time)
        else:
            if len(self._conversation_dict) >= self._max_conversations:
                self._conversation_dict.popitem(last=False)

            system_message = admin_service.get_prompt('SYSTEM_PROMPT') or SYSTEM_PROMPT
            if lang and lang.startswith('zh-TW'):
                system_message += "\n请使用繁體中文回覆。"
            conversation = Conversation(system_message)
            self._conversation_dict[conversation_id] = (conversation, current_time)

        return self._conversation_dict[conversation_id][0]

    def _cleanup_expired_conversations(self, current_time: float) -> None:
        expired_ids = []
        for conv_id, (_, last_access_time) in self._conversation_dict.items():
            if current_time - last_access_time > self._conversation_timeout:
                expired_ids.append(conv_id)

        for conv_id in expired_ids:
            self._conversation_dict.pop(conv_id, None)

    def set_conversation(self, conversation_id: str, conversation: Conversation) -> None:
        current_time = time.time()
        if conversation_id in self._conversation_dict:
            self._conversation_dict.pop(conversation_id)
        self._conversation_dict[conversation_id] = (conversation, current_time)

    def delete_conversation(self, conversation_id: str) -> None:
        if conversation_id in self._conversation_dict:
            del self._conversation_dict[conversation_id]

    @staticmethod
    def _estimate_tokens(text):
        """粗略估算 token 数：中文约 0.6 token/字，ASCII 约 0.3 token/字符"""
        cn = sum(1 for c in text if ord(c) > 127)
        en = len(text) - cn
        return int(cn * 0.6 + en * 0.3)

    @classmethod
    def _msg_tokens(cls, msg):
        return cls._estimate_tokens(msg.content) + 4  # 每条消息额外开销

    MAX_RECENT_ROUNDS = _cfg.MAX_RECENT_ROUNDS

    def _trim_conversation_history(self, conversation: Conversation) -> Conversation:
        messages = conversation.messages
        system_messages = [msg for msg in messages if msg.role == "system"]
        other_messages = [msg for msg in messages if msg.role != "system"]

        # Step 1: 轮数上限 — 保留首轮(2条) + 最近 9 轮(18条)
        max_tail = self.MAX_RECENT_ROUNDS * 2
        if len(other_messages) > 2 + max_tail:
            head = other_messages[:2]
            tail = other_messages[-max_tail:]
            other_messages = head + tail

        # Step 2: token 上限 — 超过 TOKEN_LIMIT 时从中间继续裁
        system_tokens = sum(self._msg_tokens(m) for m in system_messages)
        head = other_messages[:2] if len(other_messages) >= 2 else other_messages[:]
        head_tokens = sum(self._msg_tokens(m) for m in head)
        budget = self.TOKEN_LIMIT - system_tokens - head_tokens
        tail_pool = other_messages[len(head):]
        tail_total = sum(self._msg_tokens(m) for m in tail_pool)

        if tail_total <= budget:
            conversation.messages = system_messages + other_messages
        else:
            # 从尾部往前，尽可能多保留最近的消息
            kept_tail = []
            tail_tokens = 0
            for msg in reversed(tail_pool):
                t = self._msg_tokens(msg)
                if tail_tokens + t > budget:
                    break
                kept_tail.insert(0, msg)
                tail_tokens += t
            conversation.messages = system_messages + head + kept_tail

        return conversation

    def _aggressive_trim(self, conversation: Conversation) -> None:
        """激进裁剪：只保留 system + 首轮 + 最近 2 轮"""
        messages = conversation.messages
        system_messages = [m for m in messages if m.role == "system"]
        other = [m for m in messages if m.role != "system"]
        head = other[:2]
        tail = other[-4:] if len(other) > 6 else other[2:]
        conversation.messages = system_messages + head + tail

    def restore_conversation(self, conversation_id, messages, lang=None, reuse_id=True):
        """用历史消息重建会话

        reuse_id=True 时沿用原 conversation_id（内存会话超时/淘汰后恢复也保持同一 ID），
        使同一卦的解卦与后续追问在 usage_log 中归属同一会话。
        调用方需先确认该 conversation_id 属于当前用户，否则传 reuse_id=False。
        """
        if conversation_id in self._conversation_dict:
            return conversation_id
        system_message = admin_service.get_prompt('SYSTEM_PROMPT') or SYSTEM_PROMPT
        if lang and lang.startswith('zh-TW'):
            system_message += "\n请使用繁體中文回覆。"
        conversation = Conversation(system_message)
        for msg in messages:
            if msg['role'] == 'user':
                conversation.add_user_message(msg['content'])
            elif msg['role'] == 'assistant':
                conversation.add_assistant_message(msg['content'])
        new_id = conversation_id if (reuse_id and conversation_id) else str(uuid.uuid4())[:16]
        self.set_conversation(new_id, conversation)
        return new_id

    def process_user_message(self, conversation_id: str, message: str, lang: str = None):
        """返回 (response_text, success_bool)"""
        conversation = self.get_conversation(conversation_id, lang=lang)
        conversation = self._trim_conversation_history(conversation)

        total_tokens = sum(self._msg_tokens(m) for m in conversation.messages)
        logger.info(f'历史对话数量: {len(conversation.messages)}, 估算tokens: {total_tokens}')

        try:
            response = self.llm_client.chat_sync(
                conversation=conversation,
                user_message=message,
                temperature=_cfg.LLM_TEMPERATURE,
                max_tokens=_cfg.LLM_MAX_TOKENS,
                stream=False
            )
            self.set_conversation(conversation_id, conversation)
            return response, True
        except Exception as e:
            error_msg = str(e).lower()
            # chat_sync 内部已添加 user message，失败时需移除
            if conversation.messages and conversation.messages[-1].role == 'user':
                conversation.messages.pop()

            is_context_error = any(kw in error_msg for kw in
                                   ['context_length', 'too long', 'maximum', 'token', 'content_length'])
            if is_context_error:
                logger.warning(f'上下文过长，激进裁剪后重试: {e}')
                self._aggressive_trim(conversation)
                try:
                    response = self.llm_client.chat_sync(
                        conversation=conversation,
                        user_message=message,
                        temperature=0.7,
                        max_tokens=4096,
                        stream=False
                    )
                    self.set_conversation(conversation_id, conversation)
                    return response, True
                except Exception as retry_e:
                    logger.error(f'重试仍然失败: {retry_e}')
                    if conversation.messages and conversation.messages[-1].role == 'user':
                        conversation.messages.pop()
                    self.set_conversation(conversation_id, conversation)
                    return '抱歉，对话上下文过长导致处理失败，请尝试开始新的对话。', False
            else:
                logger.error(f'LLM 调用失败: {e}')
                self.set_conversation(conversation_id, conversation)
                return '抱歉，AI 服务暂时不可用，请稍后重试。', False
