# Passway: browser-independent Google Play access

## Established identity
- Dedicated project: `passway-release-2026` (`809880084764`). Billing explicitly unlinked and verified disabled after the Console automatically inherited an existing billing link at project creation. No paid runtime resources were created.
- Service account: `passway-play-internal@passway-release-2026.iam.gserviceaccount.com`.
- No user-managed service-account keys; no project-wide Cloud IAM roles.
- Play Console: active, non-expiring, **Passway only**. App information/quality read access and testing-track releases. No production publishing, financial, administration, or account-wide permissions.
- Provider: `projects/809880084764/locations/global/workloadIdentityPools/passway-github/providers/github-internal`.
- GitHub environment: `passway-play-internal`, restricted to `validation/isolated-current-native`.

Google verifies the issuer and an exact condition combining immutable repository ID `1419569453`, owner ID `338663904`, trusted branch, specific workflow path, and protected environment subject. This repository issues the ID-bearing subject:

```
repo:Cynqra@338663904/passway-native-tests@1419569453:environment:passway-play-internal
```

Do not replace that with the legacy `repo:owner/repository:environment:...` format. Do not remove trust restrictions to fix a failed exchange.

## Routine verification (no Google browser login)

```
gh workflow run passway-fresh-native-smoke.yml \
  -R Cynqra/passway-native-tests \
  --ref validation/isolated-current-native \
  -f mode=play-api-check
```

Only the API-check job receives `id-token: write`. It exchanges a GitHub OIDC token with Google STS, then requests a 900-second delegated token scoped to `androidpublisher`. No exported credential file or Google password is used. The check opens an isolated Play edit, reads track status, and deletes the edit, including on read failure. It does not upload, update a track, commit an edit, or publish a release. Its sanitized artifact includes internal release status so a rollout can be verified independently of the browser.

This establishes reusable API authorization, **not a generic automatic publishing workflow**. Future upload/release code can reuse this connection, but must verify the immutable signed artifact, source provenance, checksum and internal-only target before changing releases. Do not add production permissions or imply this check proves SMS/attestation/end-to-end production acceptance.

## Recovery and revocation
- Ordinary token expiry is automatic: each run obtains a fresh short-lived credential.
- To revoke: disable the provider, remove the SA's app permission in Play Console, or disable/remove the trusted GitHub environment. Removing only a local browser session is not the credential mechanism.
- New repository, branch, workflow path, or subject-template changes require an explicit owner-reviewed trust-policy update, not a broad wildcard.
- Account security, Play legal/KYC declarations, billing changes, or IAM reconfiguration may still require the human owner. The setup cannot guarantee that Google never requests owner verification.
- Production backend, Firestore rules, real SMS, positive Play-installed attestation, dependency advisories and physical-device acceptance remain separate release gates.
