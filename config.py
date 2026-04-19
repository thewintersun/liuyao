# 未登录用户免费解卦次数
GUEST_FREE_USES = 1

# 注册用户赠送解卦次数
REGISTERED_FREE_USES = 50

import os

# JWT 密钥（必须通过环境变量 .env 设置）
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError('环境变量 JWT_SECRET 未设置，请在 .env 中配置')

# JWT 过期时间（秒），30天
JWT_EXPIRY = 30 * 24 * 3600

# 邀请奖励配置
INVITE_VISIT_REWARD = 5        # 游客点开邀请链接，邀请人获得额度
INVITE_REGISTER_REWARD = 20    # 被邀请人注册成功，邀请人获得额度
INVITE_REGISTER_BONUS = 20     # 被邀请人注册成功，被邀请人获得额度
INVITE_MONTHLY_LIMIT = 20      # 每用户每月邀请上限（游客+注册合计）
INVITE_IP_DAILY_LIMIT = 3      # 同一 IP 24h 内最多触发访问奖励次数
