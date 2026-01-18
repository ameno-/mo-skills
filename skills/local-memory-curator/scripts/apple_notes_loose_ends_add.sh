#!/usr/bin/env bash
set -euo pipefail

# Append a new Loose End entry to Apple Notes.
# Folder: Mo
# Note:   loose ends
# Never deletes anything.

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"Task text...\"" >&2
  exit 2
fi

TEXT="$1"
STAMP="$(date "+%Y-%m-%d %I:%M %p")"
ID="LE-$(python3 - <<'PY'
import secrets
print(secrets.token_hex(3))
PY
)"

/usr/bin/osascript - "$ID" "$STAMP" "$TEXT" <<'OSA'
on run argv
	set itemId to item 1 of argv
	set stamp to item 2 of argv
	set taskText to item 3 of argv

	set folderName to "Mo"
	set noteName to "loose ends"
	set entryText to "- [ ] (" & itemId & ") " & taskText & " — added " & stamp & return

	tell application "Notes"
		set theFolder to missing value
		try
			set theFolder to first folder whose name is folderName
		on error
			set theFolder to make new folder with properties {name:folderName}
		end try

		set theNote to missing value
		try
			set theNote to first note of theFolder whose name is noteName
		on error
			set theNote to make new note at theFolder with properties {name:noteName, body:""}
		end try

		set oldBody to body of theNote as text
		set body of theNote to oldBody & entryText
	end tell
end run
OSA

echo "$ID"
