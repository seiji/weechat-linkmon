#!/usr/bin/osascript
on run argv
  tell application "Google Chrome"
    tell window 1
      set newTab to make new tab with properties {URL:item 1 of argv}
    end tell
  end tell
end run
