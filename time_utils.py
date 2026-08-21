"""统一时间处理

全站约定：所有时间一律使用**服务器本地时区**，不使用 UTC。

注意 SQLite 的 CURRENT_TIMESTAMP 返回的是 UTC 时间，因此本项目不再使用它，
所有写入统一由 Python 侧生成本地时间字符串（或用 datetime('now','localtime')）。
"""
from datetime import datetime

# 数据库时间列的统一存储格式
DB_TIME_FMT = '%Y-%m-%d %H:%M:%S'


def now_str():
    """当前服务器本地时间，数据库存储格式"""
    return datetime.now().strftime(DB_TIME_FMT)


def to_local_str(value):
    """把外部传入的时间字符串规范化为本地时区的数据库格式

    - 带时区标记（Z 或 ±HH:MM）的按该时区解析后转成本地时间
    - 不带时区标记的直接视为本地时间，仅规范化格式
    - 空值或无法解析时返回 None（调用方自行决定回退到 now_str()）
    """
    if not value or not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    # Python 3.10 的 fromisoformat 不认 'Z' 后缀
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt.strftime(DB_TIME_FMT)
