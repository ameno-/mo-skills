#!/usr/bin/env python3

import argparse
import glob
import json
import os
import re
import subprocess
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_SESSIONS_GLOB = os.path.expanduser("~/.clawdbot/agents/*/sessions/*.jsonl")
DEFAULT_INBOX_PATH = os.path.expanduser("~/clawd/memory/inbox/pending.jsonl")
DEFAULT_MEMORY_DIR = os.path.expanduser("~/clawd/memory")
DEFAULT_STATE_PATH = os.path.expanduser("~/clawd/memory/state.json")

# Commands accepted from the user in chat.
# Examples:
#   approve cand_deadbeef
#   reject cand_deadbeef
#   edit cand_deadbeef: new text here
CMD_RE = re.compile(r"^(approve|reject|edit)\s+(cand_[a-zA-Z0-9]+)(?::\s*(.*))?$", re.IGNORECASE)
INLINE_CMD_RE = re.compile(r"\b(approve|reject|edit)\s+(cand_[a-zA-Z0-9]+)(?::\s*([^\n]+))?\b", re.IGNORECASE)
CAND_ID_RE = re.compile(r"\bid:\s*(cand_[a-zA-Z0-9]+)\b", re.IGNORECASE)


def _load_state(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"approval_cursors": {}, "seen_approval_msgs": {}}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {"approval_cursors": {}, "seen_approval_msgs": {}}


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


def _load_pending_ids(inbox_path: str) -> set:
    ids = set()
    if not os.path.exists(inbox_path):
        return ids
    with open(inbox_path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
            except Exception:
                continue
            cid = obj.get("id")
            if isinstance(cid, str):
                ids.add(cid)
    return ids


def _edit_candidate(inbox_path: str, cand_id: str, new_text: str) -> None:
    if not os.path.exists(inbox_path):
        raise SystemExit("No pending inbox file")

    items: List[Dict[str, Any]] = []
    found = False
    with open(inbox_path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
            except Exception:
                continue
            if obj.get("id") == cand_id:
                obj["text"] = new_text
                found = True
            items.append(obj)

    if not found:
        raise SystemExit(f"No such candidate to edit: {cand_id}")

    tmp = inbox_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    os.replace(tmp, inbox_path)


def _apply(memory_dir: str, inbox_path: str, action: str, cand_id: str) -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    apply_py = os.path.join(script_dir, "memory_apply.py")
    subprocess.check_call(
        [
            "python3",
            apply_py,
            action.lower(),
            cand_id,
            "--memory-dir",
            memory_dir,
            "--inbox",
            inbox_path,
        ]
    )


def watch(
    sessions_glob: str,
    inbox_path: str,
    memory_dir: str,
    state_path: str,
    once: bool,
) -> int:
    state = _load_state(state_path)
    cursors: Dict[str, int] = state.get("approval_cursors", {})
    seen: Dict[str, bool] = state.get("seen_approval_msgs", {})

    pending_ids = _load_pending_ids(inbox_path)
    if not pending_ids:
        return 0

    def scan_once() -> int:
        nonlocal pending_ids
        applied = 0

        for path in sorted(glob.glob(sessions_glob)):
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
                if seen.get(msg_id):
                    continue

                text = _extract_user_text(obj)
                if not text:
                    continue

                # Accept commands in a few forms:
                # - "approve cand_..."
                # - Inlined inside a larger reply blob
                # - Bare "Approve" when the reply quotes our candidate message (contains "id: cand_...")
                cmd = None
                cand_id = None
                rest = ""

                for line in text.splitlines():
                    m1 = CMD_RE.match(line.strip())
                    if m1:
                        cmd = m1.group(1).lower()
                        cand_id = m1.group(2)
                        rest = (m1.group(3) or "").strip()
                        break

                if cmd is None:
                    m2 = INLINE_CMD_RE.search(text)
                    if m2:
                        cmd = m2.group(1).lower()
                        cand_id = m2.group(2)
                        rest = (m2.group(3) or "").strip()

                if cmd is None:
                    # Special case: user replies "Approve" without id, but includes our quoted candidate block.
                    if re.search(r"\bapprove\b", text, re.IGNORECASE):
                        m3 = CAND_ID_RE.search(text)
                        if m3:
                            cmd = "approve"
                            cand_id = m3.group(1)

                if cmd is None or cand_id is None:
                    continue

                if cand_id not in pending_ids:
                    seen[msg_id] = True
                    continue

                if cmd == "edit":
                    if not rest:
                        seen[msg_id] = True
                        continue
                    _edit_candidate(inbox_path, cand_id, rest)
                    # After edit, do not auto-approve; user can approve explicitly.
                    applied += 1
                elif cmd in {"approve", "reject"}:
                    _apply(memory_dir, inbox_path, cmd, cand_id)
                    applied += 1
                    pending_ids = _load_pending_ids(inbox_path)

                seen[msg_id] = True

        state["approval_cursors"] = cursors
        state["seen_approval_msgs"] = seen
        _save_state(state_path, state)
        return applied

    if once:
        scan_once()
        return 0

    # Simple loop mode (for background runner). Keep it conservative.
    import time

    while True:
        scan_once()
        time.sleep(2.0)


def main() -> int:
    ap = argparse.ArgumentParser(description="Watch session logs for approve/reject/edit commands.")
    ap.add_argument("--sessions-glob", default=DEFAULT_SESSIONS_GLOB)
    ap.add_argument("--inbox", default=DEFAULT_INBOX_PATH)
    ap.add_argument("--memory-dir", default=DEFAULT_MEMORY_DIR)
    ap.add_argument("--state", default=DEFAULT_STATE_PATH)
    ap.add_argument("--once", action="store_true", help="Run one scan and exit")
    args = ap.parse_args()

    return watch(
        sessions_glob=args.sessions_glob,
        inbox_path=args.inbox,
        memory_dir=args.memory_dir,
        state_path=args.state,
        once=args.once,
    )


if __name__ == "__main__":
    raise SystemExit(main())
