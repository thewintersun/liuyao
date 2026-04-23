"""
IP 限流器 — 基于滑动时间窗口的内存限流，无需外部依赖。
"""
import os
import time
import threading
from config import RATE_LIMITER_CLEANUP_INTERVAL, RATE_LIMITER_RETENTION_WINDOW


class RateLimiter:
    def __init__(self):
        self._records = {}  # key -> [timestamp, ...]
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = RATE_LIMITER_CLEANUP_INTERVAL

    def is_allowed(self, key, max_requests, window_seconds):
        """检查 key 在 window_seconds 内是否还未超过 max_requests 次。
        如果允许，自动记录本次请求并返回 True；否则返回 False。
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            # 定期清理过期条目，防止内存泄漏
            if now - self._last_cleanup > self._cleanup_interval:
                self._cleanup(now)

            if key not in self._records:
                self._records[key] = [now]
                return True

            # 只保留窗口内的记录
            self._records[key] = [t for t in self._records[key] if t > cutoff]

            if len(self._records[key]) >= max_requests:
                return False

            self._records[key].append(now)
            return True

    def _cleanup(self, now):
        """清理所有过期条目，防止内存无限增长。"""
        expired_keys = []
        for key, timestamps in self._records.items():
            # 保留最近 1 小时内有记录的 key（覆盖最长窗口）
            fresh = [t for t in timestamps if t > now - RATE_LIMITER_RETENTION_WINDOW]
            if fresh:
                self._records[key] = fresh
            else:
                expired_keys.append(key)
        for key in expired_keys:
            del self._records[key]
        self._last_cleanup = now


# 全局限流器实例
limiter = RateLimiter()


def get_client_ip(req):
    """获取客户端真实 IP。
    仅在部署于可信反向代理后面时（设置环境变量 BEHIND_PROXY=true），
    才信任 X-Forwarded-For / X-Real-IP 头。否则直接使用 remote_addr，防止伪造绕过。
    """
    if os.environ.get('BEHIND_PROXY', 'false').lower() == 'true':
        forwarded = req.headers.get('X-Forwarded-For', '')
        if forwarded:
            return forwarded.split(',')[0].strip()
        real_ip = req.headers.get('X-Real-IP', '')
        if real_ip:
            return real_ip.strip()
    return req.remote_addr or '0.0.0.0'
