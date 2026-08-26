"""智谱 GLM 客户端

走 OpenAI 兼容接口。注意两个端点不可互换：
- Coding Plan 端点：/api/coding/paas/v4，用包月额度，智谱声明仅限编码场景
- 通用端点：      /api/paas/v4，按 token 计费

thinking 模式开启时模型会先输出 reasoning_content，这部分 token 同样计入
max_tokens 预算，预算不足会导致 content 为空，由基类判为失败并重试。
"""

import logging
from typing import Optional

from ..common.openai_compat import OpenAICompatibleClient
from ..common.config import (
    GLM_API_KEY,
    GLM_API_BASE,
    GLM_DEFAULT_MODEL,
    GLM_THINKING_ENABLED,
)

logger = logging.getLogger(__name__)


class GLMClient(OpenAICompatibleClient):
    """智谱 GLM API客户端实现，使用OpenAI兼容的API格式"""

    def __init__(self,
                 api_key: Optional[str] = None,
                 api_base: Optional[str] = None,
                 model: Optional[str] = None,
                 thinking: Optional[bool] = None):
        """
        初始化 GLM 客户端

        Args:
            api_key: API密钥，默认从环境变量 GLM_API_KEY 获取
            api_base: API基础URL，默认从环境变量 GLM_API_BASE 获取
            model: 模型名称，默认为 GLM_DEFAULT_MODEL
            thinking: 是否开启推理模式，默认取 GLM_THINKING_ENABLED
        """
        thinking_on = GLM_THINKING_ENABLED if thinking is None else thinking
        super().__init__(
            api_key=api_key or GLM_API_KEY,
            api_base=api_base or GLM_API_BASE,
            model=model or GLM_DEFAULT_MODEL,
            provider_name='GLM',
            extra_params={'thinking': {'type': 'enabled' if thinking_on else 'disabled'}},
        )
        self.thinking = thinking_on
