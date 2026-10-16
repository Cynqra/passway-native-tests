"""Bind a signed candidate's version to its immutable source, never a filename."""
import json
import pathlib
import re
import sys


def metadata(config, provenance):
    android = config.get("android", {})
    code = android.get("versionCode")
    version = config.get("version")
    if android.get("package") != "com.passway.app":
        raise ValueError("Unexpected Android package")
    if type(code) is not int or not 1 <= code <= 2100000000:
        raise ValueError("Invalid Android version code")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Invalid release version")
    if provenance.get("sourceRepository") != "naveenbharti310/Paasway":
        raise ValueError("Unexpected source repository")
    if not re.fullmatch(r"[a-f0-9]{40}", provenance.get("sourceCommit", "")):
        raise ValueError("Invalid source commit")
    if not re.fullmatch(r"[a-f0-9]{64}", provenance.get("archiveSha256", "")):
        raise ValueError("Invalid source archive hash")
    return {
        "package": android["package"],
        "versionCode": code,
        "versionName": version,
        "sourceCommit": provenance["sourceCommit"],
        "sourceArchiveSha256": provenance["archiveSha256"],
        "scope": "Signed candidate only; no store installation, attestation or rollout proof",
    }


if __name__ == "__main__":
    config, provenance, output = map(pathlib.Path, sys.argv[1:4])
    output.write_text(json.dumps(metadata(json.loads(config.read_text()),
                                         json.loads(provenance.read_text())), indent=2) + "\n")