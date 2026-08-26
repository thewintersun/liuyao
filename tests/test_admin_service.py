import pytest
import auth
import admin_service
from config import GUEST_FREE_USES


class TestEscapeLike:
    def test_percent(self):
        assert admin_service._escape_like('100%') == '100\\%'

    def test_underscore(self):
        assert admin_service._escape_like('a_b') == 'a\\_b'

    def test_backslash(self):
        assert admin_service._escape_like('a\\b') == 'a\\\\b'

    def test_no_special(self):
        assert admin_service._escape_like('hello') == 'hello'


class TestDashboardStats:
    def test_structure(self, test_db):
        stats = admin_service.get_dashboard_stats()
        assert 'total_users' in stats
        assert 'today_users' in stats
        assert 'total_divinations' in stats
        assert 'active_sessions' in stats

    def test_counts_users(self, registered_user):
        stats = admin_service.get_dashboard_stats()
        assert stats['total_users'] >= 1


class TestUserManagement:
    def test_get_all_users(self, registered_user):
        result = admin_service.get_all_users(page=1, per_page=10)
        assert 'users' in result
        assert result['total'] >= 1

    def test_search_users(self, registered_user):
        result = admin_service.get_all_users(search='testuser')
        assert result['total'] >= 1

    def test_search_no_match(self, registered_user):
        result = admin_service.get_all_users(search='nonexistent_xyz')
        assert result['total'] == 0

    def test_get_user_detail(self, registered_user):
        user_id = registered_user['user']['id']
        detail = admin_service.get_user_detail(user_id)
        assert detail is not None
        assert detail['username'] == 'testuser'

    def test_nonexistent_user(self, test_db):
        assert admin_service.get_user_detail(99999) is None


class TestBanUnban:
    def test_ban_user(self, registered_user):
        user_id = registered_user['user']['id']
        success, _ = admin_service.ban_user(user_id)
        assert success is True
        detail = admin_service.get_user_detail(user_id)
        assert detail['role'] == 'banned'

    def test_cannot_ban_admin(self, registered_user):
        user_id = registered_user['user']['id']
        db = auth.get_db()
        db.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user_id,))
        db.commit()
        auth.release_db(db)
        success, _ = admin_service.ban_user(user_id)
        assert success is False

    def test_unban_user(self, registered_user):
        user_id = registered_user['user']['id']
        admin_service.ban_user(user_id)
        admin_service.unban_user(user_id)
        detail = admin_service.get_user_detail(user_id)
        assert detail['role'] == 'user'


class TestSystemConfig:
    def test_update_and_get(self, test_db):
        admin_service.update_system_config('TEST_KEY', '42')
        assert admin_service.get_system_config('TEST_KEY') == '42'

    def test_fallback_defaults(self, test_db):
        val = admin_service.get_system_config('GUEST_FREE_USES')
        assert val == str(GUEST_FREE_USES)

    def test_get_all_configs(self, test_db):
        configs = admin_service.get_all_configs()
        assert 'GUEST_FREE_USES' in configs
        assert 'INVITE_MONTHLY_LIMIT' in configs


class TestLLMProviderConfig:
    """LLM_PROVIDER 填错会导致解卦全挂，必须在写库前拦住"""

    def test_default_is_deepseek(self, test_db):
        assert admin_service.get_system_config('LLM_PROVIDER') == 'deepseek'

    def test_switch_to_glm(self, test_db):
        admin_service.update_system_config('LLM_PROVIDER', 'glm')
        assert admin_service.get_system_config('LLM_PROVIDER') == 'glm'

    def test_invalid_provider_rejected(self, test_db):
        with pytest.raises(ValueError):
            admin_service.update_system_config('LLM_PROVIDER', 'openai')
        # 拒绝后不应落库，仍是默认值
        assert admin_service.get_system_config('LLM_PROVIDER') == 'deepseek'

    def test_all_configs_exposes_provider_options(self, test_db):
        configs = admin_service.get_all_configs()
        assert configs['LLM_PROVIDER'] == 'deepseek'
        assert 'glm' in configs['LLM_PROVIDERS']
        assert 'deepseek' in configs['LLM_PROVIDERS']
