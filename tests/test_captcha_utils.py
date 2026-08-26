import time
import pytest
from captcha_utils import generate_captcha, validate_captcha, _store


@pytest.fixture(autouse=True)
def clear_store():
    _store.clear()
    yield
    _store.clear()


class TestGenerateCaptcha:
    def test_returns_id_and_image(self):
        captcha_id, image = generate_captcha()
        assert isinstance(captcha_id, str)
        assert len(captcha_id) == 16
        assert image.startswith('data:image/png;base64,')

    def test_unique_ids(self):
        id1, _ = generate_captcha()
        id2, _ = generate_captcha()
        assert id1 != id2


class TestValidateCaptcha:
    def test_correct_answer(self):
        _store['tid'] = ('ABCD', time.time() + 300)
        assert validate_captcha('tid', 'ABCD') is True

    def test_case_insensitive(self):
        _store['tid'] = ('ABCD', time.time() + 300)
        assert validate_captcha('tid', 'abcd') is True

    def test_consumed_after_use(self):
        _store['tid'] = ('ABCD', time.time() + 300)
        validate_captcha('tid', 'ABCD')
        assert validate_captcha('tid', 'ABCD') is False

    def test_wrong_answer(self):
        _store['tid'] = ('ABCD', time.time() + 300)
        assert validate_captcha('tid', 'WRONG') is False

    def test_expired(self):
        _store['tid'] = ('ABCD', 0)  # 已过期
        assert validate_captcha('tid', 'ABCD') is False

    def test_empty_input(self):
        assert validate_captcha(None, 'ABC') is False
        assert validate_captcha('id', None) is False
        assert validate_captcha('', '') is False

    def test_nonexistent_id(self):
        assert validate_captcha('no_such_id', 'ABCD') is False
