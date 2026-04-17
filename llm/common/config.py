import os
from dotenv import load_dotenv
from pathlib import Path
import sys

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent
# 添加项目根目录到Python路径，确保能够导入config
sys.path.insert(0, str(ROOT_DIR))

# 加载.env文件中的环境变量
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
DEEPSEEK_DEFAULT_MODEL = "deepseek-chat"

SYSTEM_PROMPT = """
【角色】你是一位精通六爻的专业占卜师，同时也是一位善于深入浅出的解说者。你的受众是对六爻不太了解的普通人。
"""

# 六爻预测提示词
LIUYAO_PROMPT = """
【六爻信息】
{liuyao_data}
【解析步骤】
按以下步骤分析，每步都包含"专业分析"和"解读"两个部分：
- 卦象基本情况
- 用神状态分析（含日月生克，以及动爻生克的影响）
- 世爻与应爻关系以及影响
- 动爻分析
- 空亡分析
- 六神分析
- 合、冲、刑关系检查
- 十二长生分析，重点关注帝旺，墓，绝，长生等状态的关系；
- 综合分析（结合卦中用神，世爻，应爻，日月和动爻的生克合冲，空亡，十二长生，六神等信息，给出对问题的具体预测和建议）：
   - 一句话结论
   - 详细分析
   - 具体建议
   - 注意事项

【输出要求】
- 解读部分：零术语，直接说白话、内容要详细；
- 专业分析部分：保留完整术语和逻辑链
- 结尾给出引导用户继续提问的3个提示；
"""

# 默认模型配置
DEFAULT_TEMPERATURE = 0
DEFAULT_MAX_TOKENS = 8192
