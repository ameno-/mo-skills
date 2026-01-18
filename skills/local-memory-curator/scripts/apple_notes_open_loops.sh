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
on ensureFolder(folderName)
	tell application "Notes"
		repeat with f in folders
			if (name of f as text) is folderName then return f
		end repeat
		return make new folder with properties {name:folderName}
	end tell
end ensureFolder

on ensureNote(theFolder, noteName)
	tell application "Notes"
		repeat with n in notes of theFolder
			if (name of n as text) is noteName then return n
		end repeat
		return make new note at theFolder with properties {name:noteName, body:""}
	end tell
end ensureNote

set folderName to "Mo"
set noteName to "Mo Open Loops"
set entryText to "- [ ] " & "${STAMP}" & " — " & "${TEXT}" & return

tell application "Notes"
	set theFolder to ensureFolder(folderName)
	set theNote to ensureNote(theFolder, noteName)
	set oldBody to body of theNote as text
	set body of theNote to oldBody & entryText
end tell
OSA
