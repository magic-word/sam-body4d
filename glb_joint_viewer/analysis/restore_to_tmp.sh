#!/bin/bash
# Restores the analysis data + scripts to /tmp so the pipeline scripts
# (which reference absolute /tmp paths) run as-is after a reboot wipes /tmp.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$DIR"/data/*.json /tmp/
cp "$DIR"/*.py /tmp/
echo "Restored $(ls "$DIR"/data/*.json | wc -l | tr -d ' ') data files + $(ls "$DIR"/*.py | wc -l | tr -d ' ') scripts to /tmp"
echo "Now you can run e.g.:  python3 /tmp/crosscheck2.py"
