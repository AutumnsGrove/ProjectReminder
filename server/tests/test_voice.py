"""
Tests for voice transcription module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import subprocess

from server.voice.whisper import (
    transcribe_audio,
    validate_whisper_installation,
    get_whisper_info,
    WHISPER_BIN,
    WHISPER_MODEL
)


class TestWhisperValidation:
    """Test Whisper.cpp installation validation."""

    def test_validate_installation_success(self):
        """Test validation passes when binary and model exist."""
        with patch('server.voice.whisper.WHISPER_BIN') as mock_bin:
            with patch('server.voice.whisper.WHISPER_MODEL') as mock_model:
                mock_bin.exists.return_value = True
                mock_model.exists.return_value = True

                # Should not raise
                validate_whisper_installation()

    def test_validate_installation_no_binary(self):
        """Test validation fails when binary missing."""
        with patch('server.voice.whisper.WHISPER_BIN') as mock_bin:
            mock_bin.exists.return_value = False

            with pytest.raises(RuntimeError, match="Whisper binary not found"):
                validate_whisper_installation()

    def test_validate_installation_no_model(self):
        """Test validation fails when model missing."""
        with patch('server.voice.whisper.WHISPER_BIN') as mock_bin:
            with patch('server.voice.whisper.WHISPER_MODEL') as mock_model:
                mock_bin.exists.return_value = True
                mock_model.exists.return_value = False

                with pytest.raises(RuntimeError, match="Whisper model not found"):
                    validate_whisper_installation()


class TestTranscribeAudio:
    """Test audio transcription function."""

    def test_transcribe_success(self, tmp_path):
        """Test successful transcription."""
        # Create temp audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b'fake audio data')

        # Mock subprocess and path validation
        with patch('server.voice.whisper.validate_whisper_installation'):
            with patch('subprocess.run') as mock_run:
                # Simulate Whisper.cpp output
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout='whisper_init: loading model\nprocessing audio...\nCall mom about Thanksgiving\n',
                    stderr=''
                )

                result = transcribe_audio(str(audio_file))

                assert result == 'Call mom about Thanksgiving'
                mock_run.assert_called_once()

                # Verify correct CLI args
                call_args = mock_run.call_args[0][0]
                assert '-otxt' in call_args
                assert '--no-timestamps' in call_args
                assert '-l' in call_args
                assert 'en' in call_args

    def test_transcribe_audio_file_not_found(self):
        """Test error when audio file doesn't exist."""
        with patch('server.voice.whisper.validate_whisper_installation'):
            with pytest.raises(FileNotFoundError, match="Audio file not found"):
                transcribe_audio('/nonexistent/audio.wav')

    def test_transcribe_whisper_binary_not_found(self):
        """Test error when Whisper binary missing."""
        with patch('server.voice.whisper.WHISPER_BIN') as mock_bin:
            mock_bin.exists.return_value = False

            with pytest.raises(RuntimeError, match="Whisper binary not found"):
                transcribe_audio('/tmp/test.wav')

    def test_transcribe_timeout(self, tmp_path):
        """Test timeout handling."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b'fake audio data')

        with patch('server.voice.whisper.validate_whisper_installation'):
            with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('cmd', 30)):
                with pytest.raises(RuntimeError, match="Transcription timeout"):
                    transcribe_audio(str(audio_file))

    def test_transcribe_empty_result(self, tmp_path):
        """Test error when transcription is empty."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b'fake audio data')

        with patch('server.voice.whisper.validate_whisper_installation'):
            with patch('subprocess.run') as mock_run:
                # Simulate silent audio
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout='whisper_init: loading model\nprocessing audio...\n[BLANK_AUDIO]\n',
                    stderr=''
                )

                with pytest.raises(RuntimeError, match="No transcription found"):
                    transcribe_audio(str(audio_file))

    def test_transcribe_nonzero_exit(self, tmp_path):
        """Test error when Whisper.cpp fails."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b'fake audio data')

        with patch('server.voice.whisper.validate_whisper_installation'):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=1,
                    stdout='',
                    stderr='error: could not process audio'
                )

                with pytest.raises(RuntimeError, match="Whisper.cpp failed"):
                    transcribe_audio(str(audio_file))


class TestGetWhisperInfo:
    """Test Whisper info function."""

    def test_get_whisper_info(self):
        """Test getting Whisper installation info."""
        with patch('server.voice.whisper.WHISPER_BIN') as mock_bin:
            with patch('server.voice.whisper.WHISPER_MODEL') as mock_model:
                mock_bin.exists.return_value = True
                mock_model.exists.return_value = True

                # Mock file size
                mock_stat = Mock()
                mock_stat.st_size = 141 * 1024 * 1024  # 141MB
                mock_model.stat.return_value = mock_stat

                info = get_whisper_info()

                assert info['binary_exists'] is True
                assert info['model_exists'] is True
                assert info['model_name'] == 'base.en'
                assert info['model_size_mb'] == 141.0