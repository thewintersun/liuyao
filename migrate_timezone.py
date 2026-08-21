"""存量数据时区迁移：UTC → 服务器本地时区

背景：
    SQLite 的 CURRENT_TIMESTAMP 返回 UTC 时间，本项目早期所有时间列都是 UTC，
    前端 records.date 也用 toISOString() 存成了 UTC。
    代码已改为统一写入本地时间，存量数据必须一并转换，否则新旧数据混在一起，
    排序和"今日"统计都会有一个时区差的偏移。

用法：
    python migrate_timezone.py --dry-run    # 预演，只打印将要发生的变化，不写库
    python migrate_timezone.py              # 实际执行（会先自动备份）

幂等性：
    脚本会在 system_config 写入 timezone_migrated 标记，重复执行会直接退出，
    避免二次转换（那会让时间再偏移一个时区差）。
"""
import os
import sys
import shutil
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')
MIGRATION_KEY = 'timezone_migrated'

# (表名, [时间列...])  —— 数据库时间列，格式 'YYYY-MM-DD HH:MM:SS'
DB_TIME_COLUMNS = [
    ('users', ['created_at', 'agreed_at', 'last_login_at']),
    ('usage_log', ['created_at']),
    ('records', ['created_at']),
    ('system_config', ['updated_at']),
    ('feedback', ['created_at']),
    ('password_reset_tokens', ['created_at']),
    ('conversations', ['created_at', 'updated_at']),
    ('invite_records', ['created_at']),
]


def table_exists(db, name):
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def column_exists(db, table, col):
    return any(r[1] == col for r in db.execute(f'PRAGMA table_info({table})'))


def already_migrated(db):
    if not table_exists(db, 'system_config'):
        return False
    row = db.execute(
        'SELECT value FROM system_config WHERE key = ?', (MIGRATION_KEY,)
    ).fetchone()
    return row is not None


def backup():
    # 本库开启了 WAL，未 checkpoint 的数据还在 -wal 文件里，
    # 直接拷贝 users.db 会得到一个缺数据的备份，必须先落盘
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    conn.close()
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = f'{DB_PATH}.utc_backup_{stamp}'
    shutil.copy2(DB_PATH, dst)
    return dst


def main():
    dry_run = '--dry-run' in sys.argv

    if not os.path.exists(DB_PATH):
        print(f'数据库不存在: {DB_PATH}')
        return 1

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    if already_migrated(db):
        print('该库已迁移过（system_config.timezone_migrated 存在），跳过。')
        print('如需强制重跑，请先删除该配置项——但注意会造成二次时区偏移。')
        return 0

    offset = db.execute(
        "SELECT ROUND((julianday('now','localtime') - julianday('now')) * 24, 2)"
    ).fetchone()[0]
    print(f'服务器本地时区相对 UTC 偏移: {offset:+g} 小时')
    print(f'模式: {"预演（不写库）" if dry_run else "实际执行"}')
    print()

    plan = []

    # 1) 数据库时间列：把 UTC 值按 localtime 重新解释
    for table, cols in DB_TIME_COLUMNS:
        if not table_exists(db, table):
            continue
        for col in cols:
            if not column_exists(db, table, col):
                continue
            n = db.execute(
                f'SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL AND {col} != ""'
            ).fetchone()[0]
            if n == 0:
                continue
            sample = db.execute(
                f'SELECT {col} AS v, datetime({col}, \'localtime\') AS nv '
                f'FROM {table} WHERE {col} IS NOT NULL AND {col} != "" LIMIT 1'
            ).fetchone()
            plan.append((table, col, n, sample['v'], sample['nv']))
            print(f'  {table}.{col:12s} {n:5d} 行   示例 {sample["v"]} → {sample["nv"]}')
            if not dry_run:
                db.execute(
                    f'UPDATE {table} SET {col} = datetime({col}, \'localtime\') '
                    f'WHERE {col} IS NOT NULL AND {col} != ""'
                )

    # 2) records.date：前端存的 UTC ISO（2026-08-21T13:00:00.000Z）
    #    → 本地无偏移 ISO（2026-08-21T21:00:00），与新前端写入的格式一致
    if table_exists(db, 'records'):
        n = db.execute(
            "SELECT COUNT(*) FROM records WHERE date LIKE '%Z'"
        ).fetchone()[0]
        if n:
            sample = db.execute(
                "SELECT date AS v, replace(datetime(date,'localtime'),' ','T') AS nv "
                "FROM records WHERE date LIKE '%Z' LIMIT 1"
            ).fetchone()
            print(f'  records.date         {n:5d} 行   示例 {sample["v"]} → {sample["nv"]}')
            plan.append(('records', 'date', n, sample['v'], sample['nv']))
            if not dry_run:
                db.execute(
                    "UPDATE records SET date = replace(datetime(date,'localtime'),' ','T') "
                    "WHERE date LIKE '%Z'"
                )

    if not plan:
        print('  没有需要迁移的数据。')

    print()
    total = sum(p[2] for p in plan)
    if dry_run:
        print(f'预演结束，共 {total} 个值将被转换。确认无误后去掉 --dry-run 实际执行。')
        db.close()
        return 0

    db.execute(
        'INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?, ?, ?)',
        (MIGRATION_KEY, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
         datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    db.commit()
    db.close()
    print(f'迁移完成，共转换 {total} 个值。')
    return 0


if __name__ == '__main__':
    if '--dry-run' not in sys.argv:
        if not os.path.exists(DB_PATH):
            print(f'数据库不存在: {DB_PATH}')
            sys.exit(1)
        path = backup()
        print(f'已备份原库到: {path}')
        print()
    sys.exit(main())
