import pytest
from unittest.mock import patch

from llm.common.base import Conversation
from llm.common.factory import LLMFactory
from llm.deepseek.client import DeepseekClient
from llm.glm.client import GLMClient


def _fake_response(content, finish_reason='stop'):
    return {
        'choices': [{'message': {'content': content}, 'finish_reason': finish_reason}],
        'usage': {'completion_tokens': 100},
    }


class TestFactory:
    def test_creates_deepseek(self):
        client = LLMFactory.create('deepseek', api_key='k')
        assert isinstance(client, DeepseekClient)

    def test_creates_glm(self):
        client = LLMFactory.create('glm', api_key='k')
        assert isinstance(client, GLMClient)

    def test_unknown_provider(self):
        with pytest.raises(ValueError):
            LLMFactory.create('nope')


class TestClientConfig:
    def test_deepseek_defaults(self):
        c = DeepseekClient(api_key='dk')
        assert c.api_base == 'https://api.deepseek.com'
        assert c.model == 'deepseek-v4-flash'
        assert c.extra_params == {}

    def test_glm_defaults_to_coding_endpoint(self):
        c = GLMClient(api_key='gk')
        assert c.api_base.endswith('/api/coding/paas/v4')
        assert c.model.startswith('glm-')

    def test_glm_thinking_enabled(self):
        c = GLMClient(api_key='gk', thinking=True)
        assert c.extra_params['thinking'] == {'type': 'enabled'}

    def test_glm_thinking_disabled(self):
        c = GLMClient(api_key='gk', thinking=False)
        assert c.extra_params['thinking'] == {'type': 'disabled'}

    def test_missing_key_rejected(self):
        with pytest.raises(ValueError):
            GLMClient(api_key='', api_base='x', model='y')


class TestNoGlobalStateLeak:
    """两个供应商并存时不能互相覆盖 openai 的全局配置"""

    def test_credentials_passed_per_call(self):
        ds = DeepseekClient(api_key='ds-key', api_base='https://api.deepseek.com')
        glm = GLMClient(api_key='glm-key', api_base='https://open.bigmodel.cn/api/coding/paas/v4')

        seen = []
        with patch('openai.ChatCompletion.create', side_effect=lambda **kw: (seen.append(kw), _fake_response('答'))[1]):
            ds.chat_sync(Conversation('sys'), '问题')
            glm.chat_sync(Conversation('sys'), '问题')

        assert seen[0]['api_key'] == 'ds-key'
        assert seen[0]['api_base'] == 'https://api.deepseek.com'
        assert 'thinking' not in seen[0]

        assert seen[1]['api_key'] == 'glm-key'
        assert seen[1]['api_base'].endswith('/api/coding/paas/v4')
        assert seen[1]['thinking'] == {'type': 'enabled'}

    def test_openai_module_globals_untouched(self):
        import openai
        before = (openai.api_key, openai.api_base)
        DeepseekClient(api_key='ds-key')
        GLMClient(api_key='glm-key')
        assert (openai.api_key, openai.api_base) == before


class TestEmptyResponseHandling:
    """空回复必须抛异常，供上层重试且不扣额度——两家供应商行为一致"""

    @pytest.mark.parametrize('client_factory', [
        lambda: DeepseekClient(api_key='k'),
        lambda: GLMClient(api_key='k'),
    ])
    def test_empty_content_raises(self, client_factory):
        client = client_factory()
        with patch('openai.ChatCompletion.create', return_value=_fake_response('', 'length')):
            with pytest.raises(ValueError, match='空回复'):
                client.chat_sync(Conversation('sys'), '问题')

    @pytest.mark.parametrize('client_factory', [
        lambda: DeepseekClient(api_key='k'),
        lambda: GLMClient(api_key='k'),
    ])
    def test_whitespace_only_raises(self, client_factory):
        client = client_factory()
        with patch('openai.ChatCompletion.create', return_value=_fake_response('   \n  ')):
            with pytest.raises(ValueError, match='空回复'):
                client.chat_sync(Conversation('sys'), '问题')

    def test_truncated_but_non_empty_is_kept(self):
        client = DeepseekClient(api_key='k')
        conv = Conversation('sys')
        with patch('openai.ChatCompletion.create', return_value=_fake_response('部分正文', 'length')):
            assert client.chat_sync(conv, '问题') == '部分正文'
        assert [m.role for m in conv.messages] == ['system', 'user', 'assistant']

    def test_malformed_response_raises(self):
        client = DeepseekClient(api_key='k')
        with patch('openai.ChatCompletion.create', return_value={'choices': []}):
            with pytest.raises(ValueError):
                client.chat_sync(Conversation('sys'), '问题')
