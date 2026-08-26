import os
import time
import sqlite3
import pytest


class TestBackupNow:
    def test_creates_file(self, test_db, tmp_path):
        import db_backup
        path = db_backup.backup_now()
        assert path is not None
        assert os.path.exists(path)

    def test_valid_sqlite(self, test_db, tmp_path):
        import db_backup
        path = db_backup.backup_now()
        conn = sqlite3.connect(path)
        tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        assert 'users' in tables


class TestCleanup:
    def test_keeps_only_n(self, test_db, tmp_path, monkeypatch):
        import db_backup
        monkeypatch.setattr(db_backup, 'BACKUP_KEEP', 2)
        # 直接创建不同名的备份文件来测试清理逻辑
        os.makedirs(db_backup.BACKUP_DIR, exist_ok=True)
        for i in range(4):
            fake_path = os.path.join(db_backup.BACKUP_DIR, f'users_2026010{i}_120000.db')
            open(fake_path, 'w').close()
        db_backup._cleanup_old_backups()
        files = [f for f in os.listdir(db_backup.BACKUP_DIR) if f.endswith('.db')]
        assert len(files) == 2
