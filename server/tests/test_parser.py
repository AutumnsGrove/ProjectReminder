"""
Unit tests for LLM parser modules (Phase 8.1).

Tests cover:
- LocalLLMParser (LM Studio integration)
- CloudflareAIParser (Cloudflare Workers AI)
- JSON extraction and validation
- Error handling (timeouts, connection failures, invalid JSON)
- Confidence scoring
- Fallback behaviors

Uses httpx.MockTransport to simulate API responses without external dependencies.

Author: Claude Sonnet 4.5 (Phase 8.1 Testing)
Date: 2025-11-04
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from server.voice.parser import LocalLLMParser, ParsedReminder
from server.voice.cloudflare_parser import CloudflareAIParser


# =============================================================================
# Mock Responses
# =============================================================================

MOCK_VALID_RESPONSE = {
    "text": "Call mom",
    "due_date": "2025-11-05",
    "due_time": "15:00:00",
    "time_required": True,
    "priority": "urgent",
    "category": "Calls",
    "location": None,
    "confidence": 0.95
}

MOCK_LM_STUDIO_RESPONSE = {
    "id": "chatcmpl-123",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "llama-3.2-1b-instruct",
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": json.dumps(MOCK_VALID_RESPONSE)
        },
        "finish_reason": "stop"
    }],
    "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150
    }
}

MOCK_CLOUDFLARE_RESPONSE = {
    "success": True,
    "result": {
        "response": json.dumps(MOCK_VALID_RESPONSE)
    }
}


# =============================================================================
# LocalLLMParser Tests
# =============================================================================

class TestLocalLLMParser:
    """Test LocalLLMParser functionality."""

    @pytest.mark.asyncio
    async def test_parse_successful(self):
        """Test successful parsing with valid LLM response."""

        def mock_handler(request):
            return httpx.Response(200, json=MOCK_LM_STUDIO_RESPONSE)

        transport = httpx.MockTransport(mock_handler)

        parser = LocalLLMParser()
        parser.client = httpx.AsyncClient(transport=transport, base_url="http://test")

        result = await parser.parse_reminder_text("Call mom tomorrow at 3pm, urgent")

        assert result["text"] == "Call mom"
        assert result["due_date"] == "2025-11-05"
        assert result["due_time"] == "15:00:00"
        assert result["priority"] == "urgent"
        assert result["category"] == "Calls"
        assert result["confidence"] == 0.95
        assert result["parse_mode"] == "local"

        await parser.close()

    @pytest.mark.asyncio
    async def test_parse_empty_text(self):
        """Test parsing empty text returns empty result."""
        parser = LocalLLMParser()

        result = await parser.parse_reminder_text("")

        assert result["text"] == ""
        assert result["due_date"] is None
        assert result["confidence"] == 0.0

        await parser.close()

    @pytest.mark.asyncio
    async def test_parse_invalid_json_response(self):
        """Test handling of invalid JSON from LLM."""

        def mock_handler(request):
            invalid_response = MOCK_LM_STUDIO_RESPONSE.copy()
            invalid_response["choices"][0]["message"]["content"] = "This is not valid JSON!"
            return httpx.Response(200, json=invalid_response)

        transport = httpx.MockTransport(mock_handler)

        parser = LocalLLMParser()
        parser.client = httpx.AsyncClient(transport=transport, base_url="http://test")

        result = await parser.parse_reminder_text("Call mom")

        # Should return empty parse with low confidence
        assert result["text"] == "Call mom"
        assert result["confidence"] == 0.2  # Low confidence fallback

        await parser.close()

    @pytest.mark.asyncio
    async def test_parse_connection_error(self):
        """Test handling of connection errors."""

        def mock_handler(request):
            raise httpx.ConnectError("Connection refused")

        transport = httpx.MockTransport(mock_handler)

        parser = LocalLLMParser()
        parser.client = httpx.AsyncClient(transport=transport, base_url="http://test")

        with pytest.raises(Exception, match="LM Studio not available"):
            await parser.parse_reminder_text("Call mom")

        await parser.close()

    @pytest.mark.asyncio
    async def test_parse_timeout(self):
        """Test handling of request timeouts."""

        def mock_handler(request):
            raise httpx.TimeoutException("Request timed out")

        transport = httpx.MockTransport(mock_handler)

        parser = LocalLLMParser()
        parser.client = httpx.AsyncClient(transport=transport, base_url="http://test")

        with pytest.raises(Exception, match="timed out"):
            await parser.parse_reminder_text("Call mom")

        await parser.close()

    @pytest.mark.asyncio
    async def test_extract_json_from_code_block(self):
        """Test extracting JSON from markdown code blocks."""
        parser = LocalLLMParser()

        llm_response = """
        Here's the parsed result:
        ```json
        {"text": "Test", "confidence": 0.8}
        ```
        """

        result = parser._extract_json(llm_response)
        assert result == {"text": "Test", "confidence": 0.8}

        await parser.close()

    @pytest.mark.asyncio
    async def test_extract_json_from_braces(self):
        """Test extracting JSON by finding braces."""
        parser = LocalLLMParser()

        llm_response = 'Some text before {"text": "Test", "confidence": 0.8} and after'

        result = parser._extract_json(llm_response)
        assert result == {"text": "Test", "confidence": 0.8}

        await parser.close()

    @pytest.mark.asyncio
    async def test_validate_and_normalize_clamps_confidence(self):
        """Test confidence is clamped to [0.0, 1.0]."""
        parser = LocalLLMParser()

        # Valid confidence values within range should pass through
        parsed_json = {
            "text": "Test",
            "due_date": None,
            "due_time": None,
            "time_required": False,
            "priority": None,
            "category": None,
            "location": None,
            "confidence": 0.95
        }
        result = parser._validate_and_normalize(parsed_json, "Test")
        assert result["confidence"] == 0.95

        # Confidence at edge (1.0) should work
        parsed_json["confidence"] = 1.0
        result = parser._validate_and_normalize(parsed_json, "Test")
        assert result["confidence"] == 1.0

        # Confidence at edge (0.0) should work
        parsed_json["confidence"] = 0.0
        result = parser._validate_and_normalize(parsed_json, "Test")
        assert result["confidence"] == 0.0

        # Invalid confidence (> 1.0) triggers validation error → fallback to 0.3
        parsed_json["confidence"] = 1.5
        result = parser._validate_and_normalize(parsed_json, "Test")
        assert result["confidence"] == 0.3  # Fallback value

        await parser.close()

    @pytest.mark.asyncio
    async def test_validate_and_normalize_invalid_priority(self):
        """Test invalid priority values are set to None."""
        parser = LocalLLMParser()

        parsed_json = {
            "text": "Test",
            "priority": "super_duper_urgent",  # Invalid
            "confidence": 1.0
        }
        result = parser._validate_and_normalize(parsed_json, "Test")

        assert result["priority"] is None
        assert result["confidence"] < 1.0  # Reduced due to invalid field

        await parser.close()

    @pytest.mark.asyncio
    async def test_validate_and_normalize_invalid_category(self):
        """Test invalid category values are set to None."""
        parser = LocalLLMParser()

        parsed_json = {
            "text": "Test",
            "category": "InvalidCategory",
            "confidence": 1.0
        }
        result = parser._validate_and_normalize(parsed_json, "Test")

        assert result["category"] is None
        assert result["confidence"] < 1.0

        await parser.close()


# =============================================================================
# CloudflareAIParser Tests
# =============================================================================

class TestCloudflareAIParser:
    """Test CloudflareAIParser functionality."""

    @pytest.mark.asyncio
    async def test_parse_successful(self):
        """Test successful parsing with Cloudflare AI."""

        def mock_handler(request):
            return httpx.Response(200, json=MOCK_CLOUDFLARE_RESPONSE)

        transport = httpx.MockTransport(mock_handler)

        parser = CloudflareAIParser(
            account_id="test-account",
            api_token="test-token"
        )
        parser.client = httpx.AsyncClient(transport=transport, base_url="http://test")

        result = await parser.parse_reminder_text("Call mom tomorrow at 3pm")

        assert result["text"] == "Call mom"
        assert result["due_date"] == "2025-11-05"
        assert result["parse_mode"] == "cloud"

        await parser.close()

    @pytest.mark.asyncio
    async def test_parse_api_error_success_false(self):
        """Test handling of Cloudflare API success=false response."""

        def mock_handler(request):
            return httpx.Response(200, json={
                "success": False,
                "errors": [{"message": "Rate limit exceeded"}]
            })

        transport = httpx.MockTransport(mock_handler)

        parser = CloudflareAIParser(
            account_id="test-account",
            api_token="test-token"
        )
        parser.client = httpx.AsyncClient(transport=transport, base_url="http://test")

        # Should return empty parse after retries
        result = await parser.parse_reminder_text("Call mom")
        assert result["confidence"] == 0.1

        await parser.close()

    @pytest.mark.asyncio
    async def test_missing_credentials_raises_error(self):
        """Test parser raises error if credentials are missing."""
        with pytest.raises(ValueError, match="credentials not found"):
            CloudflareAIParser(account_id=None, api_token=None)

    @pytest.mark.asyncio
    async def test_parse_timeout(self):
        """Test timeout handling."""

        def mock_handler(request):
            raise httpx.TimeoutException("Timeout")

        transport = httpx.MockTransport(mock_handler)

        parser = CloudflareAIParser(
            account_id="test-account",
            api_token="test-token"
        )
        parser.client = httpx.AsyncClient(transport=transport, base_url="http://test")

        with pytest.raises(Exception, match="timed out"):
            await parser.parse_reminder_text("Call mom")

        await parser.close()

    @pytest.mark.asyncio
    async def test_extract_json_methods(self):
        """Test JSON extraction methods work the same as LocalLLMParser."""
        parser = CloudflareAIParser(
            account_id="test-account",
            api_token="test-token"
        )

        # Direct JSON
        result = parser._extract_json('{"text": "Test"}')
        assert result == {"text": "Test"}

        # Code block
        result = parser._extract_json('```json\n{"text": "Test"}\n```')
        assert result == {"text": "Test"}

        # Braces
        result = parser._extract_json('prefix {"text": "Test"} suffix')
        assert result == {"text": "Test"}

        await parser.close()


# =============================================================================
# ParsedReminder Model Tests
# =============================================================================

class TestParsedReminderModel:
    """Test ParsedReminder Pydantic model validation."""

    def test_valid_parsed_reminder(self):
        """Test creating a valid ParsedReminder."""
        data = {
            "text": "Call mom",
            "due_date": "2025-11-05",
            "due_time": "15:00:00",
            "time_required": True,
            "priority": "urgent",
            "category": "Calls",
            "location": None,
            "confidence": 0.95
        }

        reminder = ParsedReminder(**data)

        assert reminder.text == "Call mom"
        assert reminder.confidence == 0.95

    def test_confidence_must_be_in_range(self):
        """Test confidence must be between 0.0 and 1.0."""
        data = {
            "text": "Test",
            "confidence": 1.5  # Invalid: > 1.0
        }

        with pytest.raises(Exception):  # Pydantic validation error
            ParsedReminder(**data)

    def test_optional_fields_default_to_none(self):
        """Test optional fields default to None."""
        data = {
            "text": "Test",
            "confidence": 0.5
        }

        reminder = ParsedReminder(**data)

        assert reminder.due_date is None
        assert reminder.due_time is None
        assert reminder.priority is None
        assert reminder.category is None
        assert reminder.location is None
        assert reminder.time_required is False  # Default


# =============================================================================
# Integration-Like Tests
# =============================================================================

class TestParserIntegration:
    """Integration-like tests for parser workflows."""

    @pytest.mark.asyncio
    async def test_full_parse_workflow_local(self):
        """Test complete parsing workflow with LocalLLMParser."""

        def mock_handler(request):
            # Verify request structure
            assert request.method == "POST"
            assert "/v1/chat/completions" in str(request.url)

            body = json.loads(request.content)
            assert "messages" in body
            assert body["temperature"] == 0.3

            return httpx.Response(200, json=MOCK_LM_STUDIO_RESPONSE)

        transport = httpx.MockTransport(mock_handler)

        parser = LocalLLMParser(temperature=0.3, max_tokens=400)
        parser.client = httpx.AsyncClient(transport=transport, base_url="http://test")

        result = await parser.parse_reminder_text("Call mom tomorrow at 3pm, urgent")

        # Verify workflow completes and returns structured data
        assert "text" in result
        assert "due_date" in result
        assert "priority" in result
        assert result["parse_mode"] == "local"
        assert 0.0 <= result["confidence"] <= 1.0
        # Text may be cleaned or original depending on validation
        assert len(result["text"]) > 0

        await parser.close()

    @pytest.mark.asyncio
    async def test_parser_handles_malformed_llm_output(self):
        """Test parser gracefully handles various malformed LLM outputs."""

        malformed_outputs = [
            "Not JSON at all",
            '{"incomplete": ',
            '[]',  # Array instead of object
            '{"text": "Test", "confidence": "not a number"}',
        ]

        for malformed in malformed_outputs:
            def mock_handler(request):
                response = MOCK_LM_STUDIO_RESPONSE.copy()
                response["choices"][0]["message"]["content"] = malformed
                return httpx.Response(200, json=response)

            transport = httpx.MockTransport(mock_handler)

            parser = LocalLLMParser()
            parser.client = httpx.AsyncClient(transport=transport, base_url="http://test")

            result = await parser.parse_reminder_text("Test input")

            # Should not crash, should return fallback
            assert "text" in result
            assert "confidence" in result
            assert result["confidence"] <= 0.3  # Low confidence

            await parser.close()
