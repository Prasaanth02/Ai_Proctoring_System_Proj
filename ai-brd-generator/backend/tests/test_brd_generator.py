import pytest
from unittest.mock import patch, MagicMock
from backend.app.brd_generator import generate_brd


MOCK_BRD = "# Business Requirements Document\n\n## 1. Project Title\nTest Project"


def _mock_openai_response(content: str):
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


@patch("backend.app.brd_generator.OpenAI")
def test_generate_brd_returns_content(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_openai_response(MOCK_BRD)

    result = generate_brd("We need a customer portal for managing orders.")
    assert "Business Requirements Document" in result
    assert "Project Title" in result


@patch("backend.app.brd_generator.OpenAI")
def test_generate_brd_calls_llm_once(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _mock_openai_response(MOCK_BRD)

    generate_brd("Some business text.")
    mock_client.chat.completions.create.assert_called_once()


def test_generate_brd_empty_input_raises():
    with pytest.raises(ValueError, match="Source text is empty"):
        generate_brd("")


def test_generate_brd_whitespace_input_raises():
    with pytest.raises(ValueError, match="Source text is empty"):
        generate_brd("   \n  ")
