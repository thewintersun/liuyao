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
【角色】
你是一位经验丰富的六爻解卦师，擅长用普通人能听懂的白话解答卦象。
"""

# 六爻预测提示词
LIUYAO_PROMPT = """
【六爻信息】
{liuyao_data}
【输出要求】
请按以下顺序和格式输出，不要使用专业术语，结论不要含糊：

1. 总体结论

2. 详细解读
   - 根据需要分几段解读，每段只说一个核心意思
   - 用比喻、日常语言，不用“用神、世应、六神、长生、空亡”等术语
   - 解释事情当前状态、发展趋势、主要阻碍或助力

3. 具体建议
   - 可操作的动作：做什么、不做什么、何时做、注意什么

4. 注意事项（最多3条）
   - 最重要的风险或前提条件
   
【专业分析】
这部分主要给专业人士参考，依次分析以下要素，给出卦象中的信息：
用神旺衰（日月生克、动爻影响）、世应关系、动爻变化、空亡、六神、合冲刑、十二长生。

---
💡 **想继续了解？你可以问我：**
（给出3个与用户问题相关的、引导深入的提问示例）
"""

# 默认模型配置
DEFAULT_TEMPERATURE = 0
DEFAULT_MAX_TOKENS = 8192
