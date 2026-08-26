"""DeepSeek 客户端

deepseek-v4-flash 是推理模型，reasoning_tokens 计入 max_tokens 预算，
预算不足时会返回空 content，基类的 _extract_content 会将其判为失败。
"""

import logging
from typing import Optional

from ..common.openai_compat import OpenAICompatibleClient
from ..common.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_API_BASE,
    DEEPSEEK_DEFAULT_MODEL,
)

logger = logging.getLogger(__name__)


class DeepseekClient(OpenAICompatibleClient):
    """DeepSeek API客户端实现，使用OpenAI兼容的API格式"""

    def __init__(self,
                 api_key: Optional[str] = None,
                 api_base: Optional[str] = None,
                 model: Optional[str] = None):
        """
        初始化DeepSeek客户端

        Args:
            api_key: API密钥，默认从环境变量获取
            api_base: API基础URL，默认从环境变量获取
            model: 模型名称，默认为 DEEPSEEK_DEFAULT_MODEL
        """
        super().__init__(
            api_key=api_key or DEEPSEEK_API_KEY,
            api_base=api_base or DEEPSEEK_API_BASE,
            model=model or DEEPSEEK_DEFAULT_MODEL,
            provider_name='DeepSeek',
        )


# 兼容早期拼写
DeepSeekClient = DeepseekClient
