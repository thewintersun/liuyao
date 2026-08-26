from typing import Dict, Any, Optional, Type
import importlib
import logging

from .base import BaseLLM

# 配置日志
logger = logging.getLogger(__name__)


class LLMFactory:
    """LLM工厂类，用于创建不同的LLM客户端"""

    # 注册的LLM类型
    _registered_llms: Dict[str, Type[BaseLLM]] = {}

    @classmethod
    def register(cls, name: str, llm_class: Type[BaseLLM]) -> None:
        """
        注册LLM类型

        Args:
            name: LLM名称
            llm_class: LLM类
        """
        cls._registered_llms[name] = llm_class
        logger.info(f"已注册LLM类型: {name}")

    @classmethod
    def create(cls, llm_type: str, **kwargs) -> BaseLLM:
        """
        创建LLM实例

        Args:
            llm_type: LLM类型名称
            **kwargs: 传递给LLM构造函数的参数

        Returns:
            LLM实例

        Raises:
            ValueError: 如果LLM类型未注册
        """
        # 如果LLM类型未注册，尝试动态导入
        if llm_type not in cls._registered_llms:
            cls._try_import_llm(llm_type)

        # 检查LLM类型是否已注册
        if llm_type not in cls._registered_llms:
            raise ValueError(f"未知的LLM类型: {llm_type}，已注册的类型: {list(cls._registered_llms.keys())}")

        # 创建LLM实例
        llm_class = cls._registered_llms[llm_type]
        return llm_class(**kwargs)

    @classmethod
    def _try_import_llm(cls, llm_type: str) -> None:
        """
        尝试动态导入LLM模块

        Args:
            llm_type: LLM类型名称
        """
        try:
            # 尝试导入对应的模块
            module_path = f"llm.{llm_type}.client"
            module = importlib.import_module(module_path)

            # 查找模块中的LLM类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, BaseLLM) and
                    attr is not BaseLLM):
                    # 注册找到的LLM类
                    cls.register(llm_type, attr)
                    logger.info(f"已动态导入LLM类型: {llm_type}")
                    return

            logger.warning(f"在模块 {module_path} 中未找到LLM类")
        except (ImportError, AttributeError) as e:
            logger.warning(f"无法导入LLM类型 {llm_type}: {str(e)}")


# 导入并注册内置的LLM客户端
try:
    from ..deepseek.client import DeepseekClient
    LLMFactory.register("deepseek", DeepseekClient)
except ImportError:
    logger.warning("无法导入 DeepseekClient")

try:
    from ..glm.client import GLMClient
    LLMFactory.register("glm", GLMClient)
except ImportError:
    logger.warning("无法导入 GLMClient")

