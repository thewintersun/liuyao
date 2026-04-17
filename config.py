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
