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

    # Convert to WAV for better compatibility with Whisper.cpp
    # WebM/Opus from browser can sometimes cause issues
    wav_path = None
    actual_audio_path = audio_path

    try:
        # Check if FFmpeg is available
        ffmpeg_check = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=False
        )

        if ffmpeg_check.returncode == 0:
            # FFmpeg available - convert to WAV
            wav_path = audio_path.replace('.webm', '.wav').replace('.mp4', '.wav')

            print(f"[Whisper] Converting to WAV for better compatibility...")
            conversion_result = subprocess.run(
                [
                    "ffmpeg",
                    "-i", audio_path,
                    "-ar", "16000",  # 16kHz sample rate (Whisper's native rate)
                    "-ac", "1",       # Mono audio
                    "-c:a", "pcm_s16le",  # PCM 16-bit WAV format
                    "-y",  # Overwrite output file
                    wav_path
                ],
                capture_output=True,
                text=True,
                check=False
            )

            if conversion_result.returncode == 0:
                print(f"[Whisper] Conversion successful: {wav_path}")
                actual_audio_path = wav_path
            else:
                print(f"[Whisper] Conversion failed, using original audio: {conversion_result.stderr}")
        else:
            print("[Whisper] FFmpeg not available, using original audio format")

    except FileNotFoundError:
        print("[Whisper] FFmpeg not found, using original audio format")
    except Exception as e:
        print(f"[Whisper] Conversion error (using original): {e}")

    try:
        # Log audio file info for debugging
        actual_file = Path(actual_audio_path)
        audio_size_kb = actual_file.stat().st_size / 1024
        print(f"[Whisper] Transcribing audio file: {actual_audio_path}")
        print(f"[Whisper] Audio file size: {audio_size_kb:.2f} KB")

        # Run Whisper.cpp with optimized flags
        result = subprocess.run(
            [
                str(WHISPER_BIN),
                "-m", str(WHISPER_MODEL),
                "-f", str(actual_audio_path),  # Use converted WAV if available
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

        # Log full Whisper output for debugging
        print(f"[Whisper] Exit code: {result.returncode}")
        print(f"[Whisper] STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"[Whisper] STDERR:\n{result.stderr}")

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
    finally:
        # Clean up temporary WAV file if it was created
        if wav_path and Path(wav_path).exists():
            try:
                Path(wav_path).unlink()
                print(f"[Whisper] Cleaned up temporary WAV file: {wav_path}")
            except Exception as e:
                print(f"[Whisper] Failed to clean up WAV file: {e}")


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