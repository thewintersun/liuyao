"""Gunicorn 配置 — 六爻AI排盘"""
import os

# 监听地址
bind = "0.0.0.0:9001"

# 使用 1 个 worker + 4 线程（gthread 模式）
# 为什么不用多 worker：
#   - _async_tasks 异步任务字典存在内存中，多 worker 会导致提交和轮询落到不同进程
#   - dialog_manager 会话缓存也在内存中，多 worker 会导致会话丢失
#   - 4 线程足以处理并发请求
workers = 1
threads = 4
worker_class = "gthread"

# 超时设置
# graceful_timeout: 平滑重启时，等待旧 worker 处理完当前请求的最大时间（秒）
#   设为 300 秒，确保正在进行的 LLM 请求能处理完毕
graceful_timeout = 300

# timeout: worker 响应超时（秒），超过此时间 master 会强制杀死 worker
#   设为 600 秒，防止极端情况下 LLM 无响应导致 worker 假死
timeout = 600

# 日志
accesslog = "-"   # 输出到 stdout（systemd 会捕获到 journal）
errorlog = "-"    # 输出到 stderr

# SSL 自动检测（与 gua_app.py 保持一致）
_root = os.path.dirname(os.path.abspath(__file__))
_cert = os.path.join(_root, "certs", "cert.pem")
_key = os.path.join(_root, "certs", "key.pem")
if os.path.isfile(_cert) and os.path.isfile(_key):
    certfile = _cert
    keyfile = _key
