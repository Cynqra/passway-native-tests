set -eu
ROOT=harness/probe
ANDROID_JAR=$(find "$ANDROID_HOME/platforms" -name android.jar | sort -V | tail -1)
TOOLS=$(find "$ANDROID_HOME/build-tools" -name aapt -printf '%h\n' | sort -V | tail -1)
mkdir -p "$ROOT/classes" "$ROOT/dex"
javac -source 8 -target 8 -cp "$ANDROID_JAR" -d "$ROOT/classes" "$ROOT/Probe.java"
"$TOOLS/d8" --lib "$ANDROID_JAR" --output "$ROOT/dex" "$ROOT/classes/com/passway/nativeprobe/Probe.class"
"$TOOLS/aapt" package -f -M "$ROOT/AndroidManifest.xml" -I "$ANDROID_JAR" -F "$ROOT/probe-unsigned.apk"
(cd "$ROOT/dex" && zip -q ../probe-unsigned.apk classes.dex)
"$TOOLS/apksigner" sign --ks debug.keystore --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out "$ROOT/probe.apk" "$ROOT/probe-unsigned.apk"

# Preserve IME configuration when a warm repair follows a keyboard visibility failure.
if [ "${PASSWAY_ATTEMPT:-0}" -ge 4 ]; then
 mkdir -p native-attempts
 adb shell dumpsys input_method > native-attempts/ime-state.txt
 adb shell ime list -a > native-attempts/ime-list.txt
 adb shell settings get secure default_input_method > native-attempts/ime-default.txt
 adb shell getprop ro.hardware.keyboard > native-attempts/ime-hardware.txt
fi
# Candidate updates are applied only when their verified bytecode hash changed.
bash harness/apply_candidate_update.sh
