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
