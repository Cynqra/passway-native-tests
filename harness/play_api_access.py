"""Keyless Play capability check. No upload, track mutation, or release commit."""
import argparse
import base64
import json
import os
import re
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

PROJECT = "passway-release-2026"
NUMBER = "809880084764"
SERVICE_ACCOUNT = f"passway-play-internal@{PROJECT}.iam.gserviceaccount.com"
PROVIDER = (
    f"projects/{NUMBER}/locations/global/workloadIdentityPools/"
    "passway-github/providers/github-internal"
)
REPOSITORY = "Cynqra/passway-native-tests"
REF = "refs/heads/validation/isolated-current-native"
WORKFLOW_REF = f"{REPOSITORY}/.github/workflows/passway-fresh-native-smoke.yml@{REF}"
PUBLISHER = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/com.passway.app/edits"


class SafeError(RuntimeError):
    """Messages must never contain tokens, response bodies, or request headers."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise SafeError("Unexpected redirect rejected")


def safe_http_error(url, code, raw):
    host = urllib.parse.urlsplit(url).hostname
    operation = {
        "sts.googleapis.com": "Google federation exchange",
        "iamcredentials.googleapis.com": "Service-account delegation",
        "androidpublisher.googleapis.com": "Play capability check",
    }.get(host, "GitHub OIDC request")
    reason = ""
    try:
        data = json.loads(raw)
        value = data.get("error", "")
        enum = value.get("status", "") if isinstance(value, dict) else value
        if isinstance(enum, str) and re.fullmatch(r"[A-Za-z_]{1,48}", enum):
            reason = "; " + enum
        description = str(data.get("error_description", "")).lower()
        for marker, classification in (
            ("attribute condition", "identity rejected by trust condition"),
            ("audience", "audience configuration rejected"),
            ("invalid json payload", "request schema rejected"),
            ("disabled", "provider or API disabled"),
            ("not found", "identity configuration not found"),
            ("subject token", "subject-token validation failed"),
        ):
            if marker in description:
                reason += "; " + classification
                break
    except (ValueError, TypeError, AttributeError):
        pass
    return SafeError(f"{operation} rejected request (HTTP {code}{reason})")


def request(url, method="GET", headers=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    hdr = dict(headers or {})
    if data is not None:
        hdr["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdr, method=method)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=25) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise SafeError("Response exceeded size limit")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise safe_http_error(url, exc.code, exc.read(65536)) from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise SafeError("API transport or JSON validation failed") from None


def validate_context(env):
    expected = {
        "GITHUB_REPOSITORY": REPOSITORY,
        "GITHUB_REPOSITORY_ID": "1419569453",
        "GITHUB_REPOSITORY_OWNER_ID": "338663904",
        "GITHUB_REF": REF,
        "GITHUB_WORKFLOW_REF": WORKFLOW_REF,
        "GITHUB_EVENT_NAME": "workflow_dispatch",
    }
    if any(env.get(k) != v for k, v in expected.items()):
        raise SafeError("Untrusted repository, owner, branch, workflow, or event")
    url = env.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(".actions.githubusercontent.com")
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
        or parsed.fragment
        or not env.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    ):
        raise SafeError("Invalid GitHub OIDC endpoint or missing token permission")
    return url


def required_token(response, field):
    value = response.get(field)
    if not isinstance(value, str) or not value:
        raise SafeError("Token response is missing its required field")
    return value


def access_token(env, send=request):
    url = validate_context(env)
    parts = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    query = [(k, v) for k, v in query if k != "audience"]
    query.append(("audience", "https://iam.googleapis.com/" + PROVIDER))
    oidc_url = urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))
    oidc = send(
        oidc_url,
        headers={"Authorization": "Bearer " + env["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]},
    )
    if env.get("PASSWAY_OIDC_DIAGNOSTICS") == "1":
        # Public identity metadata only; never log the JWT/signature or arbitrary claims.
        # Decoding here is diagnostic, NOT signature validation; Google STS validates it.
        try:
            part = required_token(oidc, "value").split(".")[1]
            metadata = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
            allowed = (
                "iss", "sub", "aud", "repository", "repository_id",
                "repository_owner_id", "ref", "workflow_ref", "environment",
            )
            print(json.dumps({"githubOidcIdentity": {k: metadata.get(k) for k in allowed}}))
        except (ValueError, IndexError, TypeError):
            raise SafeError("OIDC identity metadata could not be decoded") from None
    sts = send(
        "https://sts.googleapis.com/v1/token",
        method="POST",
        body={
            "audience": "//iam.googleapis.com/" + PROVIDER,
            "grantType": "urn:ietf:params:oauth:grant-type:token-exchange",
            "requestedTokenType": "urn:ietf:params:oauth:token-type:access_token",
            "subjectTokenType": "urn:ietf:params:oauth:token-type:jwt",
            "subjectToken": required_token(oidc, "value"),
            "scope": "https://www.googleapis.com/auth/cloud-platform",
        },
    )
    delegated = send(
        "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
        + SERVICE_ACCOUNT
        + ":generateAccessToken",
        method="POST",
        headers={"Authorization": "Bearer " + required_token(sts, "access_token")},
        body={
            "scope": ["https://www.googleapis.com/auth/androidpublisher"],
            "lifetime": "900s",
        },
    )
    return required_token(delegated, "accessToken")


def probe(token, send=request):
    headers = {"Authorization": "Bearer " + token}
    edit = send(PUBLISHER, method="POST", headers=headers, body={}).get("id")
    if not isinstance(edit, str) or not edit.isdigit():
        raise SafeError("Play edit response did not contain a valid identifier")
    try:
        tracks = send(PUBLISHER + "/" + edit + "/tracks", headers=headers)
        report = {
            "package": "com.passway.app",
            "authentication": "GitHub OIDC federation; 15-minute delegated token; no JSON key",
            "authorized": True,
            "tracks": sorted(x["track"] for x in tracks.get("tracks", [])),
            "scope": "Temporary edit/read/delete only; no bundle upload, release changes, or commit",
        }
        internal = next(
            (x for x in tracks.get("tracks", []) if x.get("track") == "internal"), {}
        )
        report["internalReleases"] = [
            {
                "name": release.get("name"),
                "status": release.get("status"),
                "versionCodes": release.get("versionCodes", []),
            }
            for release in internal.get("releases", [])
        ]
        report["publicProductionReleasePresent"] = any(
            x.get("track") == "production" and bool(x.get("releases"))
            for x in tracks.get("tracks", [])
        )
    finally:
        send(PUBLISHER + "/" + edit, method="DELETE", headers=headers)
    report["temporaryEditDeleted"] = True
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="play-api-access.json")
    args = parser.parse_args()
    try:
        report = probe(access_token(os.environ))
    except Exception as exc:
        # Deliberately never stringify arbitrary exceptions or HTTP response bodies.
        report = {
            "authorized": False,
            "error": str(exc) if isinstance(exc, SafeError) else type(exc).__name__,
            "scope": "No upload, release mutation, or commit attempted",
        }
        Path(args.output).write_text(json.dumps(report, indent=2))
        print(json.dumps(report))
        return 1
    Path(args.output).write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())