import pytest
import auth


class TestRegisterUser:
    def test_success(self, test_db):
        result, error = auth.register_user('newuser', 'pass123456')
        assert error is None
        assert 'token' in result
        assert result['user']['username'] == 'newuser'

    def test_duplicate_username(self, test_db):
        auth.register_user('dup', 'pass123456')
        result, error = auth.register_user('dup', 'pass123456')
        assert result is None
        assert error is not None

    def test_short_password(self, test_db):
        result, error = auth.register_user('u1', '123')
        assert result is None

    def test_valid_email(self, test_db):
        result, error = auth.register_user('u2', 'pass123456', email='a@b.com')
        assert error is None

    def test_invalid_email(self, test_db):
        result, error = auth.register_user('u3', 'pass123456', email='bad')
        assert result is None

    def test_invite_code_generated(self, test_db):
        result, _ = auth.register_user('u4', 'pass123456')
        db = auth.get_db()
        user = db.execute('SELECT invite_code FROM users WHERE id = ?', (result['user']['id'],)).fetchone()
        auth.release_db(db)
        assert user['invite_code'] is not None
        assert len(user['invite_code']) == 6


class TestLoginUser:
    def test_success(self, registered_user):
        result, error = auth.login_user('testuser', 'password123')
        assert error is None
        assert 'token' in result

    def test_wrong_password(self, registered_user):
        result, error = auth.login_user('testuser', 'wrong')
        assert result is None

    def test_nonexistent_user(self, test_db):
        result, error = auth.login_user('nobody', 'pass')
        assert result is None

    def test_banned_user(self, registered_user):
        db = auth.get_db()
        db.execute("UPDATE users SET role = 'banned' WHERE username = 'testuser'")
        db.commit()
        auth.release_db(db)
        result, error = auth.login_user('testuser', 'password123')
        assert result is None

    def test_login_records_ip(self, registered_user):
        auth.login_user('testuser', 'password123', ip='1.2.3.4')
        db = auth.get_db()
        user = db.execute("SELECT last_login_ip FROM users WHERE username = 'testuser'").fetchone()
        auth.release_db(db)
        assert user['last_login_ip'] == '1.2.3.4'


class TestCreditSystem:
    def test_check_credit(self, registered_user):
        user_id = registered_user['user']['id']
        assert auth.check_credit(user_id) is True

    def test_use_credit_decrements(self, registered_user):
        user_id = registered_user['user']['id']
        initial = registered_user['user']['free_uses']
        success, remaining = auth.use_credit(user_id, 'divination', 'sess1')
        assert success is True
        assert remaining == initial - 1

    def test_use_credit_at_zero(self, registered_user):
        user_id = registered_user['user']['id']
        db = auth.get_db()
        db.execute('UPDATE users SET free_uses = 0 WHERE id = ?', (user_id,))
        db.commit()
        auth.release_db(db)
        success, remaining = auth.use_credit(user_id, 'divination')
        assert success is False
        assert remaining == 0


class TestChangePassword:
    def test_success(self, registered_user):
        user_id = registered_user['user']['id']
        success, _ = auth.change_password(user_id, 'password123', 'newpass123')
        assert success is True
        # 旧密码失效
        result, _ = auth.login_user('testuser', 'password123')
        assert result is None
        # 新密码可用
        result, _ = auth.login_user('testuser', 'newpass123')
        assert result is not None

    def test_wrong_old_password(self, registered_user):
        user_id = registered_user['user']['id']
        success, _ = auth.change_password(user_id, 'wrongold', 'newpass123')
        assert success is False


class TestChangeEmail:
    def test_success(self, registered_user):
        user_id = registered_user['user']['id']
        success, _ = auth.change_email(user_id, 'new@example.com')
        assert success is True

    def test_invalid_email(self, registered_user):
        user_id = registered_user['user']['id']
        success, _ = auth.change_email(user_id, 'bad-email')
        assert success is False


class TestInviteSystem:
    def test_visit_reward(self, registered_user):
        user_id = registered_user['user']['id']
        db = auth.get_db()
        code = db.execute('SELECT invite_code FROM users WHERE id = ?', (user_id,)).fetchone()['invite_code']
        before = db.execute('SELECT free_uses FROM users WHERE id = ?', (user_id,)).fetchone()['free_uses']
        auth.release_db(db)
        result = auth.process_invite_visit(code, '8.8.8.8')
        assert result[0] is True
        db = auth.get_db()
        after = db.execute('SELECT free_uses FROM users WHERE id = ?', (user_id,)).fetchone()['free_uses']
        auth.release_db(db)
        assert after > before

    def test_invalid_code(self, test_db):
        result = auth.process_invite_visit('BADCODE', '1.1.1.1')
        assert result[0] is False

    def test_get_stats(self, registered_user):
        user_id = registered_user['user']['id']
        stats = auth.get_invite_stats(user_id)
        assert 'invite_code' in stats
        assert 'records' in stats


class TestSaveConversation:
    def test_save_and_retrieve(self, test_db):
        auth.save_conversation('sess_1', None, '["msg1"]', 'gua', 'cat', 'bg')
        db = auth.get_db()
        row = db.execute("SELECT * FROM conversations WHERE session_id = 'sess_1'").fetchone()
        auth.release_db(db)
        assert row is not None
        assert row['messages'] == '["msg1"]'

    def test_update_preserves_created_at(self, test_db):
        auth.save_conversation('sess_2', None, '["msg1"]')
        db = auth.get_db()
        created = db.execute("SELECT created_at FROM conversations WHERE session_id = 'sess_2'").fetchone()['created_at']
        auth.release_db(db)
        auth.save_conversation('sess_2', None, '["msg1","msg2"]')
        db = auth.get_db()
        row = db.execute("SELECT * FROM conversations WHERE session_id = 'sess_2'").fetchone()
        auth.release_db(db)
        assert row['messages'] == '["msg1","msg2"]'
        assert row['created_at'] == created
