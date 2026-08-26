"""OpenAI 兼容接口的通用客户端基类

DeepSeek 和智谱 GLM 都提供 OpenAI 兼容的 /chat/completions 接口，
差异只在 api_key / api_base / model / 额外请求参数，因此共用一套实现。

重要：openai 0.28 的 openai.api_key / openai.api_base 是模块级全局状态，
多个供应商并存时后初始化的会覆盖先初始化的。这里一律按调用传参
（create(api_key=..., api_base=...)），不写全局配置，供应商之间互不干扰。
"""

import logging
from typing import Dict, List, Any, Optional, Union, AsyncGenerator, AsyncIterable, Generator, Iterable
import openai

from .base import BaseLLM, Conversation
from .config import DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS

logger = logging.getLogger(__name__)


class OpenAICompatibleClient(BaseLLM):
    """OpenAI 兼容 API 的客户端基类，子类只需提供 key/base/model 等配置"""

    def __init__(self,
                 api_key: str,
                 api_base: str,
                 model: str,
                 provider_name: str = 'llm',
                 extra_params: Optional[Dict[str, Any]] = None):
        """
        Args:
            api_key: API 密钥
            api_base: API 基础 URL
            model: 模型名称
            provider_name: 供应商名称，仅用于日志
            extra_params: 每次请求都附加的额外参数（如 GLM 的 thinking）
        """
        if not api_key:
            raise ValueError(f"{provider_name} API 密钥未设置，请在 .env 中配置")

        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.provider_name = provider_name
        self.extra_params = dict(extra_params or {})

    # ========== 内部工具 ==========

    def _build_params(self, messages, temperature, max_tokens, stream, **kwargs):
        """组装请求参数，api_key/api_base 按调用传入以避免全局状态污染"""
        params = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': stream,
            'api_key': self.api_key,
            'api_base': self.api_base,
        }
        params.update(self.extra_params)
        params.update(kwargs)
        return params

    def _extract_content(self, response) -> str:
        """从非流式响应中提取正文，空回复视为失败抛出

        DeepSeek 的 deepseek-v4-flash 和 GLM 的 thinking 模式都会产生
        reasoning_content，且推理 token 计入 max_tokens 预算。推理过长时
        接口返回 200 但 content 为空（finish_reason='length'），必须当作
        失败，否则用户拿到空白结果，额度还会照扣。
        """
        try:
            choice = response["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"解析{self.provider_name}响应失败: {str(e)}")
            raise ValueError(f"无法从{self.provider_name}响应中提取助手回复: {str(e)}")

        finish_reason = choice.get("finish_reason")
        if not (content or "").strip():
            usage = response.get("usage") if hasattr(response, "get") else None
            logger.error(f"{self.provider_name} 返回空回复: finish_reason={finish_reason}, usage={usage}")
            raise ValueError(f"{self.provider_name} 返回空回复 (finish_reason={finish_reason})")
        if finish_reason == "length":
            logger.warning(f"{self.provider_name} 回复被截断: 长度={len(content)}，建议调高 max_tokens")

        return content

    @staticmethod
    def _extract_delta(chunk) -> Optional[str]:
        """从流式响应块中提取文本片段"""
        try:
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})
                if "content" in delta and delta["content"]:
                    return delta["content"]
        except Exception as e:
            logger.error(f"处理流式响应块失败: {str(e)}")
        return None

    # ========== chat_completion ==========

    async def chat_completion(self,
                              messages: List[Dict[str, str]],
                              temperature: float = DEFAULT_TEMPERATURE,
                              max_tokens: int = DEFAULT_MAX_TOKENS,
                              stream: bool = False,
                              **kwargs) -> Union[Dict[str, Any], AsyncIterable[Dict[str, Any]]]:
        """调用聊天完成 API（异步）"""
        try:
            response = await openai.ChatCompletion.acreate(
                **self._build_params(messages, temperature, max_tokens, stream, **kwargs)
            )
            return dict(response) if not stream else response
        except Exception as e:
            logger.error(f"{self.provider_name} API调用失败: {str(e)}")
            raise

    def chat_completion_sync(self,
                             messages: List[Dict[str, str]],
                             temperature: float = DEFAULT_TEMPERATURE,
                             max_tokens: int = DEFAULT_MAX_TOKENS,
                             stream: bool = False,
                             **kwargs) -> Union[Dict[str, Any], Iterable[Dict[str, Any]]]:
        """调用聊天完成 API（同步）"""
        try:
            response = openai.ChatCompletion.create(
                **self._build_params(messages, temperature, max_tokens, stream, **kwargs)
            )
            return dict(response) if not stream else response
        except Exception as e:
            logger.error(f"{self.provider_name} API同步调用失败: {str(e)}")
            raise

    # ========== generate_text ==========

    async def generate_text(self,
                            prompt: str,
                            temperature: float = DEFAULT_TEMPERATURE,
                            max_tokens: int = DEFAULT_MAX_TOKENS,
                            stream: bool = False,
                            **kwargs) -> Union[str, AsyncGenerator[str, None]]:
        """生成文本（异步）"""
        messages = [{"role": "user", "content": prompt}]

        if not stream:
            response = await self.chat_completion(
                messages, temperature=temperature, max_tokens=max_tokens, stream=False, **kwargs
            )
            return self._extract_content(response)

        async def text_generator() -> AsyncGenerator[str, None]:
            response_stream = await self.chat_completion(
                messages, temperature=temperature, max_tokens=max_tokens, stream=True, **kwargs
            )
            async for chunk in response_stream:
                content = self._extract_delta(chunk)
                if content:
                    yield content

        return text_generator()

    def generate_text_sync(self,
                           prompt: str,
                           temperature: float = DEFAULT_TEMPERATURE,
                           max_tokens: int = DEFAULT_MAX_TOKENS,
                           stream: bool = False,
                           **kwargs) -> Union[str, Generator[str, None, None]]:
        """生成文本（同步）"""
        messages = [{"role": "user", "content": prompt}]

        if not stream:
            response = self.chat_completion_sync(
                messages, temperature=temperature, max_tokens=max_tokens, stream=False, **kwargs
            )
            return self._extract_content(response)

        def text_generator() -> Generator[str, None, None]:
            response_stream = self.chat_completion_sync(
                messages, temperature=temperature, max_tokens=max_tokens, stream=True, **kwargs
            )
            for chunk in response_stream:
                content = self._extract_delta(chunk)
                if content:
                    yield content

        return text_generator()

    # ========== chat ==========

    async def chat(self,
                   conversation: Conversation,
                   user_message: str,
                   temperature: float = DEFAULT_TEMPERATURE,
                   max_tokens: int = DEFAULT_MAX_TOKENS,
                   stream: bool = False,
                   **kwargs) -> Union[str, AsyncGenerator[str, None]]:
        """多轮对话（异步）"""
        conversation.add_user_message(user_message)
        messages = conversation.get_messages()

        if not stream:
            response = await self.chat_completion(
                messages, temperature=temperature, max_tokens=max_tokens, stream=False, **kwargs
            )
            # 空回复会抛异常，由上层重试
            assistant_message = self._extract_content(response)
            conversation.add_assistant_message(assistant_message)
            return assistant_message

        async def chat_generator() -> AsyncGenerator[str, None]:
            full_response = ""
            response_stream = await self.chat_completion(
                messages, temperature=temperature, max_tokens=max_tokens, stream=True, **kwargs
            )
            async for chunk in response_stream:
                content = self._extract_delta(chunk)
                if content:
                    full_response += content
                    yield content
            conversation.add_assistant_message(full_response)

        return chat_generator()

    def chat_sync(self,
                  conversation: Conversation,
                  user_message: str,
                  temperature: float = DEFAULT_TEMPERATURE,
                  max_tokens: int = DEFAULT_MAX_TOKENS,
                  stream: bool = False,
                  **kwargs) -> Union[str, Generator[str, None, None]]:
        """多轮对话（同步）——业务主路径走这里"""
        conversation.add_user_message(user_message)
        messages = conversation.get_messages()

        if not stream:
            response = self.chat_completion_sync(
                messages, temperature=temperature, max_tokens=max_tokens, stream=False, **kwargs
            )
            # 空回复会抛异常，由上层重试
            assistant_message = self._extract_content(response)
            conversation.add_assistant_message(assistant_message)
            return assistant_message

        def chat_generator() -> Generator[str, None, None]:
            full_response = ""
            response_stream = self.chat_completion_sync(
                messages, temperature=temperature, max_tokens=max_tokens, stream=True, **kwargs
            )
            for chunk in response_stream:
                content = self._extract_delta(chunk)
                if content:
                    full_response += content
                    yield content
            conversation.add_assistant_message(full_response)

        return chat_generator()
