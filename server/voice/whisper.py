"""
Whisper.cpp Python wrapper for voice transcription.

This module provides a Python interface to the locally-installed Whisper.cpp
binary for offline speech-to-text transcription.
"""

import subprocess
import os
from pathlib import Path
from typing import Optional

# Determine project root and Whisper paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
WHISPER_BIN = PROJECT_ROOT / "whisper.cpp" / "build" / "bin" / "whisper-cli"
WHISPER_MODEL = PROJECT_ROOT / "whisper.cpp" / "models" / "ggml-base.en.bin"


def validate_whisper_installation() -> None:
    """
    Validate that Whisper.cpp binary and model exist.

    Raises:
        RuntimeError: If binary or model not found
    """
    if not WHISPER_BIN.exists():
        raise RuntimeError(
            f"Whisper binary not found at {WHISPER_BIN}. "
            "Run: cd whisper.cpp && make"
        )

    if not WHISPER_MODEL.exists():
        raise RuntimeError(
            f"Whisper model not found at {WHISPER_MODEL}. "
            "Run: cd whisper.cpp && bash ./models/download-ggml-model.sh base.en"
        )


def transcribe_audio(audio_path: str, timeout: int = 30) -> str:
    """
    Transcribe audio file using Whisper.cpp.

    Args:
        audio_path: Path to audio file (WAV/WebM/MP4)
        timeout: Max processing time in seconds (default: 30)

    Returns:
        Transcribed text string

    Raises:
        RuntimeError: If Whisper binary/model not found or transcription fails
        subprocess.TimeoutExpired: If transcription exceeds timeout
        FileNotFoundError: If audio file doesn't exist

    Example:
        >>> text = transcribe_audio("/tmp/recording.wav")
        >>> print(text)
        "Call mom about Thanksgiving"
    """
    # Validate installation
    validate_whisper_installation()

    # Validate audio file exists
    audio_file = Path(audio_path)
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # TODO: Add ffmpeg conversion for WebM → WAV if Whisper.cpp fails
    # This would improve compatibility and potentially speed up transcription.
    # For MVP, we rely on Whisper.cpp's built-in ffmpeg integration.

    try:
        # Run Whisper.cpp with optimized flags
        result = subprocess.run(
            [
                str(WHISPER_BIN),
                "-m", str(WHISPER_MODEL),
                "-f", str(audio_path),
                "-otxt",  # Plain text output (not SRT/VTT)
                "--no-timestamps",  # Faster, no word timing needed
                "-l", "en",  # Force English (base.en model)
                "-t", "4"  # 4 threads (good balance)
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False  # Don't raise on non-zero exit
        )

        # Check for errors
        if result.returncode != 0:
            raise RuntimeError(
                f"Whisper.cpp failed with exit code {result.returncode}: "
                f"{result.stderr}"
            )

        # Parse output: Extract transcribed text
        # Whisper outputs log lines followed by transcription
        lines = result.stdout.strip().split('\n')

        # Find transcription (last non-empty line that's not a log line)
        transcription = None
        for line in reversed(lines):
            line = line.strip()

            # Skip empty lines and log lines
            if not line:
                continue
            if line.startswith('['):  # Timestamp or metadata
                continue
            if line.startswith('whisper_'):  # Log line
                continue
            if 'processing' in line.lower():  # Log line
                continue
            if 'system_info' in line.lower():  # Log line
                continue

            # Found transcription
            transcription = line
            break

        # Validate we got a transcription
        if not transcription:
            raise RuntimeError(
                "No transcription found in Whisper output. "
                "Audio may be silent or corrupted."
            )

        # Clean up common Whisper artifacts
        transcription = transcription.strip()
        if transcription in ['[BLANK_AUDIO]', '(silence)', '(music)', '']:
            raise RuntimeError(
                "No speech detected in audio. "
                "Please speak louder and try again."
            )

        return transcription

    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"Transcription timeout after {timeout} seconds. "
            "Recording may be too long."
        )
    except Exception as e:
        # Re-raise with context
        if isinstance(e, RuntimeError):
            raise
        raise RuntimeError(f"Transcription failed: {str(e)}")


def get_whisper_info() -> dict:
    """
    Get information about Whisper.cpp installation.

    Returns:
        Dict with binary path, model path, installation status
    """
    return {
        "binary_path": str(WHISPER_BIN),
        "model_path": str(WHISPER_MODEL),
        "binary_exists": WHISPER_BIN.exists(),
        "model_exists": WHISPER_MODEL.exists(),
        "model_name": "base.en",
        "model_size_mb": round(WHISPER_MODEL.stat().st_size / (1024 * 1024), 1) if WHISPER_MODEL.exists() else 0
    }