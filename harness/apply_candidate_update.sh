#!/usr/bin/env bash
# Warm repair hook: replace only a changed test JavaScript candidate, retaining
# the running emulator, Android users, signing key and saved app data.
set -eu
if [ "${PASSWAY_ATTEMPT:-0}" = 0 ] || [ ! -f harness/candidate/index.android.bundle ]; then exit 0; fi
NEW=$(sha256sum harness/candidate/index.android.bundle | cut -d' ' -f1)
OLD=$(python3 -c 'import zipfile,hashlib;print(hashlib.sha256(zipfile.ZipFile("universal.apk").read("assets/index.android.bundle")).hexdigest())')
if [ "$NEW" = "$OLD" ]; then exit 0; fi
python3 harness/assemble_candidate.py
TOOLS=$(find "$ANDROID_HOME/build-tools" -name apksigner -printf '%h\n' | sort -V | tail -1)
"$TOOLS/apksigner" sign --ks debug.keystore --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out universal.apk candidate-unsigned.apk
"$TOOLS/apksigner" verify universal.apk
adb install --no-incremental -r universal.apk
python3 harness/status.py candidate_bytecode_updated
