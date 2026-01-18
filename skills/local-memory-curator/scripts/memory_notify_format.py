#!/usr/bin/env python3

import argparse
import json
import os
from typing import Any, Dict, List


DEFAULT_INBOX_PATH = os.path.expanduser("~/clawd/memory/inbox/pending.jsonl")


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


def _format_candidate(item: Dict[str, Any]) -> str:
    cid = item.get("id", "")
    ctype = item.get("type", "unknown")
    text = (item.get("text") or "").strip()
    actions = item.get("actions") or []

    action_words = []
    if isinstance(actions, list):
        for a in actions:
            if isinstance(a, dict) and a.get("kind"):
                action_words.append(str(a["kind"]))

    action_line = ", ".join(action_words) if action_words else "(none)"

    return (
        "MEMORY CANDIDATE 🧬\n"
        f"id: {cid}\n"
        f"type: {ctype}\n"
        f"action: {action_line}\n\n"
        f"{text}\n\n"
        "Reply with one of:\n"
        f"- approve {cid}\n"
        f"- reject {cid}\n"
        f"- edit {cid}: <new text>"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Format a staged memory candidate as a WhatsApp message.")
    ap.add_argument("id", nargs="?", help="Candidate id to format (defaults to first pending)")
    ap.add_argument("--inbox", default=DEFAULT_INBOX_PATH)
    args = ap.parse_args()

    pending = _load_pending(args.inbox)
    if not pending:
        print("(no pending candidates)")
        return 0

    if args.id:
        for it in pending:
            if it.get("id") == args.id:
                print(_format_candidate(it))
                return 0
        raise SystemExit(f"No such candidate: {args.id}")

    print(_format_candidate(pending[0]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
