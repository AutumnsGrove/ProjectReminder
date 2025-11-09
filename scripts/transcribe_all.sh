#!/bin/bash
set -e

PROJECT_DIR="/Users/autumn/Documents/Projects/ProjectReminder"
cd "$PROJECT_DIR"

# Create directories
mkdir -p audio_converted/wav
mkdir -p transcriptions

WHISPER_BIN="$PROJECT_DIR/whisper.cpp/build/bin/whisper-cli"
MODEL_PATH="$PROJECT_DIR/whisper.cpp/models/ggml-base.en.bin"
SOURCE_DIR="$PROJECT_DIR/EXAMPLE_RECORDINGS"

echo "=== STARTING CONVERSION & TRANSCRIPTION PROCESS ==="
echo "Source: $SOURCE_DIR"
echo "WAV Output: $PROJECT_DIR/audio_converted/wav"
echo "Transcriptions: $PROJECT_DIR/transcriptions"
echo ""

# Step 1: Convert M4A to WAV
echo "=== STEP 1: Converting M4A files to WAV ==="
for i in {1..25}; do
  if [ $i -eq 1 ]; then
    input_file="$SOURCE_DIR/VN Sandwich.m4a"
    output_file="$PROJECT_DIR/audio_converted/wav/VN Sandwich.wav"
  else
    input_file="$SOURCE_DIR/VN Sandwich ${i}.m4a"
    output_file="$PROJECT_DIR/audio_converted/wav/VN Sandwich ${i}.wav"
  fi
  
  if [ -f "$input_file" ]; then
    echo "Converting [$i/25]: $(basename "$input_file")"
    ffmpeg -i "$input_file" -acodec pcm_s16le -ar 16000 "$output_file" -y 2>/dev/null
    if [ -f "$output_file" ]; then
      echo "  ✓ Converted"
    else
      echo "  ✗ FAILED"
    fi
  else
    echo "[$i/25] File not found: $input_file"
  fi
done

echo ""
echo "=== Conversion Complete ==="
WAV_COUNT=$(ls "$PROJECT_DIR/audio_converted/wav/"*.wav 2>/dev/null | wc -l)
echo "WAV files ready: $WAV_COUNT"
echo ""

# Step 2: Transcribe WAV files
echo "=== STEP 2: Transcribing WAV files ==="
START_TIME=$(date +%s)

for i in {1..25}; do
  if [ $i -eq 1 ]; then
    wav_file="$PROJECT_DIR/audio_converted/wav/VN Sandwich.wav"
  else
    wav_file="$PROJECT_DIR/audio_converted/wav/VN Sandwich ${i}.wav"
  fi
  
  if [ -f "$wav_file" ]; then
    echo "Transcribing [$i/25]: $(basename "$wav_file")"
    FILE_START=$(date +%s)
    
    "$WHISPER_BIN" \
      -m "$MODEL_PATH" \
      -f "$wav_file" \
      -t 4 \
      -l en \
      --no-timestamps \
      -otxt \
      -of "$PROJECT_DIR/transcriptions/test_${i}" 2>/dev/null || true
    
    FILE_END=$(date +%s)
    FILE_TIME=$((FILE_END - FILE_START))
    
    if [ -f "$PROJECT_DIR/transcriptions/test_${i}.txt" ]; then
      echo "  ✓ Done in ${FILE_TIME}s"
    else
      echo "  ✗ FAILED"
    fi
  fi
done

END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo ""
echo "=== TRANSCRIPTION COMPLETE ==="
TRANSCRIBED=$(ls "$PROJECT_DIR/transcriptions/test_"*.txt 2>/dev/null | wc -l)
echo "Files transcribed: $TRANSCRIBED/25"
echo "Total time: ${TOTAL_TIME}s"
if [ $TRANSCRIBED -gt 0 ]; then
  AVG_TIME=$((TOTAL_TIME / TRANSCRIBED))
  echo "Average time per file: ${AVG_TIME}s"
fi

# Create combined transcription file
echo "" > "$PROJECT_DIR/transcriptions/all_transcriptions.txt"
for i in {1..25}; do
  if [ -f "$PROJECT_DIR/transcriptions/test_${i}.txt" ]; then
    if [ $i -eq 1 ]; then
      echo "VN Sandwich.m4a:" >> "$PROJECT_DIR/transcriptions/all_transcriptions.txt"
    else
      echo "VN Sandwich ${i}.m4a:" >> "$PROJECT_DIR/transcriptions/all_transcriptions.txt"
    fi
    cat "$PROJECT_DIR/transcriptions/test_${i}.txt" >> "$PROJECT_DIR/transcriptions/all_transcriptions.txt"
    echo "" >> "$PROJECT_DIR/transcriptions/all_transcriptions.txt"
  fi
done

echo ""
echo "=== RESULTS ==="
echo "Summary file: transcriptions/all_transcriptions.txt"
echo ""
echo "=== SAMPLE TRANSCRIPTIONS (first 5) ==="
for i in {1..5}; do
  if [ -f "$PROJECT_DIR/transcriptions/test_${i}.txt" ]; then
    echo "[$i] $(cat "$PROJECT_DIR/transcriptions/test_${i}.txt" | head -c 120)"
    if [ $(wc -c < "$PROJECT_DIR/transcriptions/test_${i}.txt") -gt 120 ]; then
      echo "..."
    fi
    echo ""
  fi
done
