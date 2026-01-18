#!/usr/bin/env bash
set -euo pipefail

# Append an Open Loop entry to Apple Notes.
# Folder: Mo
# Note:   Mo Open Loops
# Never deletes anything.

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"Open loop text...\"" >&2
  exit 2
fi

TEXT="$1"
STAMP="$(date "+%Y-%m-%d %I:%M %p")"

/usr/bin/osascript <<OSA
set folderName to "Mo"
set noteName to "Mo Open Loops"
set entryText to "- [ ] " & "${STAMP}" & " — " & "${TEXT}" & return

tell application "Notes"
	-- Folder
	set theFolder to missing value
	try
		set theFolder to first folder whose name is folderName
	on error
		set theFolder to make new folder with properties {name:folderName}
	end try

	-- Note
	set theNote to missing value
	try
		set theNote to first note of theFolder whose name is noteName
	on error
		set theNote to make new note at theFolder with properties {name:noteName, body:""}
	end try

	set oldBody to body of theNote as text
	set body of theNote to oldBody & entryText
end tell
OSA
