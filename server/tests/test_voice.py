"""
Tests for voice transcription endpoint.

Requirements:
- Test successful transcription
- Test authentication required
- Test invalid file types
"""

import io
from unittest.mock import patch

def test_transcribe_endpoint_success(client, test_token):
    """Test /api/voice/transcribe endpoint."""
    import io

    # Create fake audio file
    audio_data = io.BytesIO(b'fake audio data for testing')

    with patch('server.voice.whisper.transcribe_audio', return_value="Test transcription"):
        response = client.post(
            '/api/voice/transcribe',
            files={'audio': ('test.wav', audio_data, 'audio/wav')},
            headers={'Authorization': f'Bearer {test_token}'}
        )

    assert response.status_code == 200
    data = response.json()
    assert data['text'] == "Test transcription"
    assert data['model'] == 'base.en'
    assert 'file_size_bytes' in data

def test_transcribe_endpoint_no_auth(client):
    """Test endpoint requires authentication."""
    import io
    audio_data = io.BytesIO(b'fake audio data')

    response = client.post(
        '/api/voice/transcribe',
        files={'audio': ('test.wav', audio_data, 'audio/wav')}
    )

    assert response.status_code in [401, 403]

def test_transcribe_endpoint_invalid_content_type(client, test_token):
    """Test endpoint rejects non-audio files."""
    import io
    text_data = io.BytesIO(b'not audio data')

    response = client.post(
        '/api/voice/transcribe',
        files={'audio': ('test.txt', text_data, 'text/plain')},
        headers={'Authorization': f'Bearer {test_token}'}
    )

    assert response.status_code == 400

def test_transcribe_endpoint_too_large(client, test_token):
    """Test endpoint rejects files over 10MB."""
    import io
    large_data = io.BytesIO(b'0' * (10 * 1024 * 1024 + 1))

    response = client.post(
        '/api/voice/transcribe',
        files={'audio': ('large.wav', large_data, 'audio/wav')},
        headers={'Authorization': f'Bearer {test_token}'}
    )

    assert response.status_code == 413  # Payload Too Large
