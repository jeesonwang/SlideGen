import asyncio
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

from agno.models.response import ModelResponse

sys.modules.setdefault("aiohttp", ModuleType("aiohttp"))

from slidegen.schemas.llm_config import LLMConfigTest

llm_factory_spec = spec_from_file_location(
    "test_llm_factory_module",
    Path(__file__).resolve().parents[1] / "slidegen/services/factories/llm_factory.py",
)
assert llm_factory_spec is not None and llm_factory_spec.loader is not None
llm_factory_module = module_from_spec(llm_factory_spec)
llm_factory_spec.loader.exec_module(llm_factory_module)
LLMFactory = llm_factory_module.LLMFactory


def test_test_llm_config_uses_response_api() -> None:
    config = LLMConfigTest(
        provider="custom",
        model_id="demo-model",
        api_key="test-key",
        base_url="https://example.com/v1",
        test_prompt="Ping",
    )
    mock_llm = Mock()
    mock_llm.response.return_value = ModelResponse(content="Pong")
    mock_llm.invoke.side_effect = AssertionError("test_llm_config should use response() instead of invoke()")

    with patch.object(LLMFactory, "create_llm", return_value=mock_llm):
        result = asyncio.run(LLMFactory.test_llm_config(config))

    mock_llm.response.assert_called_once()
    assert result.success is True
    assert result.response == "Pong"
