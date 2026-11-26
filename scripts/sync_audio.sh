#!/bin/sh
# Copy the pronunciation clips into the Worker's asset directory.
# audio/ stays the single source of truth at the repo root; the copy is gitignored.
set -e
cd "$(dirname "$0")/.."
rm -rf worker/public/audio
cp -R audio worker/public/audio
echo "synced $(find worker/public/audio -name '*.mp3' | wc -l | tr -d ' ') clips into worker/public/audio"
