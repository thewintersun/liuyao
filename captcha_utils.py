import string
import random
import time
import uuid
import base64
from io import BytesIO
from captcha.image import ImageCaptcha
from config import (CAPTCHA_LENGTH, CAPTCHA_EXPIRY_SECONDS,
                     CAPTCHA_IMAGE_WIDTH, CAPTCHA_IMAGE_HEIGHT)

# 排除易混淆字符 0/O/1/I/l
CHARS = ''.join(c for c in string.ascii_uppercase + string.digits if c not in 'OI01')

# 内存存储: {captcha_id: (answer, expiry_timestamp)}
_store = {}


def _cleanup():
    """惰性清理过期条目"""
    now = time.time()
    expired = [k for k, (_, exp) in _store.items() if now > exp]
    for k in expired:
        del _store[k]


def generate_captcha():
    """生成验证码，返回 (captcha_id, base64_image)"""
    _cleanup()
    text = ''.join(random.choices(CHARS, k=CAPTCHA_LENGTH))
    captcha_id = uuid.uuid4().hex[:16]

    image_captcha = ImageCaptcha(width=CAPTCHA_IMAGE_WIDTH, height=CAPTCHA_IMAGE_HEIGHT)
    img = image_captcha.generate_image(text)

    buf = BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')

    _store[captcha_id] = (text.upper(), time.time() + CAPTCHA_EXPIRY_SECONDS)
    return captcha_id, f'data:image/png;base64,{b64}'


def validate_captcha(captcha_id, text):
    """校验验证码，一次性消耗。返回 True/False"""
    _cleanup()
    if not captcha_id or not text:
        return False
    entry = _store.pop(captcha_id, None)
    if entry is None:
        return False
    answer, expiry = entry
    if time.time() > expiry:
        return False
    return text.strip().upper() == answer
