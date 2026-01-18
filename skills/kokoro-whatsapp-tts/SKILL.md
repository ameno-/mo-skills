---
name: kokoro-whatsapp-tts
description: Generate WhatsApp-ready voice notes (OGG/Opus) locally using Kokoro TTS + ffmpeg. Defaults to a British male voice.
---

# kokoro-whatsapp-tts

Local text-to-speech → **WhatsApp voice note** output.

This skill produces **OGG/Opus** audio (the format WhatsApp reliably plays for voice notes).

## What you get

- Generate `.ogg` voice notes from text
- Tunable voice + speed
- Defaults tuned for “British englishman, a bit faster”

## Dependencies

- `kokoro-tts` CLI installed and working
- Kokoro model files available:
  - `kokoro-v1.0.onnx`
  - `voices-v1.0.bin`
- `ffmpeg` (for Opus/OGG encoding)

## Setup (example)

Put the model files somewhere stable and pass their paths (recommended). Example:

```bash
mkdir -p ~/models/kokoro
cd ~/models/kokoro
curl -L -O https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx
curl -L -O https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin
```

## Usage

### 1) Generate a voice note

```bash
./scripts/kokoro_whatsapp_tts.sh \
  --text "Big Dawg, you are cute." \
  --out ./out.ogg \
  --model ~/models/kokoro/kokoro-v1.0.onnx \
  --voices ~/models/kokoro/voices-v1.0.bin
```

### 2) Change voice/speed

```bash
./scripts/kokoro_whatsapp_tts.sh \
  --text "Hello." \
  --out ./hello.ogg \
  --model ~/models/kokoro/kokoro-v1.0.onnx \
  --voices ~/models/kokoro/voices-v1.0.bin \
  --voice bm_george \
  --lang en-gb \
  --speed 1.08
```

### 3) List voices

```bash
kokoro-tts --help-voices --model ~/models/kokoro/kokoro-v1.0.onnx --voices ~/models/kokoro/voices-v1.0.bin
```

## Defaults

- Voice: `bm_george`
- Language: `en-gb`
- Speed: `1.08`
- WhatsApp encoding: Opus in OGG, mono, 16kHz, ~64kbps

## Notes

- If WhatsApp fails to play a file, it’s almost always the container/codec. Use OGG/Opus.
- Some voices only sound good with their matching language code.
