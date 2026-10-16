# Production-readiness progress — ec65e82; public release remains BLOCKED

- **43/43 hosted two-user HTTP/Auth/Firestore assertions with App Check enforced and real ADMIN test tokens**; all disposable fixtures independently removed and preview retired. This repeats earlier40-case diagnostic coverage, not83 unique cases.
- **16/16** protected original-entry negative/SMS-disabled checks.
- **8/8** negative and **4/4** controlled-token auth/input checks on the full, unpromoted **production-configuration candidate** `dpl_2hWYWikzCJmK5vchMXNRgh9rwQWa`.
- All required live composite indexes READY. Candidate source remains unchanged; earlier634-case clean and Android14/16 81-case gates still refer to the same archive.
- The actual public API was NOT cut over; both live aliases are verified on the old deployment. Genuine Play-installed positive attestation, real SMS acceptance, coordinated client/API/rules migration, operational monitoring and residual dependency risk remain gates. Admin tokens are not Store attestation.

Details, retained diagnostic failure, cleanup and alias proofs: [cloud-staging-ec65e82](cloud-staging-ec65e82/README.md).

---

## Earlier isolated/source acceptance (before cloud staging)

# Latest rigorous audit: ec65e82 isolated gates passed; production BLOCKED

## Exact latest candidate

- Source `ec65e826e456f406a9087da843c4d4d6425d886d`, archive SHA256 `b6b17bd4f65dec104f2c7287e297722884695b4351e639ea99642a1b5b563daf`.
- New clean, native, static and signed gates consume the identical archive through harness `62e9723ae23dd6112965ecfb218210657e0a04c9`.
- Unpublished0.3.4/Android10. AAB SHA256 `872fb7529f38dff18e5533c1e273d3e51899e73670df1b98873133f813465a9a`. Backup explicitlyfalse; debuggable absent/defaultfalse; cleartext absent/defaultfalse with target API36. No store publication, production deployment, paid API enablement, or billing change.

## Confirmed reliability fixes

- A lost redemption acknowledgement formerly stranded a successfully committed requester. Optional random intent identity now binds recovery to authenticated UID, normalized name, code and exact code incarnation. Rechecks cover active accounts/phone holds, diagnostic cohort, bidirectional blocks, proximity, request/code expiry and accepted connection participants/status. Recovery cannot reverse a decline, extend expiry, claim a new code incarnation, or reopen an ended connection. Legacy clients retain strict single-use semantics. Replay sends no duplicate notification.
- Expiry is rechecked after asynchronous account/block/connection reads before returning or writing; expiry crossing fails closed.
- Synchronous refs serialize same-render connect/cancel/accept-vs-decline, OTP send-vs-verify, chat send/safety/note, age, name-save and account deletion/recovery operations. Button and keyboard/system-back paths share guards. Failures permit explicit retries; a resent OTP clears superseded input.
- Sign-out errors are caught and displayed rather than unhandled; duplicate deletion dialogs and overlapping deletion loops are suppressed.

58 additional cases:28 actual-TSX handler,26 backend recovery/security,4 real-Firestore. Not every new regression is a distinct vulnerability.

| Latest gate | Actual result | Run |
|---|---|---|
| Source clean dependency/regression/export |634/634; typechecks; all-platform exports; controlled preview build|[38941004403](https://github.com/naveenbharti310/Paasway/actions/runs/38941004403)|
| Independent clean validation |634/634; installed remediation/conformance policy passed|[38941001227](https://github.com/Cynqra/passway-native-tests/actions/runs/38941001227)|
| Static analysis |0 SARIF findings|[38941005486](https://github.com/Cynqra/passway-native-tests/actions/runs/38941005486)|
| Android14 native |81/81;925.34s; one full attempt;0 pre-dispatch reacquisitions|[38941009423](https://github.com/Cynqra/passway-native-tests/actions/runs/38941009423)|
| Android16 native |81/81;905.62s; one full attempt;0 pre-dispatch reacquisitions|[38941013183](https://github.com/Cynqra/passway-native-tests/actions/runs/38941013183)|
| Upload-signed candidate |same source/archive; metadata, manifest and SHA independently checked|[38941016522](https://github.com/Cynqra/passway-native-tests/actions/runs/38941016522)|

634 cases per clean run =4policy+196mobile+308backend+35rules+87real-Firestore+4real-Auth. Independent repeats do not double unique coverage. Both native screenshots were inspected: codes remain single-line; large-text consent labels remain whole/stacked. Request screenshots are scrolled to decision controls, not evidence that all content fits without scrolling. Native emulator evidence is not real SMS, licensed Play attestation, physical-device accessibility or production load certification. A bounded local workload separately passed160unique messages under320send/replay calls across16pairs; it is not a production SLA.

## Requested external review: Argon High actually executed

Official Antigravity CLI1.4.0 is authenticated. Model `gemini-4-argon-high` was pinned, effort `high`; actual effort inspection reports only `low,medium,high`, so High is the highest supported tier. No silent fallback or paid API activation.

The first file-discovery review repeatedly requested nonexistent paths and was stopped, not accepted. The replacement supplied14 exact source files directly and completed in one turn,142.00s:39,737input tokens,11,988output tokens,10,757thinking tokens,51,725total. It reports no confirmed correctness/security bug in supplied-code scope. It ran no tests and is not zero-bug/production certification. Result/configuration proof is in `intent-recovery-ec65e82/argon-high-review.json`; OAuth secrets and private reasoning transcripts are excluded.

## Production remains blocked

Fresh safe live negative probe:0/8. OTP routes400 before required attestation rejection; generateTid401wrongcontract; getMessages404. No SMS or authenticated mutation. Candidate not deployed. Coordinated additive API/index/client/rules cutover, genuine Play-installed positive attestation, actual2factor delivery acceptance, cloud-test IAM, and production monitoring remain unresolved. Raw registry audit still reports21high; installed hash-bound mitigations do not make it clean.

Detailed proof: `intent-recovery-ec65e82/`. Earlier evidence below is historical, never inherited as acceptance of changed source.

---

# Historical candidate: 2ffec5f (superseded by ec65e82)

## Exact candidate

- Source: `2ffec5fd702824ec5d4f1b200ac28102fd8b2a4b` (`naveenbharti310/Paasway`, PR11).
- Archive SHA256: `38b34906d1dcf6b5b0fa61cbc9cdd9ffed7a60534f741fd3cfd1151aca4ea048`.
- Candidate0.3.4/Android10 is **not published**. Existing internal release remains9; no public production release was present in the read-only Play capability check.
- Clean/signing harness10a4db2; native harness60e2e35 differs only in native text-geometry target validation. Both consume the identical archive above. Never relabel an earlier source's run as current acceptance.

## Verified gates

| Gate | Actual result | Run |
|---|---|---|
| Source clean regression/security/export |576/576 cases; both typechecks; all platform exports; controlled build-only preview|[38935318797](https://github.com/naveenbharti310/Paasway/actions/runs/38935318797)|
| Independent clean validation |576/576 cases; actual dependency hashes/exploit and pinned conformance checks|[38935320479](https://github.com/Cynqra/passway-native-tests/actions/runs/38935320479)|
| Static analysis |0 SARIF findings|[38935325182](https://github.com/Cynqra/passway-native-tests/actions/runs/38935325182)|
| Offline secret scan |Gitleaks8.30.1 exit0,0 redacted matches|Local exact tracked-source scan; not a credential-rotation claim|
| Android14 native |81/81;967.06s; one full attempt;0 pre-dispatch reacquisitions; all3 fresh markers|[38935487439](https://github.com/Cynqra/passway-native-tests/actions/runs/38935487439)|
| Android16 native |81/81;984.22s; one full attempt;0 pre-dispatch reacquisitions; all3 fresh markers|[38935492565](https://github.com/Cynqra/passway-native-tests/actions/runs/38935492565)|
| Hardened upload-signed bundle |version0.3.4/code10, backup/debug/cleartext disabled; metadata and SHA256 independently checked|[38935337937](https://github.com/Cynqra/passway-native-tests/actions/runs/38935337937)|
| Keyless Play capability |Authorized; temporary edit read/deleted; no upload/track/release commit|[38932991427](https://github.com/Cynqra/passway-native-tests/actions/runs/38932991427)|

576 cases =4 workflow-policy+168 mobile+282 backend+35 rules+83 real-Firestore+4 real-Auth bridge, per clean run. Not1152 unique cases. Conformance suites are separate: forge829 pass/4pending, braces899 pass. Raw npm registry audit remains **21 high**, from two unpatched upstream roots; installed mitigations do not make the registry audit clean or erase residual risk.

Native tests operate two Android users/four fictional identities against local Auth/Firestore and original candidate HTTP handlers. They cover actual onboarding, sign-in, pairing, bidirectional messaging/keyboard, notes, relaunch/offline recovery, rename persistence, cancellation/back/expired codes, decline, block/re-pair rejection, report/evidence retention, deletion/re-registration, and the constrained440x880/fontScale2 journey. UI screenshots were inspected after functional checks passed: four-character code now stays on one line; large-text consent actions stack with complete words. Geometry checks reject the original wrapping and distinguish text from padded accessible button containers.

## Confirmed fixes, by phase

1. CI dependency policy alignment with retained raw advisories; safe automatic credential-free PR checks; deployed gate includes getMessages; preview helper requires controlled explicit configuration and builds only.
2. Expanded real HTTP authorization/App Check boundary matrix and local Auth bridge; suspected missing phone claim was not reproduced, so no speculative patch.
3. Bounded pending-request/TID cancellation during account deletion with real transaction/race tests; moderation uses initialized credentials and bounds the complete credential/HTTP/body operation to2500ms.
4. Generator terminal-request listener; synchronous generation action lock; scrollable timed screens; native-observed code/navigation wrapping and split consent labels fixed. Harness gestures target actual inner scroll surfaces; only explicit pre-dispatch locator absence permits bounded reacquisition. Unknown/performed touch failures are never retried.99 harness unit cases pass.

Earlier failed/cancelled runs remain retained in audit-ledger.json. In particular, Android16 run38931567916 failed a pre-dispatch target lookup after passing large-text pairing; its exact transient/cache cause was not proven. The new full runs pass without invoking the recovery path. Do not reinterpret the earlier failure as a pass. Small-display swipe and stale version9 assertion defects were reproduced separately. GitHub's signing environment protection was preserved; use the authorized validation branch, not broader trust policies.

## Production phase: NOT accepted

The fresh live production negative preflight fails **0/8**: OTP routes return400 before the required App Check rejection contract; generateTid returns the wrong401 contract; getMessages returns404. No SMS or authenticated mutation is made by this check. Read-only deployment metadata last showed a production deployment with no source commit metadata. The validated candidate has not been deployed there.

Do not blindly deploy deny-body-read rules or enable enforcement against an unverified Store client. Mandatory remaining work:

1. Verify production composite index readiness and the additive API/deletion recovery in an App Check-enabled controlled staging environment.
2. Complete genuine licensed Play-installed, store-signed positive attestation and production two-user/real2factor SMS acceptance. An ADB-installed diagnostic APK, fictional OTP, emulator App Check bypass, or successful AAB build is not this proof.
3. Coordinate client availability/minimum-version policy, API/rules/index cutover, old-client rejection, reconnect/foreground/expiry acceptance and staged release. Do not deploy rules alone or weaken attestation to force a green check.
4. Establish real production load/backlog/retention-job monitoring and alert budgets; local emulator workload numbers are not production capacity or device FPS certification.
5. Retain explicit upstream advisory risk until patched upstream versions or independently reviewed alternatives are available.

Current cloud-test credential's read-only IAM inspection grants storage.buckets.create, not Test Lab matrix permissions. Free minutes do not grant IAM permission; no paid APIs, billing upgrade, self-granted roles, or security bypass was introduced. The Play publishing connection itself is working.

At this historical checkpoint, no Gemini4Argon inference was claimed. This was subsequently resolved through the official Antigravity CLI, as documented above. No Flash-Lite fallback review was used. Runtime evidence comes from actual GitHub/Android/Node tools. No zero-bugs or production-ready certification is made.
