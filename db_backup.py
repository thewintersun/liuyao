"""SQLite 数据库自动备份模块

使用 sqlite3.backup() 热备份，不阻塞正常读写。
后台线程定期自动备份，保留最近 N 份。
"""
import os
import sqlite3
import logging
import threading
import time
from datetime import datetime
from config import BACKUP_KEEP, BACKUP_INTERVAL

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')


def backup_now():
    """立即执行一次数据库备份，返回备份文件路径或 None"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'users_{timestamp}.db')

    try:
        src = sqlite3.connect(DB_PATH)
        dst = sqlite3.connect(backup_path)
        src.backup(dst)
        dst.close()
        src.close()
        logger.info(f"数据库备份成功: {backup_path}")
        _cleanup_old_backups()
        return backup_path
    except Exception as e:
        logger.error(f"数据库备份失败: {e}")
        return None


def _cleanup_old_backups():
    """删除超出保留数量的旧备份"""
    try:
        files = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.startswith('users_') and f.endswith('.db')],
            reverse=True
        )
        for old_file in files[BACKUP_KEEP:]:
            path = os.path.join(BACKUP_DIR, old_file)
            os.remove(path)
            logger.info(f"已删除旧备份: {old_file}")
    except Exception as e:
        logger.error(f"清理旧备份失败: {e}")


def start_backup_scheduler():
    """启动后台备份线程"""
    def _loop():
        while True:
            time.sleep(BACKUP_INTERVAL)
            backup_now()

    # 启动时立即备份一次
    backup_now()
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    logger.info(f"数据库自动备份已启动 (每 {BACKUP_INTERVAL // 3600} 小时, 保留 {BACKUP_KEEP} 份)")
