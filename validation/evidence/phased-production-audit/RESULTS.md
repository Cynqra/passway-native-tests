# Phased audit: isolated engineering acceptance passed; production release BLOCKED

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

No current Gemini4Argon inference is claimed: its prior quota/sign-in block remained, and no Flash-Lite fallback prompt was sent. Runtime evidence comes from actual GitHub/Android/Node tools. No zero-bugs or production-ready certification is made.
