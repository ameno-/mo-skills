---
name: local-memory-curator
description: Local-only staged memory: tail Clawdbot session JSONL logs, propose memory candidates, require explicit approval, then write durable memory + Apple Notes Open Loops.
---

# local-memory-curator

A local-only, staged memory system.

- **Input**: Clawdbot session log streams (`~/.clawdbot/agents/*/sessions/*.jsonl`)
- **Staging**: candidates go to a local inbox file
- **Approval**: explicit user approval (👍 reaction or reply like `approve` / `reject` / `edit: ...`)
- **Actions**:
  - Durable memory entries → append to `memory/YYYY-MM-DD.md`
  - Open loops → append to Apple Notes folder `Mo`, note `Mo Open Loops`
  - If an action has no workflow → create an open loop “Design workflow for: …”

## Files (local-only)

- Workspace memory (defaults; configurable via script flags):
  - `~/clawd/memory/`
  - `~/clawd/memory/inbox/`
  - `~/clawd/memory/state.json`
- Apple Notes:
  - Folder: `Mo`
  - Note: `Mo Open Loops`

## Scripts

- Scan logs for new candidates:
  - `python3 ./scripts/memory_scan.py --write`
- List pending candidates:
  - `python3 ./scripts/memory_scan.py --list`
- Format a single candidate into a WhatsApp approval request:
  - `python3 ./scripts/memory_notify_format.py <cand_id>`
- Watch logs for approvals (user sends `approve cand_...` etc):
  - `python3 ./scripts/memory_watch_approvals.py --once`
- Approve/reject directly (CLI):
  - `python3 ./scripts/memory_apply.py approve <id>`
  - `python3 ./scripts/memory_apply.py reject <id>`

If your workspace isn’t `~/clawd`, pass `--memory-dir`, `--inbox`, and `--state`.
- Append an Open Loop to Apple Notes:
  - `./scripts/apple_notes_open_loops.sh "<text>"`

## Notes

- This is deliberately **staged** (no silent writes).
- Do not delete user notes in folder `Mo`.
