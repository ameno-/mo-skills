#!/usr/bin/env python3

import argparse
import datetime as dt
import json
import os
import subprocess
from typing import Any, Dict, List, Optional


DEFAULT_MEMORY_DIR = os.path.expanduser("~/clawd/memory")
DEFAULT_INBOX_PATH = os.path.join(DEFAULT_MEMORY_DIR, "inbox", "pending.jsonl")


def _today_path(memory_dir: str) -> str:
    return os.path.join(memory_dir, dt.date.today().isoformat() + ".md")


def _load_pending(inbox_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(inbox_path):
        return []
    items: List[Dict[str, Any]] = []
    with open(inbox_path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                items.append(json.loads(ln))
            except Exception:
                continue
    return items


def _write_pending(inbox_path: str, items: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(inbox_path), exist_ok=True)
    tmp = inbox_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    os.replace(tmp, inbox_path)


def _append_memory(memory_dir: str, item: Dict[str, Any], status: str) -> None:
    os.makedirs(memory_dir, exist_ok=True)
    path = _today_path(memory_dir)
    stamp = dt.datetime.now().strftime("%Y-%m-%d %I:%M %p")

    header = f"\n## {stamp} — {item.get('type','unknown')} ({status})\n"
    body = f"- {item.get('text','').strip()}\n"
    src = f"- source: {item.get('source_session')} {item.get('source_message_id')}\n"

    with open(path, "a", encoding="utf-8") as f:
        f.write(header)
        f.write(body)
        f.write(src)


def _append_open_loop(text: str) -> None:
    # Use the bundled Apple Notes script.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sh = os.path.join(script_dir, "apple_notes_open_loops.sh")
    subprocess.check_call([sh, text])


def apply_action(item: Dict[str, Any]) -> None:
    actions = item.get("actions") or []
    if not isinstance(actions, list):
        return

    for a in actions:
        if not isinstance(a, dict):
            continue
        kind = a.get("kind")
        if kind == "add_open_loop":
            _append_open_loop(item.get("text", ""))


def main() -> int:
    ap = argparse.ArgumentParser(description="Approve/reject staged memory items.")
    ap.add_argument("action", choices=["approve", "reject"], help="What to do")
    ap.add_argument("id", help="Candidate id")
    ap.add_argument("--memory-dir", default=DEFAULT_MEMORY_DIR)
    ap.add_argument("--inbox", default=DEFAULT_INBOX_PATH)
    args = ap.parse_args()

    pending = _load_pending(args.inbox)
    keep: List[Dict[str, Any]] = []
    target: Optional[Dict[str, Any]] = None

    for it in pending:
        if it.get("id") == args.id and target is None:
            target = it
        else:
            keep.append(it)

    if not target:
        raise SystemExit(f"No such pending candidate: {args.id}")

    status = args.action
    _append_memory(args.memory_dir, target, status)

    if status == "approve":
        apply_action(target)

    _write_pending(args.inbox, keep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
