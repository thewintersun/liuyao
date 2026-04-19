import os
import json
import sqlite3
import time
import secrets
from functools import wraps
from flask import request, g, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import re
import jwt
from config import (JWT_SECRET, JWT_EXPIRY, REGISTERED_FREE_USES, GUEST_FREE_USES,
                     INVITE_VISIT_REWARD, INVITE_REGISTER_REWARD, INVITE_REGISTER_BONUS,
                     INVITE_MONTHLY_LIMIT, INVITE_IP_DAILY_LIMIT)

EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def generate_invite_code(db=None):
    """生成唯一 6 位邀请码（大写字母+数字）"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    close_db = False
    if db is None:
        db = get_db()
        close_db = True
    for _ in range(100):
        code = ''.join(random.choices(chars, k=6))
        existing = db.execute('SELECT id FROM users WHERE invite_code = ?', (code,)).fetchone()
        if not existing:
            if close_db:
                db.close()
            return code
    if close_db:
        db.close()
    return secrets.token_hex(3).upper()[:6]


def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        free_uses INTEGER DEFAULT 3,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS usage_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        session_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS records (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        date TEXT,
        yao_values TEXT,
        session_id TEXT,
        messages TEXT,
        category TEXT,
        background TEXT,
        gua_xiang_info TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    # 数据库迁移：添加 role 字段
    try:
        db.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        db.commit()
    except Exception:
        pass  # 列已存在

    # 数据库迁移：添加 email 字段
    try:
        db.execute("ALTER TABLE users ADD COLUMN email TEXT")
        db.commit()
    except Exception:
        pass  # 列已存在

    # 数据库迁移：添加 token_version 字段（用于改密码后撤销旧 JWT）
    try:
        db.execute("ALTER TABLE users ADD COLUMN token_version INTEGER DEFAULT 0")
        db.commit()
    except Exception:
        pass  # 列已存在

    # 数据库迁移：添加协议同意留证字段
    for col, col_type in [
        ('agreed_version', 'TEXT'),
        ('agreed_at', 'TIMESTAMP'),
        ('agreed_ip', 'TEXT'),
    ]:
        try:
            db.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            db.commit()
        except Exception:
            pass  # 列已存在

    # 数据库迁移：添加最后登录 IP 和时间字段
    for col, col_type in [
        ('last_login_ip', 'TEXT'),
        ('last_login_at', 'TIMESTAMP'),
    ]:
        try:
            db.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            db.commit()
        except Exception:
            pass  # 列已存在

    # 数据库迁移：usage_log 添加 ip 字段
    try:
        db.execute("ALTER TABLE usage_log ADD COLUMN ip TEXT")
        db.commit()
    except Exception:
        pass  # 列已存在

    # 初始化协议版本号（若不存在）
    try:
        db.execute(
            "INSERT OR IGNORE INTO system_config (key, value) VALUES ('terms_privacy_version', '1.0')"
        )
        db.commit()
    except Exception:
        pass  # system_config 表可能尚未建立（首次冷启动顺序问题）

    # 新建 password_reset_tokens 表
    db.execute('''CREATE TABLE IF NOT EXISTS password_reset_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # 新建 system_config 表
    db.execute('''CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 新建 feedback 表
    db.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        feedback TEXT NOT NULL,
        contact TEXT,
        status TEXT DEFAULT 'unread',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 数据库迁移：添加邀请相关字段
    for col, col_type in [
        ('invite_code', 'TEXT'),
        ('invited_by', 'INTEGER'),
    ]:
        try:
            db.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            db.commit()
        except Exception:
            pass  # 列已存在

    # 为已有用户补生成 invite_code
    try:
        users_without_code = db.execute('SELECT id FROM users WHERE invite_code IS NULL').fetchall()
        for u in users_without_code:
            code = generate_invite_code(db)
            db.execute('UPDATE users SET invite_code = ? WHERE id = ?', (code, u['id']))
        if users_without_code:
            db.commit()
    except Exception:
        pass

    # 新建 invite_records 表
    db.execute('''CREATE TABLE IF NOT EXISTS invite_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inviter_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        visitor_ip TEXT,
        invitee_id INTEGER,
        reward INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (inviter_id) REFERENCES users(id)
    )''')

    # 新建 conversations 表（对话自动持久化）
    db.execute('''CREATE TABLE IF NOT EXISTS conversations (
        session_id TEXT PRIMARY KEY,
        user_id INTEGER,
        messages TEXT,
        gua_xiang_info TEXT,
        category TEXT,
        background TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    db.commit()
    db.close()


def register_user(username, password, email=None, agreed_version=None, agreed_at=None, agreed_ip=None, invite_code=None):
    if not username or not password:
        return None, '用户名和密码不能为空'
    if len(username) < 2 or len(username) > 20:
        return None, '用户名长度需在2-20个字符之间'
    if len(password) < 6:
        return None, '密码长度不能少于6个字符'
    if not email or not email.strip():
        return None, '邮箱不能为空'
    if not EMAIL_RE.match(email.strip()):
        return None, '邮箱格式不正确'

    db = get_db()
    try:
        # 从数据库配置读取注册赠送额度，fallback 到 config.py
        row = db.execute("SELECT value FROM system_config WHERE key = 'REGISTERED_FREE_USES'").fetchone()
        free_uses = int(row['value']) if row else REGISTERED_FREE_USES

        # 查找邀请人
        inviter = None
        if invite_code and invite_code.strip():
            inviter = db.execute('SELECT id FROM users WHERE invite_code = ?', (invite_code.strip().upper(),)).fetchone()

        # 生成新用户的邀请码
        new_invite_code = generate_invite_code(db)

        db.execute(
            'INSERT INTO users (username, password_hash, free_uses, email, agreed_version, agreed_at, agreed_ip, invite_code, invited_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (username, generate_password_hash(password), free_uses, email.strip(), agreed_version, agreed_at, agreed_ip, new_invite_code, inviter['id'] if inviter else None)
        )
        db.commit()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        # 处理邀请注册奖励
        if inviter:
            _process_invite_register_reward(db, inviter['id'], user['id'])
            # 重新读取 user 以获取可能增加的额度
            user = db.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()

        token = _generate_token(user['id'], user['username'], user['token_version'] or 0)
        return {
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'free_uses': user['free_uses'],
                'created_at': user['created_at'],
                'role': user['role'],
                'email': user['email']
            }
        }, None
    except sqlite3.IntegrityError:
        return None, '用户名已存在'
    finally:
        db.close()


def login_user(username, password, ip=None):
    if not username or not password:
        return None, '用户名和密码不能为空'

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if not user or not check_password_hash(user['password_hash'], password):
        db.close()
        return None, '用户名或密码错误'

    # 检查是否被封禁
    if user['role'] == 'banned':
        db.close()
        return None, '账户已被封禁'

    # 记录最后登录 IP 和时间
    if ip:
        db.execute(
            'UPDATE users SET last_login_ip = ?, last_login_at = CURRENT_TIMESTAMP WHERE id = ?',
            (ip, user['id'])
        )
        db.commit()

    db.close()

    token = _generate_token(user['id'], user['username'], user['token_version'] or 0)
    return {
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'free_uses': user['free_uses'],
            'created_at': user['created_at'],
            'role': user['role'],
            'email': user['email']
        }
    }, None


def get_user_info(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()
    if not user:
        return None
    return {
        'id': user['id'],
        'username': user['username'],
        'free_uses': user['free_uses'],
        'created_at': user['created_at'],
        'role': user['role'],
        'email': user['email']
    }


def check_credit(user_id):
    """检查用户是否还有额度（不扣减）"""
    db = get_db()
    user = db.execute('SELECT free_uses FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()
    return bool(user and user['free_uses'] > 0)


def log_usage(action, session_id=None, user_id=None, ip=None):
    """仅记录使用日志，不扣减额度（用于游客等场景）"""
    db = get_db()
    db.execute(
        'INSERT INTO usage_log (user_id, action, session_id, ip) VALUES (?, ?, ?, ?)',
        (user_id, action, session_id, ip)
    )
    db.commit()
    db.close()


def use_credit(user_id, action, session_id=None, ip=None):
    db = get_db()
    user = db.execute('SELECT free_uses FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user or user['free_uses'] <= 0:
        db.close()
        return False, 0
    db.execute('UPDATE users SET free_uses = free_uses - 1 WHERE id = ?', (user_id,))
    db.execute(
        'INSERT INTO usage_log (user_id, action, session_id, ip) VALUES (?, ?, ?, ?)',
        (user_id, action, session_id, ip)
    )
    db.commit()
    remaining = db.execute('SELECT free_uses FROM users WHERE id = ?', (user_id,)).fetchone()['free_uses']
    db.close()
    return True, remaining


def _generate_token(user_id, username, token_version=0):
    payload = {
        'user_id': user_id,
        'username': username,
        'tv': token_version,
        'exp': int(time.time()) + JWT_EXPIRY
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def _decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({'error': 'unauthorized', 'message': '请先登录'}), 401
        payload = _decode_token(token)
        if not payload:
            return jsonify({'error': 'unauthorized', 'message': '登录已过期，请重新登录'}), 401
        # 封禁检查 + token 版本校验
        db = get_db()
        user = db.execute('SELECT role, token_version FROM users WHERE id = ?', (payload['user_id'],)).fetchone()
        db.close()
        if not user:
            return jsonify({'error': 'unauthorized', 'message': '用户不存在'}), 401
        if user['role'] == 'banned':
            return jsonify({'error': 'forbidden', 'message': '账户已被封禁'}), 403
        if payload.get('tv', 0) != (user['token_version'] or 0):
            return jsonify({'error': 'unauthorized', 'message': '密码已变更，请重新登录'}), 401
        g.user_id = payload['user_id']
        g.username = payload['username']
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        db = get_db()
        user = db.execute('SELECT role FROM users WHERE id = ?', (g.user_id,)).fetchone()
        db.close()
        if not user or user['role'] != 'admin':
            return jsonify({'error': 'forbidden', 'message': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated


def optional_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        g.user_id = None
        g.username = None
        if token:
            payload = _decode_token(token)
            if payload:
                # 封禁检查 + token 版本校验：不通过则视为未登录
                db = get_db()
                user = db.execute('SELECT role, token_version FROM users WHERE id = ?', (payload['user_id'],)).fetchone()
                db.close()
                if user and user['role'] != 'banned' and payload.get('tv', 0) == (user['token_version'] or 0):
                    g.user_id = payload['user_id']
                    g.username = payload['username']
        return f(*args, **kwargs)
    return decorated


def _extract_token():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None


# ========== Records CRUD ==========

def get_user_records(user_id):
    db = get_db()
    rows = db.execute('SELECT * FROM records WHERE user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
    db.close()
    records = []
    for row in rows:
        records.append(_row_to_record(row))
    return records


def get_user_record_by_id(record_id, user_id):
    db = get_db()
    row = db.execute('SELECT * FROM records WHERE id = ? AND user_id = ?', (record_id, user_id)).fetchone()
    db.close()
    if not row:
        return None
    return _row_to_record(row)


def create_user_record(user_id, record_data):
    db = get_db()
    record_id = _generate_record_id()
    db.execute(
        '''INSERT INTO records (id, user_id, title, date, yao_values, session_id, messages, category, background, gua_xiang_info)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            record_id,
            user_id,
            record_data.get('title', ''),
            record_data.get('date', ''),
            json.dumps(record_data.get('yaoValues'), ensure_ascii=False) if record_data.get('yaoValues') is not None else None,
            record_data.get('sessionId', ''),
            json.dumps(record_data.get('messages'), ensure_ascii=False) if record_data.get('messages') is not None else None,
            json.dumps(record_data.get('category'), ensure_ascii=False) if record_data.get('category') is not None else None,
            record_data.get('background', ''),
            json.dumps(record_data.get('guaXiangInfo'), ensure_ascii=False) if record_data.get('guaXiangInfo') is not None else None,
        )
    )
    db.commit()
    row = db.execute('SELECT * FROM records WHERE id = ?', (record_id,)).fetchone()
    db.close()
    return _row_to_record(row)


def update_user_record(record_id, user_id, updates):
    allowed_fields = {
        'title': 'title',
        'date': 'date',
        'yaoValues': 'yao_values',
        'sessionId': 'session_id',
        'messages': 'messages',
        'category': 'category',
        'background': 'background',
        'guaXiangInfo': 'gua_xiang_info',
    }
    json_fields = {'yaoValues', 'messages', 'category', 'guaXiangInfo'}
    sets = []
    values = []
    for js_key, db_col in allowed_fields.items():
        if js_key in updates:
            sets.append(f'{db_col} = ?')
            val = updates[js_key]
            if js_key in json_fields and val is not None:
                val = json.dumps(val, ensure_ascii=False)
            values.append(val)
    if not sets:
        return False
    values.extend([record_id, user_id])
    db = get_db()
    cursor = db.execute(
        f'UPDATE records SET {", ".join(sets)} WHERE id = ? AND user_id = ?',
        values
    )
    db.commit()
    affected = cursor.rowcount
    db.close()
    return affected > 0


def delete_user_record(record_id, user_id):
    db = get_db()
    cursor = db.execute('DELETE FROM records WHERE id = ? AND user_id = ?', (record_id, user_id))
    db.commit()
    affected = cursor.rowcount
    db.close()
    return affected > 0


def _row_to_record(row):
    return {
        'id': row['id'],
        'title': row['title'],
        'date': row['date'],
        'yaoValues': json.loads(row['yao_values']) if row['yao_values'] else None,
        'sessionId': row['session_id'],
        'messages': json.loads(row['messages']) if row['messages'] else None,
        'category': json.loads(row['category']) if row['category'] else None,
        'background': row['background'],
        'guaXiangInfo': json.loads(row['gua_xiang_info']) if row['gua_xiang_info'] else None,
        'createdAt': row['created_at'],
    }


def _generate_record_id():
    import random
    import string
    t = int(time.time() * 1000)
    r = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f'{t:x}{r}'


# ========== 修改密码 ==========

def change_password(user_id, old_password, new_password):
    """用户自行修改密码，需验证旧密码"""
    if not old_password or not new_password:
        return False, '请填写完整'
    if len(new_password) < 6:
        return False, '新密码长度不能少于6个字符'
    db = get_db()
    user = db.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        db.close()
        return False, '用户不存在'
    if not check_password_hash(user['password_hash'], old_password):
        db.close()
        return False, '原密码错误'
    db.execute(
        'UPDATE users SET password_hash = ?, token_version = COALESCE(token_version, 0) + 1 WHERE id = ?',
        (generate_password_hash(new_password), user_id)
    )
    db.commit()
    db.close()
    return True, None


# ========== 修改邮箱 ==========

def change_email(user_id, new_email):
    """用户��行修改邮箱"""
    if not new_email or not new_email.strip():
        return False, '邮箱不能为空'
    new_email = new_email.strip()
    if not EMAIL_RE.match(new_email):
        return False, '邮箱格���不正确'
    db = get_db()
    # 检查邮箱是否已被其他用户使用
    existing = db.execute('SELECT id FROM users WHERE email = ? AND id != ?', (new_email, user_id)).fetchone()
    if existing:
        db.close()
        return False, '该邮箱已被其他账户使用'
    cursor = db.execute('UPDATE users SET email = ? WHERE id = ?', (new_email, user_id))
    db.commit()
    affected = cursor.rowcount
    db.close()
    if affected == 0:
        return False, '用户不存在'
    return True, None


# ========== 密码重置 ==========

def reset_password(user_id, new_password):
    """直接重置密码（管理员用）"""
    if not new_password or len(new_password) < 6:
        return False, '密码长度不能少于6个字符'
    db = get_db()
    cursor = db.execute(
        'UPDATE users SET password_hash = ?, token_version = COALESCE(token_version, 0) + 1 WHERE id = ?',
        (generate_password_hash(new_password), user_id)
    )
    db.commit()
    affected = cursor.rowcount
    db.close()
    if affected == 0:
        return False, '用户不存在'
    return True, None


def create_reset_token(email):
    """通过邮箱查找用户并生成重置 token"""
    if not email or not email.strip():
        return None, None
    db = get_db()
    # 清理过期和已使用的 token，防止表无限增长
    db.execute("DELETE FROM password_reset_tokens WHERE used = 1 OR created_at < datetime('now', '-1 hour')")
    user = db.execute('SELECT id, username, email FROM users WHERE email = ?', (email.strip(),)).fetchone()
    if not user:
        db.commit()
        db.close()
        return None, None
    token = secrets.token_hex(32)
    db.execute(
        'INSERT INTO password_reset_tokens (token, user_id) VALUES (?, ?)',
        (token, user['id'])
    )
    db.commit()
    db.close()
    return token, dict(user)


def validate_reset_token(token):
    """验证 token 是否有效（30 分钟内且未使用）"""
    db = get_db()
    row = db.execute(
        "SELECT user_id, created_at, used FROM password_reset_tokens WHERE token = ?",
        (token,)
    ).fetchone()
    db.close()
    if not row:
        return None
    if row['used']:
        return None
    # 检查是否在 30 分钟内
    from datetime import datetime, timedelta
    created = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
    if datetime.utcnow() - created > timedelta(minutes=30):
        return None
    return row['user_id']


def reset_password_with_token(token, new_password):
    """验证 token 后重置密码"""
    if not new_password or len(new_password) < 6:
        return False, '密码长度不能少于6个字符'
    user_id = validate_reset_token(token)
    if not user_id:
        return False, '重置链接无效或已过期'
    db = get_db()
    db.execute(
        'UPDATE users SET password_hash = ?, token_version = COALESCE(token_version, 0) + 1 WHERE id = ?',
        (generate_password_hash(new_password), user_id)
    )
    db.execute(
        'UPDATE password_reset_tokens SET used = 1 WHERE token = ?',
        (token,)
    )
    db.commit()
    db.close()
    return True, None


# ========== IP 地理位置查询 ==========

def get_ip_location(ip):
    """通过 ip-api.com 查询 IP 地理位置，内网 IP 返回"本地网络"，异常返回"未知" """
    if not ip:
        return '未知'
    # 内网/本地 IP 判断
    if ip in ('127.0.0.1', '::1', 'localhost') or ip.startswith(('10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.')):
        return '本地网络'
    try:
        import urllib.request
        url = f'http://ip-api.com/json/{ip}?lang=zh-CN&fields=status,country,regionName,city'
        req = urllib.request.Request(url, headers={'User-Agent': 'liuyao-app'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('status') == 'success':
                parts = [data.get('country', ''), data.get('regionName', ''), data.get('city', '')]
                return ' '.join(p for p in parts if p)
    except Exception:
        pass
    return '未知'


# ========== 对话持久化 ==========

def _get_config_int(db, key, default):
    """从 system_config 读取整数配置，fallback 到默认值"""
    row = db.execute("SELECT value FROM system_config WHERE key = ?", (key,)).fetchone()
    return int(row['value']) if row else default


def _get_monthly_invite_count(db, inviter_id):
    """获取邀请人当月邀请记录数"""
    return db.execute(
        "SELECT COUNT(*) as cnt FROM invite_records WHERE inviter_id = ? AND created_at >= date('now', 'start of month')",
        (inviter_id,)
    ).fetchone()['cnt']


def _process_invite_register_reward(db, inviter_id, invitee_id):
    """处理邀请注册奖励：检查月度上限 → 双方加额度 → 写记录"""
    monthly_limit = _get_config_int(db, 'INVITE_MONTHLY_LIMIT', INVITE_MONTHLY_LIMIT)
    current_count = _get_monthly_invite_count(db, inviter_id)
    if current_count >= monthly_limit:
        return  # 已达月度上限

    inviter_reward = _get_config_int(db, 'INVITE_REGISTER_REWARD', INVITE_REGISTER_REWARD)
    invitee_bonus = _get_config_int(db, 'INVITE_REGISTER_BONUS', INVITE_REGISTER_BONUS)

    # 邀请人加额度
    db.execute('UPDATE users SET free_uses = free_uses + ? WHERE id = ?', (inviter_reward, inviter_id))
    # 被邀请人加额度
    db.execute('UPDATE users SET free_uses = free_uses + ? WHERE id = ?', (invitee_bonus, invitee_id))
    # 写记录
    db.execute(
        'INSERT INTO invite_records (inviter_id, type, invitee_id, reward) VALUES (?, ?, ?, ?)',
        (inviter_id, 'register', invitee_id, inviter_reward)
    )
    db.commit()


def process_invite_visit(invite_code, visitor_ip):
    """处理游客访问邀请链接奖励"""
    if not invite_code or not invite_code.strip():
        return False, '邀请码不能为空'

    db = get_db()
    try:
        # 查找邀请人
        inviter = db.execute('SELECT id FROM users WHERE invite_code = ?', (invite_code.strip().upper(),)).fetchone()
        if not inviter:
            return False, '邀请码无效'

        # 检查 IP 24h 限流
        ip_daily_limit = _get_config_int(db, 'INVITE_IP_DAILY_LIMIT', INVITE_IP_DAILY_LIMIT)
        ip_count = db.execute(
            "SELECT COUNT(*) as cnt FROM invite_records WHERE type = 'visit' AND visitor_ip = ? AND created_at >= datetime('now', '-24 hours')",
            (visitor_ip,)
        ).fetchone()['cnt']
        if ip_count >= ip_daily_limit:
            return False, 'IP 访问奖励已达上限'

        # 检查月度上限
        monthly_limit = _get_config_int(db, 'INVITE_MONTHLY_LIMIT', INVITE_MONTHLY_LIMIT)
        current_count = _get_monthly_invite_count(db, inviter['id'])
        if current_count >= monthly_limit:
            return False, '邀请人本月邀请已达上限'

        visit_reward = _get_config_int(db, 'INVITE_VISIT_REWARD', INVITE_VISIT_REWARD)

        # 邀请人加额度
        db.execute('UPDATE users SET free_uses = free_uses + ? WHERE id = ?', (visit_reward, inviter['id']))
        # 写记录
        db.execute(
            'INSERT INTO invite_records (inviter_id, type, visitor_ip, reward) VALUES (?, ?, ?, ?)',
            (inviter['id'], 'visit', visitor_ip, visit_reward)
        )
        db.commit()
        return True, None
    finally:
        db.close()


def get_invite_stats(user_id):
    """查询用户的邀请统计和记录列表"""
    db = get_db()
    try:
        user = db.execute('SELECT invite_code FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return None

        # 本月统计
        monthly_count = _get_monthly_invite_count(db, user_id)
        monthly_reward = db.execute(
            "SELECT COALESCE(SUM(reward), 0) as total FROM invite_records WHERE inviter_id = ? AND created_at >= date('now', 'start of month')",
            (user_id,)
        ).fetchone()['total']

        # 总统计
        total_count = db.execute(
            'SELECT COUNT(*) as cnt FROM invite_records WHERE inviter_id = ?', (user_id,)
        ).fetchone()['cnt']
        total_reward = db.execute(
            'SELECT COALESCE(SUM(reward), 0) as total FROM invite_records WHERE inviter_id = ?', (user_id,)
        ).fetchone()['total']

        # 最近 50 条记录
        records = db.execute(
            '''SELECT ir.type, ir.visitor_ip, ir.reward, ir.created_at, u.username as invitee_name
               FROM invite_records ir
               LEFT JOIN users u ON ir.invitee_id = u.id
               WHERE ir.inviter_id = ?
               ORDER BY ir.id DESC LIMIT 50''',
            (user_id,)
        ).fetchall()

        monthly_limit = _get_config_int(db, 'INVITE_MONTHLY_LIMIT', INVITE_MONTHLY_LIMIT)

        return {
            'invite_code': user['invite_code'],
            'monthly_count': monthly_count,
            'monthly_reward': monthly_reward,
            'monthly_limit': monthly_limit,
            'total_count': total_count,
            'total_reward': total_reward,
            'records': [dict(r) for r in records]
        }
    finally:
        db.close()


def save_conversation(session_id, user_id, messages_json, gua_xiang_info=None, category=None, background=None):
    """自动保存/更新对话到 conversations 表"""
    db = get_db()
    try:
        db.execute(
            '''INSERT OR REPLACE INTO conversations
               (session_id, user_id, messages, gua_xiang_info, category, background, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?,
                   COALESCE((SELECT created_at FROM conversations WHERE session_id = ?), CURRENT_TIMESTAMP),
                   CURRENT_TIMESTAMP)''',
            (session_id, user_id, messages_json, gua_xiang_info, category, background, session_id)
        )
        db.commit()
    except Exception as e:
        print(f"保存对话失败: {e}")
    finally:
        db.close()
