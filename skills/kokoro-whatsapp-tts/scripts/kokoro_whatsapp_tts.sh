#!/usr/bin/env bash
set -euo pipefail

# kokoro_whatsapp_tts.sh
# Generate a WhatsApp-ready OGG/Opus voice note using Kokoro TTS.

usage() {
  cat >&2 <<'EOF'
Usage:
  kokoro_whatsapp_tts.sh --text "..." --out out.ogg --model /path/kokoro.onnx --voices /path/voices.bin [options]

Required:
  --text <string>         Text to speak
  --out <path.ogg>        Output OGG path
  --model <path.onnx>     Path to kokoro-v1.0.onnx
  --voices <path.bin>     Path to voices-v1.0.bin

Options:
  --voice <name>          Default: bm_george
  --lang <code>           Default: en-gb
  --speed <float>         Default: 1.08
  --bitrate <rate>        Default: 64k
  --sr <hz>               Default: 16000
EOF
}

TEXT=""
OUT_OGG=""
MODEL=""
VOICES=""
VOICE="bm_george"
LANG="en-gb"
SPEED="1.08"
BITRATE="64k"
SR="16000"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --text) TEXT="$2"; shift 2;;
    --out) OUT_OGG="$2"; shift 2;;
    --model) MODEL="$2"; shift 2;;
    --voices) VOICES="$2"; shift 2;;
    --voice) VOICE="$2"; shift 2;;
    --lang) LANG="$2"; shift 2;;
    --speed) SPEED="$2"; shift 2;;
    --bitrate) BITRATE="$2"; shift 2;;
    --sr) SR="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2;;
  esac
done

if [[ -z "$TEXT" || -z "$OUT_OGG" || -z "$MODEL" || -z "$VOICES" ]]; then
  usage
  exit 2
fi

if ! command -v kokoro-tts >/dev/null 2>&1; then
  echo "Missing dependency: kokoro-tts" >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Missing dependency: ffmpeg" >&2
  exit 1
fi

TMP_DIR="${TMPDIR:-/tmp}/kokoro_whatsapp_tts"
mkdir -p "$TMP_DIR"

TMP_TXT="$TMP_DIR/input_$$.txt"
TMP_WAV="$TMP_DIR/output_$$.wav"

printf "%s\n" "$TEXT" > "$TMP_TXT"

kokoro-tts "$TMP_TXT" "$TMP_WAV" \
  --model "$MODEL" \
  --voices "$VOICES" \
  --voice "$VOICE" \
  --lang "$LANG" \
  --speed "$SPEED" \
  --format wav >/dev/null

ffmpeg -hide_banner -loglevel error -y \
  -i "$TMP_WAV" \
  -c:a libopus -b:a "$BITRATE" -ar "$SR" -ac 1 \
  "$OUT_OGG"

rm -f "$TMP_TXT" "$TMP_WAV"

echo "$OUT_OGG"
