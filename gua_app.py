import sys
import os
import time
import threading
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()  # 最早加载 .env，确保后续 import 能读到环境变量
from utils import send_email, send_reset_email
import json
from datetime import datetime
import uuid
from liuyao_utils import orgnize_data
from dialog_manager import DialogManager
from captcha_utils import generate_captcha, validate_captcha

ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from llm.common.config import LIUYAO_PROMPT
from auth import (init_db, register_user, login_user, get_user_info, check_credit, use_credit, log_usage, require_auth, optional_auth, require_admin,
                  get_user_records, get_user_record_by_id, create_user_record, update_user_record, delete_user_record,
                  change_password, change_email, create_reset_token, validate_reset_token, reset_password_with_token,
                  save_conversation)
from config import GUEST_FREE_USES
from rate_limiter import limiter, get_client_ip
import admin_service

app = Flask(__name__, static_folder=None)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(32).hex())

# CORS：生产环境同源无需配置，开发环境允许 Vite dev server
CORS(app, resources={r"/api/*": {"origins": os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')}})

dialog_manager = DialogManager()

# 启动时初始化数据库
init_db()


# 异步任务存储（用于微信等 WebView 的轮询模式）
_async_tasks = {}
_async_tasks_lock = threading.Lock()


def _cleanup_old_tasks():
    """清理超过 10 分钟的旧任务，防止内存泄漏"""
    now = time.time()
    with _async_tasks_lock:
        expired = [tid for tid, t in _async_tasks.items() if now - t.get('created_at', 0) > 600]
        for tid in expired:
            del _async_tasks[tid]


LLM_LOG_DIR = os.path.dirname(__file__)


def _extract_messages_json(session_id):
    """从 dialog_manager 内存中提取非 system 消息，返回 JSON 字符串"""
    if session_id not in dialog_manager._conversation_dict:
        return None
    conversation, _ = dialog_manager._conversation_dict[session_id]
    messages = []
    for msg in conversation.messages:
        if msg.role == 'system':
            continue
        messages.append({'role': msg.role, 'content': msg.content})
    return json.dumps(messages, ensure_ascii=False)


def log_llm(session_id, direction, text):
    """追加记录 LLM 交互日志，按日期分文件"""
    try:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        log_path = os.path.join(LLM_LOG_DIR, f"llm_log_{now.strftime('%Y-%m-%d')}.txt")
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{timestamp}] session={session_id} {direction}\n")
            f.write(f"{'='*60}\n")
            f.write(text)
            f.write('\n')
    except Exception as e:
        print(f"写入LLM日志失败: {e}")


def cut_message(message):
    message = message.split("以上内容由AI生成")[0].strip()
    lines = message.rstrip().split('\n')
    # 去掉末尾10行中包含 deepseek 的行（不区分大小写）
    tail_count = min(10, len(lines))
    tail_start = len(lines) - tail_count
    lines = lines[:tail_start] + [line for line in lines[tail_start:] if 'deepseek' not in line.lower()]
    # 去掉可能残留的分隔线
    while lines and lines[-1].strip() in ('---', '***', '___', ''):
        lines.pop()
    return '\n'.join(lines).strip()


# ========== 认证接口 ==========

@app.route('/api/captcha', methods=['GET'])
def api_captcha():
    ip = get_client_ip(request)
    if not limiter.is_allowed(f"captcha:{ip}", 30, 600):
        return jsonify({"error": "请求过于频繁，请稍后再试"}), 429
    captcha_id, image = generate_captcha()
    return jsonify({"captcha_id": captcha_id, "image": image})


@app.route('/api/auth/register', methods=['POST'])
def api_register():
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400
    data = request.get_json()
    if not data.get('agreed'):
        return jsonify({"error": "请先同意《用户协议与隐私政策》"}), 400
    if not validate_captcha(data.get('captcha_id', ''), data.get('captcha_text', '')):
        return jsonify({"error": "验证码错误或已过期"}), 400
    terms_version = admin_service.get_system_config('terms_privacy_version') or '1.0'
    agreed_ip = get_client_ip(request)
    agreed_at = datetime.utcnow()
    result, error = register_user(
        data.get('username', ''),
        data.get('password', ''),
        data.get('email', ''),
        agreed_version=terms_version,
        agreed_at=agreed_at,
        agreed_ip=agreed_ip,
    )
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"status": "success", **result})


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    ip = get_client_ip(request)
    if not limiter.is_allowed(f"login:{ip}", 10, 600):
        return jsonify({"error": "请求过于频繁，请稍后再试"}), 429
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400
    data = request.get_json()
    result, error = login_user(data.get('username', ''), data.get('password', ''), ip=ip)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"status": "success", **result})


@app.route('/api/auth/me', methods=['GET'])
@require_auth
def api_me():
    user = get_user_info(g.user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify({"status": "success", "user": user})


@app.route('/api/auth/change-password', methods=['PUT'])
@require_auth
def api_change_password():
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400
    data = request.get_json()
    success, error = change_password(g.user_id, data.get('old_password', ''), data.get('new_password', ''))
    if not success:
        return jsonify({"error": error}), 400
    return jsonify({"status": "success", "message": "密码修改成功"})


@app.route('/api/auth/change-email', methods=['PUT'])
@require_auth
def api_change_email():
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400
    data = request.get_json()
    success, error = change_email(g.user_id, data.get('email', ''))
    if not success:
        return jsonify({"error": error}), 400
    user = get_user_info(g.user_id)
    return jsonify({"status": "success", "message": "邮箱修改成功", "user": user})


@app.route('/api/config/quota', methods=['GET'])
def api_quota():
    guest_uses = admin_service.get_system_config('GUEST_FREE_USES')
    return jsonify({"guest_free_uses": int(guest_uses) if guest_uses else GUEST_FREE_USES})


# ========== 记录接口 ==========

@app.route('/api/records', methods=['GET'])
@require_auth
def api_get_records():
    records = get_user_records(g.user_id)
    return jsonify({"status": "success", "records": records})


@app.route('/api/records', methods=['POST'])
@require_auth
def api_create_record():
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400
    data = request.get_json()
    record = create_user_record(g.user_id, data)
    return jsonify({"status": "success", "record": record})


@app.route('/api/records/<record_id>', methods=['PUT'])
@require_auth
def api_update_record(record_id):
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400
    data = request.get_json()
    success = update_user_record(record_id, g.user_id, data)
    if not success:
        return jsonify({"error": "记录不存在或无权修改"}), 404
    return jsonify({"status": "success"})


@app.route('/api/records/<record_id>', methods=['DELETE'])
@require_auth
def api_delete_record(record_id):
    success = delete_user_record(record_id, g.user_id)
    if not success:
        return jsonify({"error": "记录不存在或无权删除"}), 404
    return jsonify({"status": "success"})


# ========== 业务接口 ==========

@app.route('/api/receive', methods=['POST'])
@optional_auth
def receive_data():
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400

    # 游客 IP 限流：5次/小时（登录用户已有额度控制，不限流）
    if not g.user_id:
        ip = get_client_ip(request)
        if not limiter.is_allowed(f"receive:{ip}", 5, 3600):
            return jsonify({"error": "请求过于频繁，请稍后再试"}), 429

    # 已登录用户：先检查额度（不扣减）
    if g.user_id and not check_credit(g.user_id):
        return jsonify({"error": "no_credit", "message": "额度已用完"}), 403

    session_id = str(uuid.uuid4())[:16]
    print(f"当前会话ID: {session_id}")

    lang = request.headers.get('X-Lang', 'zh-CN')
    data = request.get_json()
    orgnized_data = orgnize_data(data)
    liuyao_prompt = admin_service.get_prompt('LIUYAO_PROMPT')
    message = liuyao_prompt.format(liuyao_data=orgnized_data)
    log_llm(session_id, '发送', message)
    response, llm_success = dialog_manager.process_user_message(session_id, message, lang=lang)
    log_llm(session_id, '接收', response)
    cut_response = cut_message(response)
    print(cut_response)

    # LLM 成功后才扣减额度 / 记录日志 / 保存对话
    remaining_uses = None
    if llm_success:
        if g.user_id:
            _, remaining = use_credit(g.user_id, 'receive', session_id)
            remaining_uses = remaining
        else:
            log_usage('receive', session_id)

        # 自动持久化对话到 conversations 表
        messages_json = _extract_messages_json(session_id)
        if messages_json:
            save_conversation(
                session_id=session_id,
                user_id=g.user_id,
                messages_json=messages_json,
                gua_xiang_info=json.dumps(data.get('gua_xiang_info'), ensure_ascii=False) if data.get('gua_xiang_info') else None,
                category=json.dumps(data.get('category'), ensure_ascii=False) if data.get('category') else None,
                background=data.get('background', '')
            )

    result = {
        "status": "success",
        "message": cut_response,
        "session_id": session_id
    }
    if remaining_uses is not None:
        result["remaining_uses"] = remaining_uses
    return jsonify(result)


@app.route('/api/receive/async', methods=['POST'])
@optional_auth
def receive_data_async():
    """异步版本的 /api/receive，立即返回 task_id，后台线程处理 LLM 请求。
    用于微信等 WebView 环境，避免长请求被系统强制断开。"""
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400

    if not g.user_id:
        ip = get_client_ip(request)
        if not limiter.is_allowed(f"receive:{ip}", 5, 3600):
            return jsonify({"error": "请求过于频繁，请稍后再试"}), 429

    if g.user_id and not check_credit(g.user_id):
        return jsonify({"error": "no_credit", "message": "额度已用完"}), 403

    # 提取请求上下文（后台线程无法访问 Flask request/g）
    user_id = g.user_id
    data = request.get_json()
    lang = request.headers.get('X-Lang', 'zh-CN')

    task_id = str(uuid.uuid4())[:16]
    with _async_tasks_lock:
        _async_tasks[task_id] = {'status': 'processing', 'created_at': time.time()}

    _cleanup_old_tasks()

    def process():
        try:
            session_id = str(uuid.uuid4())[:16]
            orgnized_data = orgnize_data(data)
            liuyao_prompt = admin_service.get_prompt('LIUYAO_PROMPT')
            message = liuyao_prompt.format(liuyao_data=orgnized_data)
            log_llm(session_id, '发送', message)
            response, llm_success = dialog_manager.process_user_message(session_id, message, lang=lang)
            log_llm(session_id, '接收', response)
            cut_response = cut_message(response)

            remaining_uses = None
            if llm_success:
                if user_id:
                    _, remaining = use_credit(user_id, 'receive', session_id)
                    remaining_uses = remaining
                else:
                    log_usage('receive', session_id)

                messages_json = _extract_messages_json(session_id)
                if messages_json:
                    save_conversation(
                        session_id=session_id,
                        user_id=user_id,
                        messages_json=messages_json,
                        gua_xiang_info=json.dumps(data.get('gua_xiang_info'), ensure_ascii=False) if data.get('gua_xiang_info') else None,
                        category=json.dumps(data.get('category'), ensure_ascii=False) if data.get('category') else None,
                        background=data.get('background', '')
                    )

            result = {
                "status": "success",
                "message": cut_response,
                "session_id": session_id
            }
            if remaining_uses is not None:
                result["remaining_uses"] = remaining_uses

            with _async_tasks_lock:
                _async_tasks[task_id] = {'status': 'done', 'result': result, 'created_at': time.time()}
        except Exception as e:
            print(f"异步任务处理失败: {e}")
            with _async_tasks_lock:
                _async_tasks[task_id] = {'status': 'error', 'error': str(e), 'created_at': time.time()}

    threading.Thread(target=process, daemon=True).start()
    return jsonify({"status": "success", "task_id": task_id})


@app.route('/api/chat/async', methods=['POST'])
@optional_auth
def chat_async():
    """异步版本的 /api/chat"""
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400

    if not g.user_id:
        ip = get_client_ip(request)
        if not limiter.is_allowed(f"chat:{ip}", 10, 3600):
            return jsonify({"error": "请求过于频繁，请稍后再试"}), 429

    user_id = g.user_id
    data = request.get_json()
    session_id = data.get('session_id', '')
    message = data.get('message', '')
    lang = request.headers.get('X-Lang', 'zh-CN')

    if g.user_id and not check_credit(g.user_id):
        return jsonify({"error": "no_credit", "message": "额度已用完"}), 403

    task_id = str(uuid.uuid4())[:16]
    with _async_tasks_lock:
        _async_tasks[task_id] = {'status': 'processing', 'created_at': time.time()}

    _cleanup_old_tasks()

    def process():
        try:
            log_llm(session_id, '发送', message)
            response, llm_success = dialog_manager.process_user_message(session_id, message, lang=lang)
            log_llm(session_id, '接收', response)
            cut_response = cut_message(response)

            remaining_uses = None
            if llm_success:
                if user_id:
                    _, remaining = use_credit(user_id, 'chat', session_id)
                    remaining_uses = remaining
                else:
                    log_usage('chat', session_id)

                messages_json = _extract_messages_json(session_id)
                if messages_json:
                    save_conversation(session_id=session_id, user_id=user_id, messages_json=messages_json)

            result = {"status": "success", "message": cut_response}
            if remaining_uses is not None:
                result["remaining_uses"] = remaining_uses

            with _async_tasks_lock:
                _async_tasks[task_id] = {'status': 'done', 'result': result, 'created_at': time.time()}
        except Exception as e:
            print(f"异步聊天任务处理失败: {e}")
            with _async_tasks_lock:
                _async_tasks[task_id] = {'status': 'error', 'error': str(e), 'created_at': time.time()}

    threading.Thread(target=process, daemon=True).start()
    return jsonify({"status": "success", "task_id": task_id})


@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_result(task_id):
    """轮询查询异步任务结果"""
    with _async_tasks_lock:
        task = _async_tasks.get(task_id)
    if not task:
        return jsonify({"error": "任务不存在或已过期"}), 404
    if task['status'] == 'processing':
        return jsonify({"status": "processing"})
    # 返回结果并清理
    with _async_tasks_lock:
        _async_tasks.pop(task_id, None)
    if task['status'] == 'error':
        return jsonify({"status": "error", "message": "处理失败，请重试"}), 500
    return jsonify(task['result'])


@app.route('/api/chat', methods=['POST'])
@optional_auth
def chat():
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400

    # 游客 IP 限流：10次/小时
    if not g.user_id:
        ip = get_client_ip(request)
        if not limiter.is_allowed(f"chat:{ip}", 10, 3600):
            return jsonify({"error": "请求过于频繁，请稍后再试"}), 429

    data = request.get_json()
    session_id = data.get('session_id', '')
    message = data.get('message', '')
    lang = request.headers.get('X-Lang', 'zh-CN')

    # 已登录用户：先检查额度（不扣减）
    if g.user_id and not check_credit(g.user_id):
        return jsonify({"error": "no_credit", "message": "额度已用完"}), 403

    print(f"当前会话ID: {session_id}")

    log_llm(session_id, '发送', message)
    response, llm_success = dialog_manager.process_user_message(session_id, message, lang=lang)
    log_llm(session_id, '接收', response)
    cut_response = cut_message(response)
    print(cut_response)

    # LLM 成功后才扣减额度 / 记录日志 / 更新对话
    remaining_uses = None
    if llm_success:
        if g.user_id:
            _, remaining = use_credit(g.user_id, 'chat', session_id)
            remaining_uses = remaining
        else:
            log_usage('chat', session_id)

        # 自动更新对话到 conversations 表
        messages_json = _extract_messages_json(session_id)
        if messages_json:
            save_conversation(
                session_id=session_id,
                user_id=g.user_id,
                messages_json=messages_json
            )

    result = {
        "status": "success",
        "message": cut_response,
    }
    if remaining_uses is not None:
        result["remaining_uses"] = remaining_uses
    return jsonify(result)


@app.route('/api/chat/restore', methods=['POST'])
@optional_auth
def chat_restore():
    ip = get_client_ip(request)
    if not limiter.is_allowed(f"restore:{ip}", 20, 3600):
        return jsonify({"error": "请求过于频繁，请稍后再试"}), 429
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400

    data = request.get_json()
    session_id = data.get('session_id', '')
    messages = data.get('messages', [])
    lang = request.headers.get('X-Lang', 'zh-CN')

    # 输入校验：messages 必须是列表，最多 100 条
    if not isinstance(messages, list):
        return jsonify({"error": "messages 格式不正确"}), 400
    if len(messages) > 100:
        return jsonify({"error": "消息记录过多，最多支持100条"}), 400
    for msg in messages:
        if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
            return jsonify({"error": "消息格式不正确"}), 400

    new_session_id = dialog_manager.restore_conversation(session_id, messages, lang=lang)
    return jsonify({
        "status": "success",
        "session_id": new_session_id
    })


@app.route('/api/feedback', methods=['POST'])
@optional_auth
def feedback():
    ip = get_client_ip(request)
    if not limiter.is_allowed(f"feedback:{ip}", 5, 3600):
        return jsonify({"error": "请求过于频繁，请稍后再试"}), 429
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400

    data = request.get_json()

    try:
        feedback_content = data.get('feedback', '')
        contact_info = data.get('contact', '未提供')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 保存到数据库
        admin_service.create_feedback(g.user_id, feedback_content, contact_info)

        email_subject = f"六爻Web应用反馈 - {timestamp}"
        email_body = f"""
收到新的用户反馈(Web端):

时间: {timestamp}
联系方式: {contact_info}
反馈内容:
{feedback_content}
        """
        send_email(email_subject, email_body)
    except Exception as e:
        print(f"处理反馈时出错: {str(e)}")

    return jsonify({
        "status": "success",
        "message": "反馈已收到"
    })


# ========== 密码重置接口 ==========

@app.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    ip = get_client_ip(request)
    if not limiter.is_allowed(f"forgot:{ip}", 3, 3600):
        return jsonify({"error": "请求过于频繁，请稍后再试"}), 429
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400
    data = request.get_json()
    email = data.get('email', '').strip()
    if not email:
        return jsonify({"error": "请输入邮箱地址"}), 400
    # 无论邮箱是否存在都返回成功（防枚举）
    token, user = create_reset_token(email)
    if token and user:
        reset_url = f"{request.host_url}reset-password?token={token}"
        send_reset_email(email, reset_url)
    return jsonify({"status": "success", "message": "如果该邮箱已注册，重置邮件已发送"})


@app.route('/api/auth/verify-reset-token/<token>', methods=['GET'])
def api_verify_reset_token(token):
    user_id = validate_reset_token(token)
    if not user_id:
        return jsonify({"error": "重置链接无效或已过期"}), 400
    return jsonify({"status": "success"})


@app.route('/api/auth/reset-password', methods=['POST'])
def api_reset_password():
    if not request.is_json:
        return jsonify({"error": "请求必须是 JSON 格式"}), 400
    data = request.get_json()
    token = data.get('token', '')
    password = data.get('password', '')
    success, error = reset_password_with_token(token, password)
    if not success:
        return jsonify({"error": error}), 400
    return jsonify({"status": "success", "message": "密码重置成功"})


# ========== 管理接口 ==========

@app.route('/api/admin/dashboard', methods=['GET'])
@require_auth
@require_admin
def admin_dashboard():
    stats = admin_service.get_dashboard_stats(dialog_manager)
    return jsonify({"status": "success", **stats})


@app.route('/api/admin/users', methods=['GET'])
@require_auth
@require_admin
def admin_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('search', None)
    result = admin_service.get_all_users(page, per_page, search)
    return jsonify({"status": "success", **result})


@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
@require_auth
@require_admin
def admin_user_detail(user_id):
    user = admin_service.get_user_detail(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify({"status": "success", "user": user})


@app.route('/api/admin/users/<int:user_id>/quota', methods=['PUT'])
@require_auth
@require_admin
def admin_update_quota(user_id):
    data = request.get_json()
    free_uses = data.get('free_uses')
    if free_uses is None:
        return jsonify({"error": "请提供 free_uses 参数"}), 400
    admin_service.update_user_quota(user_id, int(free_uses))
    return jsonify({"status": "success"})


@app.route('/api/admin/users/<int:user_id>/ban', methods=['PUT'])
@require_auth
@require_admin
def admin_ban_user(user_id):
    success, error = admin_service.ban_user(user_id)
    if not success:
        return jsonify({"error": error}), 400
    return jsonify({"status": "success"})


@app.route('/api/admin/users/<int:user_id>/unban', methods=['PUT'])
@require_auth
@require_admin
def admin_unban_user(user_id):
    admin_service.unban_user(user_id)
    return jsonify({"status": "success"})


@app.route('/api/admin/config', methods=['GET'])
@require_auth
@require_admin
def admin_get_config():
    configs = admin_service.get_all_configs()
    return jsonify({"status": "success", "configs": configs})


@app.route('/api/admin/config', methods=['PUT'])
@require_auth
@require_admin
def admin_update_config():
    data = request.get_json()
    for key, value in data.items():
        admin_service.update_system_config(key, str(value))
    return jsonify({"status": "success"})


@app.route('/api/admin/prompts', methods=['GET'])
@require_auth
@require_admin
def admin_get_prompts():
    prompts = admin_service.get_all_prompts()
    return jsonify({"status": "success", "prompts": prompts})


@app.route('/api/admin/prompts', methods=['PUT'])
@require_auth
@require_admin
def admin_update_prompts():
    data = request.get_json()
    for key, value in data.items():
        admin_service.update_prompt(key, value)
    return jsonify({"status": "success"})


@app.route('/api/admin/feedback', methods=['GET'])
@require_auth
@require_admin
def admin_get_feedback():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status', None)
    result = admin_service.get_all_feedback(page, per_page, status)
    return jsonify({"status": "success", **result})


@app.route('/api/admin/feedback/<int:feedback_id>', methods=['PUT'])
@require_auth
@require_admin
def admin_update_feedback(feedback_id):
    data = request.get_json()
    status = data.get('status')
    if not status:
        return jsonify({"error": "请提供 status 参数"}), 400
    success = admin_service.update_feedback_status(feedback_id, status)
    if not success:
        return jsonify({"error": "反馈不存在"}), 404
    return jsonify({"status": "success"})


@app.route('/api/admin/logs', methods=['GET'])
@require_auth
@require_admin
def admin_get_logs():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    username = request.args.get('username', None)
    date_from = request.args.get('date_from', None)
    date_to = request.args.get('date_to', None)
    result = admin_service.get_usage_logs(page, per_page, username, date_from, date_to)
    return jsonify({"status": "success", **result})


@app.route('/api/admin/logs/session/<session_id>', methods=['GET'])
@require_auth
@require_admin
def admin_session_detail(session_id):
    result = admin_service.get_session_messages(session_id, dialog_manager)
    if not result:
        return jsonify({"error": "未找到该会话记录"}), 404
    return jsonify({"status": "success", **result})


@app.route('/api/admin/users/<int:user_id>/reset-password', methods=['PUT'])
@require_auth
@require_admin
def admin_reset_password(user_id):
    data = request.get_json()
    password = data.get('password', '')
    success, error = admin_service.admin_reset_password(user_id, password)
    if not success:
        return jsonify({"error": error}), 400
    return jsonify({"status": "success", "message": "密码已重置"})


@app.route('/api/active_users', methods=['GET'])
def get_active_users():
    return str(dialog_manager.get_current_active_user_number())


STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')


# SPA fallback
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    static_file = os.path.join(STATIC_DIR, path)
    if path and os.path.isfile(static_file):
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, 'index.html')


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    cert_file = os.path.join(ROOT_DIR, 'certs', 'cert.pem')
    key_file = os.path.join(ROOT_DIR, 'certs', 'key.pem')
    ssl_ctx = None
    if os.path.isfile(cert_file) and os.path.isfile(key_file):
        ssl_ctx = (cert_file, key_file)
        print(f' * HTTPS enabled: https://0.0.0.0:9001')
    app.run(debug=debug, host='0.0.0.0', port=9001, ssl_context=ssl_ctx)
