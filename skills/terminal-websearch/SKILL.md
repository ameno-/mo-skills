---
name: terminal-websearch
description: Terminal-based web search + page reading without API keys (ddgr + lynx), with safe fallbacks.
---

# terminal-websearch

A simple, terminal-first web search workflow that doesn’t rely on paid APIs.

## What you get

- **Search**: DuckDuckGo via `ddgr` (JSON output supported)
- **Read**: Extract readable plaintext from a URL via `lynx -dump`
- **Fallbacks**:
  - If `ddgr` is missing, falls back to a minimal DuckDuckGo HTML scraper.
  - If `lynx` is missing, falls back to raw `curl`.

## Install

macOS (Homebrew):

```bash
brew install ddgr lynx
```

## Usage

### Search

```bash
./scripts/websearch.sh "<query>" 5
./scripts/websearch.sh "<query>" 5 --json
```

### Read

```bash
./scripts/webread.sh "<url>"
```

## Agent playbook

1. Run `websearch.sh` for the user’s query (prefer `--json` for summarization).
2. Pick the top 3 relevant URLs.
3. Run `webread.sh` on each URL and skim for the answer.
4. Reply with a concise summary + links.

## Notes / Caveats

- DuckDuckGo markup can change; the fallback scraper is best-effort.
- Some sites block scraping; if `webread.sh` returns garbage, try another result.
