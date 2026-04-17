"""将指定用户提升为管理员

用法: python make_admin.py <用户名>
"""
import sys
from auth import get_db

def make_admin(username):
    db = get_db()
    user = db.execute('SELECT id, username, role FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        print(f'错误: 用户 "{username}" 不存在')
        db.close()
        return False
    if user['role'] == 'admin':
        print(f'用户 "{username}" 已经是管理员')
        db.close()
        return True
    db.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user['id'],))
    db.commit()
    db.close()
    print(f'成功: 用户 "{username}" 已被提升为管理员')
    return True

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('用法: python make_admin.py <用户名>')
        sys.exit(1)
    success = make_admin(sys.argv[1])
    sys.exit(0 if success else 1)
