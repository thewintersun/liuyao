import pytest
from unittest.mock import patch, MagicMock
from llm.common.base import Conversation
from dialog_manager import DialogManager


@pytest.fixture
def dm():
    """创建 DialogManager，注入 mock 客户端并 mock 掉 admin_service"""
    with patch('dialog_manager.admin_service') as mock_admin:
        mock_admin.get_prompt.return_value = '你是测试助手'
        mock_admin.get_system_config.return_value = None
        manager = DialogManager()
        manager.llm_client = MagicMock()
        yield manager


class TestEstimateTokens:
    def test_ascii(self):
        assert DialogManager._estimate_tokens('hello') == int(5 * 0.3)

    def test_chinese(self):
        assert DialogManager._estimate_tokens('你好') == int(2 * 0.6)

    def test_empty(self):
        assert DialogManager._estimate_tokens('') == 0


class TestTrimConversation:
    def test_short_no_trim(self, dm):
        conv = Conversation('system')
        conv.add_user_message('q1')
        conv.add_assistant_message('a1')
        result = dm._trim_conversation_history(conv)
        non_sys = [m for m in result.messages if m.role != 'system']
        assert len(non_sys) == 2

    def test_exceeding_rounds_trimmed(self, dm):
        conv = Conversation('system')
        conv.add_user_message('first_q')
        conv.add_assistant_message('first_a')
        for i in range(15):
            conv.add_user_message(f'q{i}')
            conv.add_assistant_message(f'a{i}')
        result = dm._trim_conversation_history(conv)
        non_sys = [m for m in result.messages if m.role != 'system']
        assert len(non_sys) <= 2 + dm.MAX_RECENT_ROUNDS * 2
        # 首轮保留
        assert non_sys[0].content == 'first_q'


class TestProcessUserMessage:
    def test_success(self, dm):
        dm.llm_client.chat_sync.return_value = '回答'
        response, success = dm.process_user_message('c1', '你好')
        assert success is True
        assert response == '回答'

    def test_failure(self, dm):
        dm.llm_client.chat_sync.side_effect = Exception('network error')
        response, success = dm.process_user_message('c2', '你好')
        assert success is False
        assert '不可用' in response

    def test_context_length_retry_success(self, dm):
        dm.llm_client.chat_sync.side_effect = [
            Exception('context_length_exceeded'),
            '重试成功'
        ]
        response, success = dm.process_user_message('c3', '你好')
        assert success is True
        assert response == '重试成功'

    def test_context_length_retry_fail(self, dm):
        dm.llm_client.chat_sync.side_effect = Exception('context_length_exceeded')
        response, success = dm.process_user_message('c4', '你好')
        assert success is False
        assert '上下文过长' in response


class TestConversationManagement:
    def test_creates_new(self, dm):
        conv = dm.get_conversation('new_id')
        assert conv is not None

    def test_reuses_existing(self, dm):
        conv1 = dm.get_conversation('same')
        conv1.add_user_message('test')
        conv2 = dm.get_conversation('same')
        assert any(m.content == 'test' for m in conv2.messages)

    def test_eviction(self, dm):
        dm._max_conversations = 3
        dm.get_conversation('a')
        dm.get_conversation('b')
        dm.get_conversation('c')
        dm.get_conversation('d')
        assert 'a' not in dm._conversation_dict
        assert 'd' in dm._conversation_dict


class TestProviderSwitch:
    """供应商切换：管理后台配置优先，非法值回退到默认"""

    def _provider_with_config(self, configured):
        with patch('dialog_manager.admin_service') as mock_admin:
            mock_admin.get_system_config.return_value = configured
            return DialogManager.get_provider()

    def test_default_when_unset(self):
        assert self._provider_with_config(None) == 'deepseek'

    def test_switch_to_glm(self):
        assert self._provider_with_config('glm') == 'glm'

    def test_case_and_space_tolerant(self):
        assert self._provider_with_config('  GLM ') == 'glm'

    def test_unknown_falls_back(self):
        assert self._provider_with_config('not-a-provider') == 'deepseek'

    def test_client_cached_per_provider(self):
        with patch('dialog_manager.admin_service') as mock_admin:
            mock_admin.get_system_config.return_value = 'glm'
            with patch('dialog_manager.LLMFactory') as mock_factory:
                mock_factory.create.return_value = MagicMock()
                manager = DialogManager()
                first = manager._get_client()
                second = manager._get_client()
                assert first is second
                mock_factory.create.assert_called_once_with('glm')

    def test_injected_client_wins(self):
        """显式注入的客户端优先于工厂创建（测试注入场景）"""
        with patch('dialog_manager.admin_service') as mock_admin:
            mock_admin.get_system_config.return_value = 'glm'
            with patch('dialog_manager.LLMFactory') as mock_factory:
                manager = DialogManager()
                injected = MagicMock()
                manager.llm_client = injected
                assert manager._get_client() is injected
                mock_factory.create.assert_not_called()
