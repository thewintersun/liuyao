"""管理后台业务逻辑"""
import json
from auth import get_db, reset_password, get_ip_location
from config import (GUEST_FREE_USES, REGISTERED_FREE_USES,
                     INVITE_VISIT_REWARD, INVITE_REGISTER_REWARD, INVITE_REGISTER_BONUS,
                     INVITE_MONTHLY_LIMIT, INVITE_IP_DAILY_LIMIT)
from llm.common.config import SYSTEM_PROMPT, LIUYAO_PROMPT


# ========== 数据看板 ==========

def get_dashboard_stats(dialog_manager=None):
    db = get_db()
    total_users = db.execute('SELECT COUNT(*) as cnt FROM users').fetchone()['cnt']
    today_users = db.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE date(created_at) = date('now')"
    ).fetchone()['cnt']
    total_divinations = db.execute('SELECT COUNT(*) as cnt FROM usage_log').fetchone()['cnt']
    today_divinations = db.execute(
        "SELECT COUNT(*) as cnt FROM usage_log WHERE date(created_at) = date('now')"
    ).fetchone()['cnt']
    db.close()

    active_sessions = 0
    if dialog_manager:
        active_sessions = dialog_manager.get_current_active_user_number()

    return {
        'total_users': total_users,
        'today_users': today_users,
        'total_divinations': total_divinations,
        'today_divinations': today_divinations,
        'active_sessions': active_sessions
    }


# ========== 用户管理 ==========

def get_all_users(page=1, per_page=20, search=None):
    db = get_db()
    offset = (page - 1) * per_page

    if search:
        total = db.execute(
            'SELECT COUNT(*) as cnt FROM users WHERE username LIKE ?',
            (f'%{search}%',)
        ).fetchone()['cnt']
        rows = db.execute(
            'SELECT id, username, role, free_uses, created_at FROM users WHERE username LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?',
            (f'%{search}%', per_page, offset)
        ).fetchall()
    else:
        total = db.execute('SELECT COUNT(*) as cnt FROM users').fetchone()['cnt']
        rows = db.execute(
            'SELECT id, username, role, free_uses, created_at FROM users ORDER BY id DESC LIMIT ? OFFSET ?',
            (per_page, offset)
        ).fetchall()

    db.close()
    users = [dict(row) for row in rows]
    return {
        'users': users,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }


def get_user_detail(user_id):
    db = get_db()
    user = db.execute(
        'SELECT id, username, role, free_uses, email, created_at, last_login_ip, last_login_at FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    if not user:
        db.close()
        return None

    total_uses = db.execute(
        'SELECT COUNT(*) as cnt FROM usage_log WHERE user_id = ?',
        (user_id,)
    ).fetchone()['cnt']

    action_stats = db.execute(
        'SELECT action, COUNT(*) as cnt FROM usage_log WHERE user_id = ? GROUP BY action',
        (user_id,)
    ).fetchall()

    db.close()

    result = {
        **dict(user),
        'total_uses': total_uses,
        'action_stats': {row['action']: row['cnt'] for row in action_stats}
    }

    # 查询 IP 地理位置（延迟查询，不在登录时调用）
    result['last_login_location'] = get_ip_location(user['last_login_ip']) if user['last_login_ip'] else None

    return result


def update_user_quota(user_id, free_uses):
    db = get_db()
    db.execute('UPDATE users SET free_uses = ? WHERE id = ?', (free_uses, user_id))
    db.commit()
    db.close()


def ban_user(user_id):
    db = get_db()
    # 不允许封禁管理员
    user = db.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        db.close()
        return False, '用户不存在'
    if user['role'] == 'admin':
        db.close()
        return False, '不能封禁管理员'
    db.execute("UPDATE users SET role = 'banned' WHERE id = ?", (user_id,))
    db.commit()
    db.close()
    return True, None


def unban_user(user_id):
    db = get_db()
    db.execute("UPDATE users SET role = 'user' WHERE id = ? AND role = 'banned'", (user_id,))
    db.commit()
    db.close()
    return True, None


def admin_reset_password(user_id, new_password):
    """管理员重置用户密码"""
    return reset_password(user_id, new_password)


# ========== 系统配置 ==========

def get_system_config(key):
    db = get_db()
    row = db.execute('SELECT value FROM system_config WHERE key = ?', (key,)).fetchone()
    db.close()
    if row:
        return row['value']
    # fallback 到 config.py 默认值
    defaults = {
        'GUEST_FREE_USES': str(GUEST_FREE_USES),
        'REGISTERED_FREE_USES': str(REGISTERED_FREE_USES),
        'INVITE_VISIT_REWARD': str(INVITE_VISIT_REWARD),
        'INVITE_REGISTER_REWARD': str(INVITE_REGISTER_REWARD),
        'INVITE_REGISTER_BONUS': str(INVITE_REGISTER_BONUS),
        'INVITE_MONTHLY_LIMIT': str(INVITE_MONTHLY_LIMIT),
        'INVITE_IP_DAILY_LIMIT': str(INVITE_IP_DAILY_LIMIT),
    }
    return defaults.get(key)


def update_system_config(key, value):
    db = get_db()
    db.execute(
        'INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
        (key, value)
    )
    db.commit()
    db.close()


def get_all_configs():
    configs = {
        'GUEST_FREE_USES': get_system_config('GUEST_FREE_USES'),
        'REGISTERED_FREE_USES': get_system_config('REGISTERED_FREE_USES'),
        'INVITE_VISIT_REWARD': get_system_config('INVITE_VISIT_REWARD'),
        'INVITE_REGISTER_REWARD': get_system_config('INVITE_REGISTER_REWARD'),
        'INVITE_REGISTER_BONUS': get_system_config('INVITE_REGISTER_BONUS'),
        'INVITE_MONTHLY_LIMIT': get_system_config('INVITE_MONTHLY_LIMIT'),
        'INVITE_IP_DAILY_LIMIT': get_system_config('INVITE_IP_DAILY_LIMIT'),
    }
    return configs


# ========== Prompt 管理 ==========

def get_prompt(key):
    db = get_db()
    row = db.execute('SELECT value FROM system_config WHERE key = ?', (key,)).fetchone()
    db.close()
    if row:
        return row['value']
    # fallback 到 llm/common/config.py 默认值
    defaults = {
        'SYSTEM_PROMPT': SYSTEM_PROMPT,
        'LIUYAO_PROMPT': LIUYAO_PROMPT,
    }
    return defaults.get(key)


def update_prompt(key, value):
    db = get_db()
    db.execute(
        'INSERT OR REPLACE INTO system_config (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
        (key, value)
    )
    db.commit()
    db.close()


def get_all_prompts():
    return {
        'SYSTEM_PROMPT': get_prompt('SYSTEM_PROMPT'),
        'LIUYAO_PROMPT': get_prompt('LIUYAO_PROMPT'),
    }


# ========== 反馈管理 ==========

def create_feedback(user_id, feedback, contact):
    db = get_db()
    db.execute(
        'INSERT INTO feedback (user_id, feedback, contact) VALUES (?, ?, ?)',
        (user_id, feedback, contact)
    )
    db.commit()
    db.close()


def get_all_feedback(page=1, per_page=20, status_filter=None):
    db = get_db()
    offset = (page - 1) * per_page

    if status_filter and status_filter != 'all':
        total = db.execute(
            'SELECT COUNT(*) as cnt FROM feedback WHERE status = ?',
            (status_filter,)
        ).fetchone()['cnt']
        rows = db.execute(
            'SELECT f.*, u.username FROM feedback f LEFT JOIN users u ON f.user_id = u.id WHERE f.status = ? ORDER BY f.id DESC LIMIT ? OFFSET ?',
            (status_filter, per_page, offset)
        ).fetchall()
    else:
        total = db.execute('SELECT COUNT(*) as cnt FROM feedback').fetchone()['cnt']
        rows = db.execute(
            'SELECT f.*, u.username FROM feedback f LEFT JOIN users u ON f.user_id = u.id ORDER BY f.id DESC LIMIT ? OFFSET ?',
            (per_page, offset)
        ).fetchall()

    db.close()
    feedbacks = [dict(row) for row in rows]
    return {
        'feedbacks': feedbacks,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }


def update_feedback_status(feedback_id, status):
    db = get_db()
    cursor = db.execute(
        'UPDATE feedback SET status = ? WHERE id = ?',
        (status, feedback_id)
    )
    db.commit()
    affected = cursor.rowcount
    db.close()
    return affected > 0


# ========== 日志查看 ==========

def get_usage_logs(page=1, per_page=20, username=None, date_from=None, date_to=None):
    """按 session_id 分组查询使用日志，每个会话只显示一行"""
    db = get_db()
    offset = (page - 1) * per_page

    conditions = []
    params = []

    if username:
        conditions.append('u.username LIKE ?')
        params.append(f'%{username}%')
    if date_from:
        conditions.append("date(l.created_at) >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date(l.created_at) <= ?")
        params.append(date_to)

    where_clause = ''
    if conditions:
        where_clause = 'WHERE ' + ' AND '.join(conditions)

    # 按 session_id 分组（NULL session_id 每条单独一行）
    total = db.execute(
        f'''SELECT COUNT(*) as cnt FROM (
            SELECT COALESCE(l.session_id, 'null_' || l.id) as grp
            FROM usage_log l LEFT JOIN users u ON l.user_id = u.id
            {where_clause}
            GROUP BY grp
        )''',
        params
    ).fetchone()['cnt']

    rows = db.execute(
        f'''SELECT
            MIN(l.id) as id,
            l.user_id,
            l.session_id,
            l.ip,
            u.username,
            MIN(l.created_at) as created_at,
            COUNT(*) as use_count,
            GROUP_CONCAT(l.action, ',') as actions
        FROM usage_log l
        LEFT JOIN users u ON l.user_id = u.id
        {where_clause}
        GROUP BY COALESCE(l.session_id, 'null_' || l.id)
        ORDER BY MAX(l.id) DESC
        LIMIT ? OFFSET ?''',
        params + [per_page, offset]
    ).fetchall()

    db.close()
    logs = [dict(row) for row in rows]
    return {
        'logs': logs,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }


def _rebuild_first_user_message(gua_xiang_info_str, category_str, background):
    """从 record 存储的卦象数据重建第一条发给 AI 的用户消息"""
    try:
        from liuyao_utils import orgnize_data
        gua_xiang_info = json.loads(gua_xiang_info_str) if gua_xiang_info_str else None
        category = json.loads(category_str) if category_str else None
        if not gua_xiang_info or not category:
            return None
        data = {
            'gua_xiang_info': gua_xiang_info,
            'background': background or '',
            'category': category
        }
        organized = orgnize_data(data)
        liuyao_prompt = get_prompt('LIUYAO_PROMPT')
        return liuyao_prompt.format(liuyao_data=organized)
    except Exception as e:
        print(f'重建首条消息失败: {e}')
        return None


def get_session_messages(session_id, dialog_manager=None):
    """通过 session_id 获取聊天记录，优先从 records 表查，再查内存"""
    # 1. 从 records 表查
    db = get_db()
    row = db.execute(
        'SELECT messages, title, category, date, user_id, gua_xiang_info, background FROM records WHERE session_id = ?',
        (session_id,)
    ).fetchone()
    # 查 usage_log 获取关联用户信息
    log_rows = db.execute(
        'SELECT l.*, u.username FROM usage_log l LEFT JOIN users u ON l.user_id = u.id WHERE l.session_id = ? ORDER BY l.id ASC',
        (session_id,)
    ).fetchall()
    db.close()

    logs = [dict(r) for r in log_rows] if log_rows else []

    if row and row['messages']:
        messages = json.loads(row['messages'])
        # 如果第一条消息是 assistant（缺少首条 user 消息），尝试重建
        if messages and messages[0].get('role') == 'assistant':
            first_msg = _rebuild_first_user_message(
                row['gua_xiang_info'], row['category'], row['background']
            )
            if first_msg:
                messages.insert(0, {'role': 'user', 'content': first_msg})
        return {
            'source': 'record',
            'messages': messages,
            'title': row['title'],
            'category': json.loads(row['category']) if row['category'] else None,
            'date': row['date'],
            'user_id': row['user_id'],
            'logs': logs
        }

    # 2. 从 conversations 表查（自动持久化的对话归档）
    db2 = get_db()
    conv_row = db2.execute(
        'SELECT messages, gua_xiang_info, category, background, user_id, created_at FROM conversations WHERE session_id = ?',
        (session_id,)
    ).fetchone()
    db2.close()

    if conv_row and conv_row['messages']:
        messages = json.loads(conv_row['messages'])
        category = json.loads(conv_row['category']) if conv_row['category'] else None
        # 如果第一条消息是 assistant（缺少首条 user 消息），尝试重建
        if messages and messages[0].get('role') == 'assistant':
            first_msg = _rebuild_first_user_message(
                conv_row['gua_xiang_info'], conv_row['category'], conv_row['background']
            )
            if first_msg:
                messages.insert(0, {'role': 'user', 'content': first_msg})
        return {
            'source': 'conversation',
            'messages': messages,
            'title': None,
            'category': category,
            'date': conv_row['created_at'],
            'user_id': conv_row['user_id'],
            'logs': logs
        }

    # 3. 从 dialog_manager 内存查
    if dialog_manager and session_id in dialog_manager._conversation_dict:
        conversation, _ = dialog_manager._conversation_dict[session_id]
        messages = []
        for msg in conversation.messages:
            if msg.role == 'system':
                continue
            messages.append({'role': msg.role, 'content': msg.content})
        return {
            'source': 'memory',
            'messages': messages,
            'title': None,
            'category': None,
            'date': None,
            'user_id': None,
            'logs': logs
        }

    # 4. 仅有日志记录但没有聊天记录
    if logs:
        return {
            'source': 'logs_only',
            'messages': [],
            'title': None,
            'category': None,
            'date': None,
            'user_id': logs[0].get('user_id'),
            'logs': logs
        }

    return None
