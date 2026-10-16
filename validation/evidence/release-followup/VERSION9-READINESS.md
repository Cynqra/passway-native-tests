# Passway version 9 — verified internal candidate, NOT production certification

Source: `fbc13efb9ce8ea0322ae455e1694d164a163af76`; version 0.3.3 / code 9.
All release acceptance runs were frozen at harness `b144576caf9230a4835ef827843ad2220ea8dce4`.

## Completed
- Exact-source regression: 129 mobile + 223 backend + 35 rules + 80 real Firestore = 467 passing checks. Both typechecks, exports and reviewed dependency-patch acceptance passed. Run 38905433289.
- Static analysis: zero SARIF findings in this scan. Run 38905436876.
- Signed bundle: actual hash and compiled manifest verified; cryptographic signature verified by CI and publication guard. Run 38905440467.
- Fresh native: 75/75 checks, one attempt, fresh base/extended markers, coordinator exit 0; 823.93 seconds. Run 38905444007. Native journeys use two Android users and LOCAL Firebase/Auth/Firestore and original candidate handlers via an explicit test-only routing overlay. They do NOT establish production SMS, Store licensing or attestation.
- Internal publication only: 38909570418. Play readback 38909909885 confirms completed internal version 9, no public production release, temporary readback edit deleted.
- Actual Google Play generated APK9 downloaded and verified: 38909913894. APK SHA256 `1029b6356a47139d727e75f73d32a8468cea1d31a05516e644e2afedd9f86863`; package com.passway.app; 96,545,280 bytes. Download is NOT a licensed Store installation.
- Retention copy now distinguishes 72-hour chat availability, subsequent cleanup and longer reported-content retention; two regressions failed before the correction and passed afterward.

## Measured slow-test cause and fix
The driver redundantly read hierarchy after the native probe already returned a fresh post-action hierarchy. Corrected without removing assertions, fresh-read retries, deadlines or journeys. Same-app source8 comparison: 1037.54 to 813.91 seconds (21.6% faster), 779 to 717 instrumentation calls. One hosted comparison, runner noise applies; NOT an application-latency benchmark.

After candidate9 publication/readback completed, harness `2fc6bd0` removed cross-revision queue contention ONLY for isolated test modes; 72 harness tests pass. Cloud/release mutation modes retain shared serialization and no in-progress cancellation. No measured parallel-speedup claim. Candidate9 acceptance remains attached to its original frozen harness; it is not relabeled as validation of later revisions.

## Still blocked / not claimed
1. Genuine Play-installed licensed-device positive attestation and real production SMS/current-production two-user acceptance are not established.
2. Actual protected APK8 offline UI run 38904704772 FAILED before onboarding: obsolete Play Services and Play license wrong-installer rejection on the sideloaded Google APIs emulator. Onboarding/font-scale cases did NOT pass; do not rerun the same incompatible environment or bypass protection.
3. Read-only Test Lab request returns 403 Not authorized for project passway-2ddc8. Cloud Billing read is separately SERVICE_DISABLED, not proof of billing IAM failure. No API/billing upgrade or paid physical test was initiated.
4. Candidate API/client/rules require a coordinated verified production cutover. Existing production negative-attestation contract checks did not pass. Do not promote API or deny message-body reads in isolation and break existing clients.
5. Raw registry npm audit is NOT clean: unresolved braces/node-forge advisories remain, despite reviewed hash-bound installed-code mitigations and passing exploit/conformance gates. Backend production dependency audit was clean in its scoped check.
6. No zero-bugs, E2EE, penetration-test/compliance certification, production load SLO, or positive Store attestation claim.

Production backlog read-only metadata audit observed no eligible expired records or pending account-deletion jobs at its recorded instant. It is not an SLA/load proof.

All workflow URLs: https://github.com/Cynqra/passway-native-tests/actions/runs/<run-id>
