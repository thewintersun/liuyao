import pytest
from rate_limiter import RateLimiter, get_client_ip


class MockRequest:
    def __init__(self, remote_addr='127.0.0.1', headers=None):
        self.remote_addr = remote_addr
        self.headers = headers or {}


class TestIsAllowed:
    def test_first_request(self):
        rl = RateLimiter()
        assert rl.is_allowed('k1', 3, 60) is True

    def test_under_limit(self):
        rl = RateLimiter()
        for _ in range(3):
            assert rl.is_allowed('k2', 3, 60) is True

    def test_over_limit(self):
        rl = RateLimiter()
        for _ in range(3):
            rl.is_allowed('k3', 3, 60)
        assert rl.is_allowed('k3', 3, 60) is False

    def test_different_keys_independent(self):
        rl = RateLimiter()
        for _ in range(3):
            rl.is_allowed('kA', 3, 60)
        assert rl.is_allowed('kA', 3, 60) is False
        assert rl.is_allowed('kB', 3, 60) is True

    def test_window_expiry(self):
        rl = RateLimiter()
        # 手动注入过期记录
        rl._records['kE'] = [0.0, 0.0, 0.0]  # 很久以前的时间戳
        assert rl.is_allowed('kE', 3, 60) is True


class TestGetClientIp:
    def test_direct_connection(self, monkeypatch):
        monkeypatch.setenv('BEHIND_PROXY', 'false')
        req = MockRequest(remote_addr='192.168.1.1')
        assert get_client_ip(req) == '192.168.1.1'

    def test_behind_proxy_xff(self, monkeypatch):
        monkeypatch.setenv('BEHIND_PROXY', 'true')
        req = MockRequest(
            remote_addr='127.0.0.1',
            headers={'X-Forwarded-For': '8.8.8.8, 10.0.0.1'}
        )
        assert get_client_ip(req) == '8.8.8.8'

    def test_behind_proxy_real_ip(self, monkeypatch):
        monkeypatch.setenv('BEHIND_PROXY', 'true')
        req = MockRequest(
            remote_addr='127.0.0.1',
            headers={'X-Real-IP': '1.2.3.4'}
        )
        assert get_client_ip(req) == '1.2.3.4'

    def test_no_proxy_ignores_headers(self, monkeypatch):
        monkeypatch.setenv('BEHIND_PROXY', 'false')
        req = MockRequest(
            remote_addr='192.168.1.1',
            headers={'X-Forwarded-For': '8.8.8.8'}
        )
        assert get_client_ip(req) == '192.168.1.1'

    def test_no_remote_addr(self, monkeypatch):
        monkeypatch.setenv('BEHIND_PROXY', 'false')
        req = MockRequest(remote_addr=None)
        assert get_client_ip(req) == '0.0.0.0'
