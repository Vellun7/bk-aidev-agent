# -*- coding: utf-8 -*-
"""``LLMService``：请求级 resource_manager 必须一路传到平台 client。

若 ``list_llms`` 忽略传入的 manager 再 ``AgentResourceManager(username=...)``，
会回到主智能体空间拉模型列表，子智能体热切换授权会误判。
"""

from unittest.mock import MagicMock, patch

from aidev_bkplugin.services.llm import LLMService


def test_list_llms_uses_injected_resource_manager_client():
    rm = MagicMock(name="request_rm")
    client = MagicMock(name="client")
    rm.get_client.return_value = client
    client.api.list_agents_v1_llms.return_value = {"data": [{"llm_code": "qwen-plus"}]}

    with patch("aidev_bkplugin.services.llm.AgentResourceManager") as mock_cls:
        result = LLMService.list_llms(username="alice", resource_manager=rm)

    mock_cls.assert_not_called()
    rm.get_client.assert_called_once_with()
    client.api.list_agents_v1_llms.assert_called_once_with(params={})
    assert result == [{"llm_code": "qwen-plus"}]


def test_list_llms_does_not_send_user_header():
    """有 username 也不带 X-BKAIDEV-USER，避免应用态 JWT 下平台 IAM Subject 为空。"""
    rm = MagicMock(name="request_rm")
    rm.get_client.return_value.api.list_agents_v1_llms.return_value = {"data": []}

    LLMService.list_llms(username="alice", resource_manager=rm)

    _, kwargs = rm.get_client.return_value.api.list_agents_v1_llms.call_args
    assert "headers" not in kwargs or "X-BKAIDEV-USER" not in (kwargs.get("headers") or {})


def test_is_llm_accessible_forwards_resource_manager_to_list_llms():
    rm = MagicMock(name="request_rm")
    with patch.object(LLMService, "list_llms", return_value=[{"llm_code": "qwen-plus"}]) as mock_list:
        assert LLMService.is_llm_accessible(username="alice", llm_code="qwen-plus", resource_manager=rm) is True
    mock_list.assert_called_once_with(username="alice", resource_manager=rm)
