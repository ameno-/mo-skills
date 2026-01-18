#!/usr/bin/env bash
set -euo pipefail

# Mark a Loose End as complete in Apple Notes.
# Folder: Mo
# Note:   loose ends
# Edits checklist line in-place and appends completion metadata.

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <LE-id> [note]" >&2
  exit 2
fi

LE_ID="$1"
NOTE="${2:-}"
STAMP="$(date "+%Y-%m-%d %I:%M %p")"

/usr/bin/osascript - "$LE_ID" "$STAMP" "$NOTE" <<'OSA'
on run argv
	set targetId to item 1 of argv
	set doneStamp to item 2 of argv
	set doneNote to item 3 of argv

	set folderName to "Mo"
	set noteName to "loose ends"

	tell application "Notes"
		set theFolder to first folder whose name is folderName
		set theNote to first note of theFolder whose name is noteName
		set b to body of theNote as text
	end tell

	set ls to paragraphs of b
	set outLines to {}
	set changed to false

	repeat with ln in ls
		set s to (ln as text)
		if s contains "(" & targetId & ")" then
			if s starts with "- [ ]" then
				set s to "- [x]" & text 6 thru -1 of s
			end if
			if doneNote is not "" then
				set s to s & " — done " & doneStamp & " (" & doneNote & ")"
			else
				set s to s & " — done " & doneStamp
			end if
			set changed to true
		end if
		set end of outLines to s
	end repeat

	if changed then
		set AppleScript's text item delimiters to return
		set newBody to outLines as text
		set AppleScript's text item delimiters to ""
		tell application "Notes"
			set theFolder to first folder whose name is folderName
			set theNote to first note of theFolder whose name is noteName
			set body of theNote to newBody
		end tell
	else
		error "No matching item for " & targetId
	end if
end run
OSA
