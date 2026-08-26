import os

# ========== JWT ==========
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError('环境变量 JWT_SECRET 未设置，请在 .env 中配置')
JWT_EXPIRY = 30 * 24 * 3600  # 30 天

# ========== 站点 ==========
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:9001')

# ========== 额度 ==========
GUEST_FREE_USES = 1       # 未登录用户免费解卦次数
REGISTERED_FREE_USES = 50  # 注册用户赠送解卦次数

# ========== 用户名/密码规则 ==========
USERNAME_MIN_LENGTH = 2
USERNAME_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 6

# ========== 密码重置 ==========
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 30  # token 有效期
PASSWORD_RESET_TOKEN_CLEANUP_HOURS = 1    # 过期 token 清理阈值

# ========== 邀请奖励 ==========
INVITE_VISIT_REWARD = 5        # 游客点开邀请链接，邀请人获得额度
INVITE_REGISTER_REWARD = 20    # 被邀请人注册成功，邀请人获得额度
INVITE_REGISTER_BONUS = 20     # 被邀请人注册成功，被邀请人获得额度
INVITE_MONTHLY_LIMIT = 20      # 每用户每月邀请上限（游客+注册合计）
INVITE_IP_DAILY_LIMIT = 3      # 同一 IP 24h 内最多触发访问奖励次数
INVITE_RECORDS_QUERY_LIMIT = 50  # 邀请记录查询上限

# ========== 验证码 ==========
CAPTCHA_LENGTH = 4
CAPTCHA_EXPIRY_SECONDS = 300   # 5 分钟
CAPTCHA_IMAGE_WIDTH = 160
CAPTCHA_IMAGE_HEIGHT = 60

# ========== 速率限制 ==========
RATE_LIMIT_CAPTCHA = (30, 600)         # (次数, 窗口秒数) 验证码
RATE_LIMIT_LOGIN = (10, 600)           # 登录
RATE_LIMIT_REGISTER = (5, 3600)        # 注册（同一IP每小时最多5次）
RATE_LIMIT_GUEST_RECEIVE = (5, 3600)   # 游客排盘
RATE_LIMIT_GUEST_CHAT = (10, 3600)     # 游客聊天
RATE_LIMIT_CHAT_RESTORE = (20, 3600)   # 对话恢复
RATE_LIMIT_FEEDBACK = (5, 3600)        # 反馈
RATE_LIMIT_INVITE_VISIT = (10, 3600)   # 邀请访问
RATE_LIMIT_FORGOT_PASSWORD = (3, 3600) # 忘记密码
RATE_LIMITER_CLEANUP_INTERVAL = 300    # 限流器清理间隔（5 分钟）
RATE_LIMITER_RETENTION_WINDOW = 3600   # 限流器保留窗口（1 小时）

# ========== 对话管理 ==========
CONVERSATION_TOKEN_LIMIT = 50000         # token 上限
MAX_CONCURRENT_CONVERSATIONS = 100       # 最大并发对话数
CONVERSATION_TIMEOUT_SECONDS = 86400     # 对话超时（24 小时）
ACTIVE_USER_WINDOW_SECONDS = 600         # 活跃用户判断窗口（10 分钟）
MAX_RECENT_ROUNDS = 9                    # 首轮之外最多保留轮数
LLM_TEMPERATURE = 0.7
# deepseek-v4-flash 是推理模型，reasoning_tokens 计入本预算。
# 4096 时复杂卦例的推理会耗尽预算导致正文为空，故放宽（模型上限 65536）。
LLM_MAX_TOKENS = 16384
LLM_RETRY_ON_FAILURE = True              # LLM 调用失败（含空回复）时自动重试一次
CHAT_RESTORE_MAX_MESSAGES = 100          # 恢复对话最大消息数

# ========== 异步任务 ==========
ASYNC_TASK_TIMEOUT_SECONDS = 600  # 10 分钟

# ========== 管理后台分页 ==========
ADMIN_DEFAULT_PER_PAGE = 20
ADMIN_MAX_PER_PAGE = 100

# ========== IP 地理位置 ==========
IP_LOCATION_CACHE_TTL = 86400     # 缓存 24 小时
IP_LOCATION_QUERY_TIMEOUT = 3     # 查询超时（秒）

# ========== 邮件 ==========
EMAIL_SMTP_SERVER = os.environ.get('EMAIL_SMTP_SERVER', 'smtp.163.com')
EMAIL_SMTP_PORT = int(os.environ.get('EMAIL_SMTP_PORT', '465'))

# ========== LLM 日志 ==========
LLM_LOG_MAX_SIZE = 10 * 1024 * 1024   # 单文件最大 10MB，超过后轮转
LLM_LOG_RETENTION_DAYS = 30           # 保留最近 30 天的日志

# ========== 数据库备份 ==========
BACKUP_KEEP = 7          # 保留最近 7 份
BACKUP_INTERVAL = 86400  # 每 24 小时备份一次
