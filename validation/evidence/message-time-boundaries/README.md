# Exact-source verification: message-time boundary fix

Candidate application commit: `bc5a5918719cb22ea6e915e09c5d7281a5d15ca7`.
Candidate archive SHA-256: `03b889404d9497f52a13fb07d1597fdc8e40e132108c17f037a214ec48500c56`.
Harness input revision: `c139d2b` on `validation/isolated-current-native`.

## Reproduced and fixed

Five new unit regressions and the same five real Firestore integration regressions failed before correction. Malformed/future reply timestamps could be accepted; future persisted rows could consume the query limit and hide valid latest/history rows. The backend now checks finite, nonfuture, unexpired reply timestamps and applies both query-time bounds before the existing result limit. This is persisted-record robustness: client rules already deny direct message writes, not evidence of an unauthenticated write exploit.

No native/client/signing change, new dependency/index, production deployment or security-policy bypass was introduced.

## Independent runs

- Regression/dependency verification: https://github.com/Cynqra/passway-native-tests/actions/runs/38872226893 — success. 113 mobile + 208 backend + 35 rules + 65 real Firestore integration = **421 passing**, zero failures. Both TypeScript checks and Android/iOS/web exports passed.
- Extended static security: https://github.com/Cynqra/passway-native-tests/actions/runs/38872230115 — success.
- Fresh isolated extended native: https://github.com/Cynqra/passway-native-tests/actions/runs/38872233392 — success. Downloaded artifact independently checked against exact source SHA: **75/75 PASS**, coordinator exit 0, both core and extended completion markers present. Duration **1065.97 seconds**.

The native artifact is an explicitly isolated two-user Android/Auth/Firestore emulator test. It is **not** real-SMS, store-installation, positive Play Integrity or production two-user acceptance proof. The internal v7 native client is unchanged by this backend-only patch.

## Dependency qualification

Installed, hash-bound local security remediations and their conformance checks passed. **Raw npm registry audit is NOT clean**. Do not rewrite this as zero dependency advisories. See application `docs/build-tool-security-remediation.md`.

## Measured test overhead

The separately measured prior native run 38864503942 took 1113.19 seconds. 777 instrumentation probes consumed 703.16 seconds (~63.2%); median 0.65 seconds and p95 1.88 seconds. This is test-driver overhead, not app-response latency. The attached aggregate is not a claim about all historical delays. No test assertions or safety waits were weakened to manufacture a speedup.

## Release remains blocked

`release/production-acceptance` remains failure. Store-installed positive attestation and a full production two-user flow remain unverified. Current candidate API/client/rules migration must be coordinated; rules-only promotion breaks older direct-message-read clients. No public production release was made. A fresh hosted preview of this backend revision was not deployed: the saved Vercel token was rejected. Historical hosted-preview results must not be relabeled as this revision's results.

A secure browser input failure coincided with the local workspace reverting to an older snapshot. Remote commits/runs/artifacts survived and were recovered, rather than blindly repeating completed runs. Platform root cause is unknown; no unsupported claim about session lifetime is made.
