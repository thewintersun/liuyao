import logging
from typing import Dict, List, Any, Optional, Union, AsyncGenerator, AsyncIterable, Generator, Iterable
import openai


from ..common.base import BaseLLM, Conversation
from ..common.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_API_BASE,
    DEEPSEEK_DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
)

# 配置日志
logger = logging.getLogger(__name__)


class DeepseekClient(BaseLLM):
    """DeepSeek API客户端实现，使用OpenAI兼容的API格式"""

    def __init__(self,
                api_key: Optional[str] = None,
                api_base: Optional[str] = None,
                model: str = DEEPSEEK_DEFAULT_MODEL):
        """
        初始化DeepSeek客户端

        Args:
            api_key: API密钥，默认从环境变量获取
            api_base: API基础URL，默认从环境变量获取
            model: 模型名称，默认为deepseek-chat
        """
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.api_base = api_base or DEEPSEEK_API_BASE
        self.model = model

        if not self.api_key:
            raise ValueError("DeepSeek API密钥未设置，请在.env文件中设置DEEPSEEK_API_KEY")

        # 配置OpenAI客户端
        openai.api_key = self.api_key
        openai.api_base = self.api_base


    @staticmethod
    def _extract_content(response) -> str:
        """从非流式响应中提取正文，空回复视为失败抛出

        deepseek-v4-flash 是推理模型，reasoning_tokens 计入 max_tokens 预算，
        推理过长时会耗尽预算，此时接口返回 200 但 content 为空
        （finish_reason='length'），必须当作失败，否则用户拿到空白结果。
        """
        try:
            choice = response["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"解析DeepSeek响应失败: {str(e)}")
            raise ValueError(f"无法从DeepSeek响应中提取助手回复: {str(e)}")

        finish_reason = choice.get("finish_reason")
        if not (content or "").strip():
            usage = response.get("usage") if hasattr(response, "get") else None
            logger.error(f"DeepSeek 返回空回复: finish_reason={finish_reason}, usage={usage}")
            raise ValueError(f"DeepSeek 返回空回复 (finish_reason={finish_reason})")
        if finish_reason == "length":
            logger.warning(f"DeepSeek 回复被截断: 长度={len(content)}，建议调高 max_tokens")

        return content


    async def chat_completion(self,
                       messages: List[Dict[str, str]],
                       temperature: float = DEFAULT_TEMPERATURE,
                       max_tokens: int = DEFAULT_MAX_TOKENS,
                       stream: bool = False,
                       **kwargs) -> Union[Dict[str, Any], AsyncIterable[Dict[str, Any]]]:
        """
        调用DeepSeek聊天完成API

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否使用流式模式
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回完整的API响应结果
            如果stream=True，返回一个异步迭代器，可以逐步获取生成的内容
        """
        try:
            # 使用OpenAI客户端调用API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )

            if not stream:
                # 非流式模式，返回完整响应
                return dict(response)
            else:
                # 流式模式，返回异步迭代器
                return response
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            raise

    def chat_completion_sync(self,
                      messages: List[Dict[str, str]],
                      temperature: float = DEFAULT_TEMPERATURE,
                      max_tokens: int = DEFAULT_MAX_TOKENS,
                      stream: bool = False,
                      **kwargs) -> Union[Dict[str, Any], Iterable[Dict[str, Any]]]:
        """
        同步调用DeepSeek聊天完成API

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否使用流式模式
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回完整的API响应结果
            如果stream=True，返回一个迭代器，可以逐步获取生成的内容
        """
        try:
            # 使用OpenAI客户端同步调用API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )

            if not stream:
                # 非流式模式，返回完整响应
                return dict(response)
            else:
                # 流式模式，返回迭代器
                return response
        except Exception as e:
            logger.error(f"DeepSeek API同步调用失败: {str(e)}")
            raise

    async def generate_text(self,
                     prompt: str,
                     temperature: float = DEFAULT_TEMPERATURE,
                     max_tokens: int = DEFAULT_MAX_TOKENS,
                     stream: bool = False,
                     **kwargs) -> Union[str, AsyncGenerator[str, None]]:
        """
        生成文本

        Args:
            prompt: 提示文本
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否使用流式模式
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回生成的完整文本
            如果stream=True，返回一个异步生成器，可以逐步获取生成的文本片段
        """
        # 将提示转换为消息格式
        messages = [{"role": "user", "content": prompt}]

        if not stream:
            # 非流式模式
            # 调用聊天完成API
            response = await self.chat_completion(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )

            # 提取生成的文本
            try:
                return response["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as e:
                logger.error(f"解析DeepSeek响应失败: {str(e)}")
                raise ValueError(f"无法从DeepSeek响应中提取文本: {str(e)}")
        else:
            # 流式模式
            async def text_generator() -> AsyncGenerator[str, None]:
                response_stream = await self.chat_completion(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs
                )

                async for chunk in response_stream:
                    try:
                        # 提取每个块中的文本片段
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                yield delta["content"]
                    except Exception as e:
                        logger.error(f"处理流式响应块失败: {str(e)}")

            return text_generator()

    def generate_text_sync(self,
                    prompt: str,
                    temperature: float = DEFAULT_TEMPERATURE,
                    max_tokens: int = DEFAULT_MAX_TOKENS,
                    stream: bool = False,
                    **kwargs) -> Union[str, Generator[str, None, None]]:
        """
        同步生成文本

        Args:
            prompt: 提示文本
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否使用流式模式
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回生成的完整文本
            如果stream=True，返回一个生成器，可以逐步获取生成的文本片段
        """
        # 将提示转换为消息格式
        messages = [{"role": "user", "content": prompt}]

        if not stream:
            # 非流式模式
            # 调用同步聊天完成API
            response = self.chat_completion_sync(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )

            # 提取生成的文本
            try:
                return response["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as e:
                logger.error(f"解析DeepSeek响应失败: {str(e)}")
                raise ValueError(f"无法从DeepSeek响应中提取文本: {str(e)}")
        else:
            # 流式模式
            def text_generator() -> Generator[str, None, None]:
                response_stream = self.chat_completion_sync(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs
                )

                for chunk in response_stream:
                    try:
                        # 提取每个块中的文本片段
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                yield delta["content"]
                    except Exception as e:
                        logger.error(f"处理流式响应块失败: {str(e)}")

            return text_generator()

    async def chat(self,
            conversation: Conversation,
            user_message: str,
            temperature: float = DEFAULT_TEMPERATURE,
            max_tokens: int = DEFAULT_MAX_TOKENS,
            stream: bool = False,
            **kwargs) -> Union[str, AsyncGenerator[str, None]]:
        """
        进行对话

        Args:
            conversation: 对话对象
            user_message: 用户消息
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否使用流式模式
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回助手的完整回复
            如果stream=True，返回一个异步生成器，可以逐步获取助手的回复片段
        """
        # 添加用户消息到对话历史
        conversation.add_user_message(user_message)

        # 获取所有消息
        messages = conversation.get_messages()

        if not stream:
            # 非流式模式
            # 调用聊天完成API
            response = await self.chat_completion(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )

            # 提取助手回复（空回复会抛异常，由上层重试）
            assistant_message = self._extract_content(response)

            # 将助手回复添加到对话历史
            conversation.add_assistant_message(assistant_message)

            return assistant_message
        else:
            # 流式模式
            async def chat_generator() -> AsyncGenerator[str, None]:
                full_response = ""

                response_stream = await self.chat_completion(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs
                )

                async for chunk in response_stream:
                    try:
                        # 提取每个块中的文本片段
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                content = delta["content"]
                                full_response += content
                                yield content
                    except Exception as e:
                        logger.error(f"处理流式响应块失败: {str(e)}")

                # 流式生成完成后，将完整回复添加到对话历史
                conversation.add_assistant_message(full_response)

            return chat_generator()

    def chat_sync(self,
           conversation: Conversation,
           user_message: str,
           temperature: float = DEFAULT_TEMPERATURE,
           max_tokens: int = DEFAULT_MAX_TOKENS,
           stream: bool = False,
           **kwargs) -> Union[str, Generator[str, None, None]]:
        """
        同步进行对话

        Args:
            conversation: 对话对象
            user_message: 用户消息
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否使用流式模式
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回助手的完整回复
            如果stream=True，返回一个生成器，可以逐步获取助手的回复片段
        """
        # 添加用户消息到对话历史
        conversation.add_user_message(user_message)

        # 获取所有消息
        messages = conversation.get_messages()

        if not stream:
            # 非流式模式
            # 调用同步聊天完成API
            response = self.chat_completion_sync(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                **kwargs
            )

            # 提取助手回复（空回复会抛异常，由上层重试）
            assistant_message = self._extract_content(response)

            # 将助手回复添加到对话历史
            conversation.add_assistant_message(assistant_message)

            return assistant_message
        else:
            # 流式模式
            def chat_generator() -> Generator[str, None, None]:
                full_response = ""

                response_stream = self.chat_completion_sync(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs
                )

                for chunk in response_stream:
                    try:
                        # 提取每个块中的文本片段
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                content = delta["content"]
                                full_response += content
                                yield content
                    except Exception as e:
                        logger.error(f"处理流式响应块失败: {str(e)}")

                # 流式生成完成后，将完整回复添加到对话历史
                conversation.add_assistant_message(full_response)

            return chat_generator()
