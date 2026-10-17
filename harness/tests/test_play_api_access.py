import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "play_api_access", Path(__file__).parents[1] / "play_api_access.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def env():
    return {
        "GITHUB_REPOSITORY": m.REPOSITORY,
        "GITHUB_REPOSITORY_ID": "1419569453",
        "GITHUB_REPOSITORY_OWNER_ID": "338663904",
        "GITHUB_REF": m.REF,
        "GITHUB_WORKFLOW_REF": m.WORKFLOW_REF,
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "ACTIONS_ID_TOKEN_REQUEST_URL": "https://pipelines.actions.githubusercontent.com/token?api-version=2",
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "fictional-test-token",
    }


class PlayAccessTests(unittest.TestCase):
    def test_trusted_context(self):
        self.assertTrue(m.validate_context(env()).startswith("https://"))

    def test_every_identity_boundary_rejected_before_network(self):
        for key in (
            "GITHUB_REPOSITORY", "GITHUB_REPOSITORY_ID", "GITHUB_REPOSITORY_OWNER_ID",
            "GITHUB_REF", "GITHUB_WORKFLOW_REF", "GITHUB_EVENT_NAME",
        ):
            with self.subTest(key=key):
                data = env()
                data[key] = "untrusted"
                with self.assertRaises(m.SafeError):
                    m.access_token(data, lambda *a, **k: self.fail("Network called"))

    def test_oidc_endpoint_boundaries(self):
        for url in (
            "http://pipelines.actions.githubusercontent.com/token",
            "https://evil.example/token",
            "https://actions.githubusercontent.com.evil.example/token",
            "https://x.actions.githubusercontent.com:444/token",
            "https://user:password@x.actions.githubusercontent.com/token",
            "https://x.actions.githubusercontent.com/token#fragment",
        ):
            with self.subTest(url=url):
                data = env()
                data["ACTIONS_ID_TOKEN_REQUEST_URL"] = url
                with self.assertRaises(m.SafeError):
                    m.validate_context(data)

    def test_missing_oidc_permission_rejected(self):
        data = env()
        del data["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
        with self.assertRaises(m.SafeError):
            m.validate_context(data)

    def test_exchange_has_fixed_audience_scope_and_short_lifetime(self):
        calls = []
        def send(url, **kwargs):
            calls.append((url, kwargs))
            return [{"value": "fictional-oidc"}, {"access_token": "fictional-sts"},
                    {"accessToken": "fictional-delegated"}][len(calls) - 1]
        self.assertEqual(m.access_token(env(), send), "fictional-delegated")
        self.assertIn(m.PROVIDER, calls[1][1]["body"]["audience"])
        self.assertEqual(calls[2][1]["body"]["lifetime"], "900s")
        self.assertEqual(calls[2][1]["body"]["scope"],
                         ["https://www.googleapis.com/auth/androidpublisher"])

    def test_empty_token_fails_closed(self):
        with self.assertRaises(m.SafeError):
            m.access_token(env(), lambda *a, **k: {})

    def test_probe_only_creates_reads_deletes(self):
        calls = []
        def send(url, **kwargs):
            calls.append((url, kwargs.get("method", "GET")))
            if len(calls) == 1:
                return {"id": "123"}
            return {"tracks": [{"track": "internal"}]}
        report = m.probe("fictional-token", send)
        self.assertEqual([x[1] for x in calls], ["POST", "GET", "DELETE"])
        self.assertTrue(report["temporaryEditDeleted"])
        self.assertFalse(any("commit" in x[0] for x in calls))

    def test_cleanup_even_when_track_read_fails(self):
        calls = []
        def send(url, **kwargs):
            calls.append(kwargs.get("method", "GET"))
            if len(calls) == 1:
                return {"id": "123"}
            if len(calls) == 2:
                raise m.SafeError("Read rejected")
            return {}
        with self.assertRaises(m.SafeError):
            m.probe("fictional-token", send)
        self.assertEqual(calls, ["POST", "GET", "DELETE"])

    def test_release_status_evidence_is_internal_and_read_only(self):
        calls = []
        def send(url, **kwargs):
            calls.append(kwargs.get("method", "GET"))
            if len(calls) == 1:
                return {"id": "123"}
            if len(calls) == 2:
                return {"tracks": [
                    {"track": "internal", "releases": [
                        {"name": "Internal six", "status": "completed", "versionCodes": ["6"]}
                    ]},
                    {"track": "production", "releases": []},
                ]}
            return {}
        report = m.probe("fictional-token", send)
        self.assertEqual(report["internalReleases"][0]["versionCodes"], ["6"])
        self.assertFalse(report["publicProductionReleasePresent"])
        self.assertEqual(calls, ["POST", "GET", "DELETE"])

    def test_invalid_edit_identifier_rejected(self):
        with self.assertRaises(m.SafeError):
            m.probe("fictional-token", lambda *a, **k: {"id": "../unexpected"})

    def test_redirects_never_forward_bearer(self):
        with self.assertRaises(m.SafeError):
            m.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example")

    def test_error_diagnostics_classify_without_echoing_response_or_tokens(self):
        error = m.safe_http_error(
            "https://sts.googleapis.com/v1/token", 400,
            '{"error":"invalid_grant","error_description":"The given credential is rejected by the attribute condition. secret-token-example"}',
        )
        self.assertIn("Google federation exchange", str(error))
        self.assertIn("trust condition", str(error))
        self.assertNotIn("secret-token-example", str(error))

    def test_untrusted_error_fields_are_not_logged(self):
        error = m.safe_http_error(
            "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/test:generateAccessToken",
            403, '{"error":{"status":"SECRET-WITH-HYPHENS","message":"private-response"}}',
        )
        self.assertNotIn("SECRET-WITH-HYPHENS", str(error))
        self.assertNotIn("private-response", str(error))

    def test_production_draft_is_not_reported_as_public_release(self):
        def send(url, **kwargs):
            if url == m.PUBLISHER:return {"id":"123"}
            return {"tracks":[{"track":"production","releases":[{"status":"draft","versionCodes":["13"]}]}]}
        r=m.probe("fictional",send)
        self.assertFalse(r["publicProductionReleasePresent"])
        self.assertEqual(r["productionReleases"],[{"status":"draft","versionCodes":["13"]}])

    def test_independent_store_readback_checks_exact_candidate_and_assets(self):
        from public_store_assets import load_assets
        from public_release_preflight import BUNDLE_SHA
        from public_release_draft import FULL,SHORT
        calls=[];assets=load_assets()
        def send(url, **kwargs):
            calls.append(kwargs.get("method","GET"))
            if url==m.PUBLISHER:return {"id":"123"}
            if url.endswith("/bundles"):return {"bundles":[{"versionCode":13,"sha256":BUNDLE_SHA}]}
            if url.endswith("/listings/en-US"):return {"title":"Passway","shortDescription":SHORT,"fullDescription":FULL}
            for kind in ("icon","featureGraphic","phoneScreenshots"):
                if url.endswith("/"+kind):return {"images":[{"sha256":r["sha256"]} for r,d in assets if r["kind"]==kind]}
            return {"tracks":[{"track":"production","releases":[{"status":"draft","versionCodes":["13"]}]}]}
        r=m.probe("fictional",send,store_readback=True)
        self.assertTrue(r["storeAssetsReadbackVerified"]);self.assertTrue(r["listingTextVerified"])
        self.assertEqual(r["imageCounts"],dict(icon=1,featureGraphic=1,phoneScreenshots=6))
        self.assertEqual(calls[0],"POST");self.assertEqual(calls[-1],"DELETE");self.assertNotIn("PUT",calls)


if __name__ == "__main__":
    unittest.main()