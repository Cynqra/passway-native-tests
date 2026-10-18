# Native harness audit and remediation

Source baseline: enterprise test repository c2102a61c28bdbd05bc3d332aeb83222cb02bb15.
Application archive verified SHA-256 4cab05310a072d39a4d20776e2a5d9ebc10d39ea0798bf862b2c4529b08dfd82, source fc8d436d6f1896245a06e5f947d0456aaf601fd9.

## Findings fixed in this candidate

- Coordinator used to wait up to five minutes after failure for an incoming main-branch patch, replace harness files and HEAD, then rerun while keeping emulator state. Removed live patching and implicit retries: one immutable attempt, hard 900-second ceiling, explicit result file.
- A stale complete.json could remain from a previous run. Remove before starting and require both exit zero and a fresh marker.
- waitfor's outer deadline did not constrain nested probes/ADB calls (45/90-second inner budgets). Context-local deadlines now constrain subprocess timeouts; dump has its own 30-second ceiling and hidden nodes cannot satisfy waits. Context isolation prevents GPS background-thread interference.
- Every recorded check synchronously performed GitHub branch/status API writes, each with a 15-second request timeout. Status now writes local atomic evidence and stage history only. No repository write token is needed; permissions reduced to contents:read and checkout credentials are not retained.
- Fresh native compilation had no persistent Gradle or npm download cache. Add pinned setup-gradle and npm caching plus Gradle build-cache. This is an optimization candidate: no warm-cache speedup is claimed until measured in hosted CI.
- Pin third-party actions to immutable commits in historical native workflows. Keep old JS-patched APK workflow manual and label it historical; it must not stand in for fresh-source/production E2E.

## Validation and limits

Eleven Python harness tests (including real subprocess timeout enforcement) pass locally; workflow YAML parses and Python compilation succeeds. Tests use mocked subprocesses, not a live Android emulator. No native device execution of these harness changes has occurred yet.

Recovered unchanged application: 70 mobile cases and 171 backend cases pass; mobile and both backend/API TypeScript checks pass. Fresh isolated Firestore run also passed 32 rules cases and 42 integration cases: 315 application cases total. Expected error logs in injected Auth-deletion-failure tests were accompanied by successful recovery assertions; these are not production crashes.

Existing hosted regression run 38704395961 succeeded; dependency-security failed at mobile/build-tool npm audit. Exact-lockfile re-audit reproduces 21 high-severity affected dependency entries from two unpatched advisories (braces GHSA-vfj7-8cjw-p6xm; node-forge GHSA-86w9-cpqp-85rv). No gate suppression, Expo major downgrade, production deployment or paid/SMS request is included.

Previous fresh-native smoke run 38703132829 only proves demo-config Android16 compilation and signed-out cold start, not production two-user E2E. These changes do not upgrade that historical evidence.
