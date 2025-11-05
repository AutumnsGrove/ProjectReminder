import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from server.main import app
from server.models import ReminderParseResponse

class MockAuth:
    """Mock authentication decorator for testing."""
    def __init__(self, token=None):
        self.token = token or "test_token"

    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper

@pytest.fixture
def client():
    """Create test client for the FastAPI application."""
    return TestClient(app)

@pytest.fixture
def valid_token():
    """Provide a valid test token."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_token"

@pytest.mark.asyncio
@patch('server.voice.parser.LocalLLMParser.parse_reminder_text', new_callable=AsyncMock)
@patch('server.voice.cloudflare_parser.CloudflareAIParser.parse_reminder_text', new_callable=AsyncMock)
@patch('server.main.verify_token', side_effect=MockAuth())
async def test_parse_endpoint_authentication(
    mock_verify, 
    mock_cloud_parse, 
    mock_local_parse, 
    client: TestClient,
    valid_token: str
):
    """Test authentication scenarios for the parse endpoint."""
    # Setup mock parser results
    mock_local_parse.return_value = {
        'text': 'Test reminder', 
        'confidence': 0.9, 
        'due_date': '2025-12-01', 
        'priority': 'important'
    }

    # Test valid token
    response = client.post(
        "/api/voice/parse", 
        json={"text": "Buy milk", "mode": "local"},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    assert "text" in response.json()

    # Test missing token
    response = client.post(
        "/api/voice/parse", 
        json={"text": "Buy milk", "mode": "local"}
    )
    assert response.status_code == 401

    # Test invalid token 
    response = client.post(
        "/api/voice/parse", 
        json={"text": "Buy milk", "mode": "local"},
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
@patch('server.voice.parser.LocalLLMParser.parse_reminder_text', new_callable=AsyncMock)
@patch('server.voice.cloudflare_parser.CloudflareAIParser.parse_reminder_text', new_callable=AsyncMock)
@patch('server.main.verify_token', side_effect=MockAuth())
async def test_parse_endpoint_mode_selection(
    mock_verify, 
    mock_cloud_parse, 
    mock_local_parse, 
    client: TestClient,
    valid_token: str
):
    """Test different parsing modes."""
    # Successful local parse
    mock_local_parse.return_value = {
        'text': 'Buy milk', 
        'confidence': 0.9, 
        'due_date': '2025-12-01', 
        'priority': 'important',
        'parse_mode': 'local'
    }

    # Successful cloud parse
    mock_cloud_parse.return_value = {
        'text': 'Buy milk', 
        'confidence': 0.8, 
        'due_date': '2025-12-01', 
        'priority': 'chill',
        'parse_mode': 'cloud'
    }

    # Auto Mode: Local succeeds
    response = client.post(
        "/api/voice/parse", 
        json={"text": "Buy milk", "mode": "auto"},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result['confidence'] == 0.9
    assert result['parse_mode'] == 'local'

    # Local Mode
    response = client.post(
        "/api/voice/parse", 
        json={"text": "Buy milk", "mode": "local"},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result['confidence'] == 0.9
    assert result['parse_mode'] == 'local'

    # Cloud Mode
    mock_cloud_parse.return_value = {
        'text': 'Buy milk', 
        'confidence': 0.8, 
        'due_date': '2025-12-01', 
        'priority': 'chill',
        'parse_mode': 'cloud'
    }
    response = client.post(
        "/api/voice/parse", 
        json={"text": "Buy milk", "mode": "cloud"},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result['confidence'] == 0.8
    assert result['parse_mode'] == 'cloud'

@pytest.mark.asyncio
@patch('server.voice.parser.LocalLLMParser.parse_reminder_text', new_callable=AsyncMock)
@patch('server.voice.cloudflare_parser.CloudflareAIParser.parse_reminder_text', new_callable=AsyncMock)
@patch('server.main.verify_token', side_effect=MockAuth())
async def test_parse_endpoint_request_validation(
    mock_verify, 
    mock_cloud_parse, 
    mock_local_parse, 
    client: TestClient,
    valid_token: str
):
    """Test request validation for parse endpoint."""
    # Empty text (should raise 422)
    response = client.post(
        "/api/voice/parse", 
        json={"text": "", "mode": "local"},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 422

    # Text too long (should raise 422)
    long_text = "a" * 1001
    response = client.post(
        "/api/voice/parse", 
        json={"text": long_text, "mode": "local"},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 422

    # Invalid mode (should raise 422)
    response = client.post(
        "/api/voice/parse", 
        json={"text": "Buy milk", "mode": "invalid"},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
@patch('server.voice.parser.LocalLLMParser.parse_reminder_text', new_callable=AsyncMock)
@patch('server.voice.cloudflare_parser.CloudflareAIParser.parse_reminder_text', new_callable=AsyncMock)
@patch('server.main.verify_token', side_effect=MockAuth())
async def test_parse_endpoint_fallback_logic(
    mock_verify, 
    mock_cloud_parse, 
    mock_local_parse, 
    client: TestClient,
    valid_token: str
):
    """Test fallback parsing logic."""
    # Local with low confidence
    mock_local_parse.return_value = {
        'text': 'Buy milk', 
        'confidence': 0.1, 
        'due_date': None, 
        'priority': None
    }

    # Cloud parse with higher confidence
    mock_cloud_parse.return_value = {
        'text': 'Buy milk', 
        'confidence': 0.7, 
        'due_date': '2025-12-01', 
        'priority': 'important',
        'parse_mode': 'cloud'
    }

    # Auto mode should fallback to cloud
    response = client.post(
        "/api/voice/parse", 
        json={"text": "Buy milk", "mode": "auto"},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result['confidence'] == 0.7
    assert result['parse_mode'] == 'cloud'

    # Test both parsers failing
    mock_local_parse.side_effect = Exception("Local parse failed")
    mock_cloud_parse.side_effect = Exception("Cloud parse failed")

    # Auto mode with both parsers failing
    response = client.post(
        "/api/voice/parse", 
        json={"text": "Buy milk", "mode": "auto"},
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result['confidence'] == 0.0
    assert result['text'] == 'Buy milk'

@pytest.mark.asyncio
@patch('server.voice.parser.LocalLLMParser.parse_reminder_text', new_callable=AsyncMock)
@patch('server.voice.cloudflare_parser.CloudflareAIParser.parse_reminder_text', new_callable=AsyncMock)
@patch('server.main.verify_token', side_effect=MockAuth())
async def test_parse_endpoint_input_variety(
    mock_verify, 
    mock_cloud_parse, 
    mock_local_parse, 
    client: TestClient,
    valid_token: str
):
    """Test parsing various input styles."""
    test_inputs = [
        "Buy milk",
        "Doctor appointment tomorrow",
        "Meeting at 3pm",
        "Call mom urgent",
        "Dentist next Tuesday at 2pm, important",
        "Sometime soon maybe"
    ]

    for text in test_inputs:
        # Setup consistent mock result
        mock_local_parse.return_value = {
            'text': text, 
            'confidence': 0.8, 
            'due_date': '2025-12-01', 
            'priority': 'chill',
            'parse_mode': 'local'
        }

        response = client.post(
            "/api/voice/parse", 
            json={"text": text, "mode": "local"},
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, dict)
        assert ReminderParseResponse(**result)  # Validate model
        assert result['text'] == text
