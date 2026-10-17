"""Configure only the generated native Gradle file; never embed key material."""
from pathlib import Path
import sys

MARKER = "// PASSWAY_STORE_SIGNING"
FRAGMENT = """
// PASSWAY_STORE_SIGNING
def passwaySigning = new groovy.json.JsonSlurper().parse(new File(System.getenv('PASSWAY_SIGNING_JSON')))
android {
  signingConfigs {
    passwayStore {
      storeFile file(System.getenv('PASSWAY_KEYSTORE_PATH'))
      storePassword passwaySigning.keystorePassword
      keyAlias passwaySigning.keyAlias
      keyPassword passwaySigning.keyPassword
    }
  }
  buildTypes { release { signingConfig signingConfigs.passwayStore } }
}
"""


def configure(path: Path) -> None:
    original = path.read_text()
    if MARKER in original:
        raise ValueError("Generated signing configuration is already present.")
    # Expo plugins can leave their final `apply plugin` line without a newline.
    # Always delimit the generated fragment, regardless of source EOF style.
    path.write_text(original.rstrip() + "\n\n" + FRAGMENT.lstrip())


if __name__ == "__main__":
    configure(Path(sys.argv[1]))