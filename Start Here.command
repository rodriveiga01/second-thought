#!/bin/bash
# Double-click this file to run the Second Thought check-up.
# (If macOS asks, right-click it and choose Open.)
cd "$(dirname "$0")"
./second-thought test
echo ""
echo "You can close this window now."
read -r -p "Press Enter to close. "
exit 0
