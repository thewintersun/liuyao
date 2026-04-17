from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, AsyncGenerator, AsyncIterable


class Message:
    """聊天消息类"""

    def __init__(self, role: str, content: str):
        """
        初始化聊天消息

        Args:
            role: 消息角色，如'user', 'assistant', 'system'
            content: 消息内容
        """
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式"""
        return {
            "role": self.role,
            "content": self.content
        }


class Conversation:
    """对话管理类，用于管理多轮对话的历史记录"""

    def __init__(self, system_message: Optional[str] = None):
        """
        初始化对话

        Args:
            system_message: 系统消息，用于设置对话的上下文或指导模型行为
        """
        self.messages: List[Message] = []
        if system_message:
            self.add_system_message(system_message)

    def add_system_message(self, content: str) -> None:
        """添加系统消息"""
        self.messages.append(Message("system", content))

    def add_user_message(self, content: str) -> None:
        """添加用户消息"""
        self.messages.append(Message("user", content))

    def add_assistant_message(self, content: str) -> None:
        """添加助手消息"""
        self.messages.append(Message("assistant", content))

    def get_messages(self) -> List[Dict[str, str]]:
        """获取所有消息的字典列表"""
        return [message.to_dict() for message in self.messages]

    def clear(self) -> None:
        """清空对话历史"""
        self.messages = []


class BaseLLM(ABC):
    """LLM基础接口类"""

    @abstractmethod
    async def chat_completion(self,
                       messages: List[Dict[str, str]],
                       temperature: float = 0.7,
                       max_tokens: int = 4096,
                       stream: bool = False,
                       **kwargs) -> Union[Dict[str, Any], AsyncIterable[Dict[str, Any]]]:
        """
        聊天完成接口

        Args:
            messages: 消息列表，每个消息包含role和content
            temperature: 温度参数，控制输出的随机性
            max_tokens: 生成的最大token数
            stream: 是否使用流式模式
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回完整的API响应结果
            如果stream=True，返回一个异步迭代器，可以逐步获取生成的内容
        """
        pass

    @abstractmethod
    async def generate_text(self,
                     prompt: str,
                     temperature: float = 0.7,
                     max_tokens: int = 4096,
                     stream: bool = False,
                     **kwargs) -> Union[str, AsyncGenerator[str, None]]:
        """
        生成文本接口

        Args:
            prompt: 提示文本
            temperature: 温度参数，控制输出的随机性
            max_tokens: 生成的最大token数
            stream: 是否使用流式模式
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回生成的完整文本
            如果stream=True，返回一个异步生成器，可以逐步获取生成的文本片段
        """
        pass

    @abstractmethod
    async def chat(self,
            conversation: Conversation,
            user_message: str,
            temperature: float = 0.7,
            max_tokens: int = 4096,
            stream: bool = False,
            **kwargs) -> Union[str, AsyncGenerator[str, None]]:
        """
        进行对话接口

        Args:
            conversation: 对话对象，包含历史消息
            user_message: 用户消息
            temperature: 温度参数，控制输出的随机性
            max_tokens: 生成的最大token数
            stream: 是否使用流式模式
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回助手的完整回复
            如果stream=True，返回一个异步生成器，可以逐步获取助手的回复片段
        """
        pass


class UserSession:
    """用户会话类，用于管理不同用户的对话"""

    def __init__(self, user_id: str, llm: BaseLLM):
        """
        初始化用户会话

        Args:
            user_id: 用户ID
            llm: LLM实例
        """
        self.user_id = user_id
        self.llm = llm
        self.conversation = Conversation()

    async def send_message(self,
                    message: str,
                    temperature: float = 0.7,
                    max_tokens: int = 4096,
                    stream: bool = False,
                    **kwargs) -> Union[str, AsyncGenerator[str, None]]:
        """
        发送消息并获取回复

        Args:
            message: 用户消息
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否使用流式模式
            **kwargs: 其他参数

        Returns:
            如果stream=False，返回助手的完整回复
            如果stream=True，返回一个异步生成器，可以逐步获取助手的回复片段
        """
        return await self.llm.chat(
            self.conversation,
            message,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        )

    def reset_conversation(self, system_message: Optional[str] = None) -> None:
        """
        重置对话

        Args:
            system_message: 新的系统消息
        """
        self.conversation = Conversation(system_message)
