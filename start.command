#!/bin/sh
cd "$(dirname "$0")"
python3 start.py
status=$?
if [ "$status" -ne 0 ]; then
  echo
  echo "ForgeClaw stopped with an error (exit code $status)."
  read -r -p "Press Enter to close this window..." _
fi
exit "$status"
