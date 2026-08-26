import os

# 必须在所有 import 之前设置环境变量，config.py 加载时会校验
os.environ.setdefault('JWT_SECRET', 'test-secret-key-for-testing')
os.environ.setdefault('DEEPSEEK_API_KEY', 'fake-key-for-testing')
os.environ.setdefault('DEEPSEEK_API_BASE', 'https://api.deepseek.com')

import pytest


@pytest.fixture()
def test_db(monkeypatch, tmp_path):
    """将 auth.DB_PATH 指向临时文件，每个测试函数独立数据库"""
    db_file = str(tmp_path / "test_users.db")

    import auth
    monkeypatch.setattr(auth, 'DB_PATH', db_file)
    # 连接池在模块加载时已绑定真实 DB_PATH，必须一并替换，
    # 否则 get_db() 仍连到生产库 users.db，测试数据会写进去
    monkeypatch.setattr(auth, '_db_pool', auth._DBPool(db_file))

    import db_backup
    monkeypatch.setattr(db_backup, 'DB_PATH', db_file)
    monkeypatch.setattr(db_backup, 'BACKUP_DIR', str(tmp_path / "backups"))

    auth.init_db()
    yield db_file


@pytest.fixture()
def registered_user(test_db):
    """注册一个标准测试用户"""
    import auth
    result, error = auth.register_user('testuser', 'password123', email='test@example.com')
    assert error is None, f"注册失败: {error}"
    return result
