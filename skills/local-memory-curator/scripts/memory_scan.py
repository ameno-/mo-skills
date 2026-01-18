#!/usr/bin/env python3

import argparse
import datetime as dt
import glob
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_SESSIONS_GLOB = os.path.expanduser("~/.clawdbot/agents/*/sessions/*.jsonl")

DEFAULT_MEMORY_DIR = os.path.expanduser("~/clawd/memory")
DEFAULT_INBOX_DIR = os.path.join(DEFAULT_MEMORY_DIR, "inbox")
DEFAULT_STATE_PATH = os.path.join(DEFAULT_MEMORY_DIR, "state.json")
DEFAULT_INBOX_PATH = os.path.join(DEFAULT_INBOX_DIR, "pending.jsonl")


@dataclass
class Candidate:
    id: str
    created_at: str
    type: str
    text: str
    source_session: str
    source_message_id: str
    source_timestamp: str
    source_quote: str
    actions: List[Dict[str, Any]]


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _load_state(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"cursors": {}, "seen_message_ids": {}, "candidates": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_state(path: str, state: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _iter_new_lines(path: str, start_offset: int) -> Tuple[int, Iterable[str]]:
    with open(path, "rb") as f:
        f.seek(start_offset)
        data = f.read()
        end_offset = f.tell()
    text = data.decode("utf-8", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return end_offset, lines


def _extract_user_text(msg: Dict[str, Any]) -> Optional[str]:
    # Log schema: {type:"message", message:{role, content:[{type,text}...]}}
    message = msg.get("message")
    if not isinstance(message, dict):
        return None
    if message.get("role") != "user":
        return None

    content = message.get("content")
    if not isinstance(content, list):
        return None

    parts: List[str] = []
    for c in content:
        if isinstance(c, dict) and c.get("type") == "text":
            t = c.get("text")
            if isinstance(t, str) and t.strip():
                parts.append(t.strip())
    if not parts:
        return None
    return "\n".join(parts).strip()


def _classify(text: str) -> Tuple[str, List[Dict[str, Any]]]:
    t = text.strip()
    lowered = t.lower()

    # Ignore harness/automation instructions that sometimes show up as user text.
    if lowered.startswith("read heartbeat.md") or lowered.startswith("system:"):
        return "unknown", []

    # High-signal rules/preferences.
    if re.search(r"\bcall me\b|\bmy name is\b|\bpreferred\b", lowered):
        return "preference", [{"kind": "commit_to_memory"}]
    if re.search(r"\balways\b|\bnever\b|\bdon't\b|\bdo not\b", lowered):
        return "rule", [{"kind": "commit_to_memory"}]

    # Open-loop / future work.
    if re.search(r"\bopen loop\b|\bwe should\b|\blater\b|\bnext\b|\bto-?do\b", lowered):
        return "open_loop", [{"kind": "add_open_loop"}]

    # Default fallback: treat as candidate only if it looks durable.
    if re.search(r"\bdefault\b|\bgoing with\b|\bdecide\b|\bdecision\b", lowered):
        return "decision", [{"kind": "commit_to_memory"}]

    return "unknown", []


def _should_propose(candidate_type: str, actions: List[Dict[str, Any]]) -> bool:
    # Only stage things that have a clear action.
    return candidate_type != "unknown" and len(actions) > 0


def scan(sessions_glob: str, memory_dir: str, inbox_path: str, state_path: str) -> List[Candidate]:
    state = _load_state(state_path)
    cursors: Dict[str, int] = state.get("cursors", {})
    seen_message_ids: Dict[str, bool] = state.get("seen_message_ids", {})

    candidates: List[Candidate] = []

    for path in sorted(glob.glob(sessions_glob)):
        session_id = os.path.basename(path)
        start = int(cursors.get(path, 0))
        end, lines = _iter_new_lines(path, start)
        cursors[path] = end

        for ln in lines:
            try:
                obj = json.loads(ln)
            except Exception:
                continue

            if obj.get("type") != "message":
                continue

            msg_id = obj.get("id")
            if not isinstance(msg_id, str) or not msg_id:
                continue
            if seen_message_ids.get(msg_id):
                continue

            text = _extract_user_text(obj)
            if not text:
                continue

            cand_type, actions = _classify(text)
            if not _should_propose(cand_type, actions):
                seen_message_ids[msg_id] = True
                continue

            cand_id = f"cand_{msg_id}"
            created_at = _now_iso()
            candidates.append(
                Candidate(
                    id=cand_id,
                    created_at=created_at,
                    type=cand_type,
                    text=text,
                    source_session=session_id,
                    source_message_id=msg_id,
                    source_timestamp=str(obj.get("timestamp", "")),
                    source_quote=text[:240],
                    actions=actions,
                )
            )

            # Mark seen so we don't propose repeatedly.
            seen_message_ids[msg_id] = True

    # Persist state
    state["cursors"] = cursors
    state["seen_message_ids"] = seen_message_ids
    _save_state(state_path, state)

    if candidates:
        os.makedirs(os.path.dirname(inbox_path), exist_ok=True)
        with open(inbox_path, "a", encoding="utf-8") as f:
            for c in candidates:
                f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

    return candidates


def list_pending(inbox_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(inbox_path):
        return []
    out: List[Dict[str, Any]] = []
    with open(inbox_path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan Clawdbot session logs and stage memory candidates.")
    ap.add_argument("--sessions-glob", default=DEFAULT_SESSIONS_GLOB)
    ap.add_argument("--memory-dir", default=DEFAULT_MEMORY_DIR)
    ap.add_argument("--inbox", default=DEFAULT_INBOX_PATH)
    ap.add_argument("--state", default=DEFAULT_STATE_PATH)
    ap.add_argument("--write", action="store_true", help="Scan and append new candidates to inbox")
    ap.add_argument("--list", action="store_true", help="List pending candidates")
    args = ap.parse_args()

    if args.list:
        pending = list_pending(args.inbox)
        print(json.dumps(pending, ensure_ascii=False, indent=2))
        return 0

    if args.write:
        cands = scan(args.sessions_glob, args.memory_dir, args.inbox, args.state)
        print(json.dumps([asdict(c) for c in cands], ensure_ascii=False, indent=2))
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
