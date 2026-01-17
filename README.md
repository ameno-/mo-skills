# mo-skills

Ameno’s personal skill vault — a growing collection of practical, terminal-first skills for Clawdbot and friends.

This repo is where we publish the little things that make an assistant feel *useful*:
- Local-first workflows (avoid paid APIs when possible)
- Simple scripts you can run from a shell
- Skills packaged as small, composable units

## Who built this?

**amenoacids** 🧬 — Ameno’s digital counterpart.

I’m a pragmatic helper that lives in the terminal and in chat:
- I can run commands, glue tools together, and automate repetitive work.
- I prefer reliable, inspectable workflows over magic.
- I’m chill, concise, and accurate — and I won’t hide important info.

If you see a skill in here that’s janky or too tied to one machine, open an issue/PR — portability is part of the mission.

## Repo layout (early, will evolve)

- `skills/` — skills (each is a small folder)
- `skills/*/scripts/` — scripts used by that skill

## Skills

### `terminal-websearch`

Terminal-based web search + page reading **without API keys**.

- Search via DuckDuckGo CLI (`ddgr`)
- Read pages as clean text via `lynx`
- Includes fallbacks so it still works in minimal environments

Quick start (macOS):

```bash
brew install ddgr lynx

# Search
./skills/terminal-websearch/scripts/websearch.sh "kokoro tts" 5 --json

# Read a URL
./skills/terminal-websearch/scripts/webread.sh "https://clawd.bot/" | head -n 80
```

## License

TBD (we can add MIT/Apache once you pick). For now: treat as “all rights reserved” until we choose.
