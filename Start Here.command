#!/bin/bash
# Double-click this file to run the TimeCop check-up.
# (If macOS asks, right-click it and choose Open.)
cd "$(dirname "$0")"
./timecop-cli test
echo ""
echo "You can close this window now."
read -r -p "Press Enter to close. "
exit 0
