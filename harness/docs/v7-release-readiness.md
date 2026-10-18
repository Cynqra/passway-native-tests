# Passway v7 — release readiness evidence

**Decision: NOT production-ready. Public release remains blocked.**

Candidate source: `04a26edefcc8857c8df7db93df0ede4dc40ffd5c`.
Version: Android `7`, application `0.3.1`.

## Verified
- Fresh functional regression: **411/411**; mobile/backend typechecks and Android/iOS/web exports passed. https://github.com/Cynqra/passway-native-tests/actions/runs/38864497211
- Extended static-security analysis passed without adding finding exclusions. https://github.com/Cynqra/passway-native-tests/actions/runs/38864500226
- Exact-source isolated native extended journeys: **75/75**, one attempt, 1,113.19 seconds, local services, two isolated Android users. This is NOT production two-user acceptance. https://github.com/Cynqra/passway-native-tests/actions/runs/38864503942
- Both vulnerable build-tool roots have hash-bound, reviewed local code fixes. Original registry advisory output is retained; **raw npm audit is NOT clean**. No version labels were fabricated. Remediation tests 18/18; upstream conformance: Forge 829 passing/4 existing pending, braces 899 passing. Production backend audit has zero advisories. Local fixes require maintenance until official patched releases exist.
- Signed bundle provenance and upload signing verified. https://github.com/Cynqra/passway-native-tests/actions/runs/38864507995
- Google Play INTERNAL release v7 was committed; independent authenticated readback confirms internal v7 completed, with no public production release. https://github.com/Cynqra/passway-native-tests/actions/runs/38867466558 https://github.com/Cynqra/passway-native-tests/actions/runs/38867771942
- Play-generated universal APK downloaded through keyless read-only API access and cryptographically verified, including hybrid v3.2 signatures and registered v3.0 app signing certificate. https://github.com/Cynqra/passway-native-tests/actions/runs/38868515570
- Harness unit tests: **58/58**.

## Real physical-device result — blocked, not passed
A real Google Pixel 9 / API35 accepted installation of the exact Play-generated APK over ADB. SHA256 `0cabec3cb07b69dd14b0e57b7d6301b12623b15314025b916fa39b24d2604eff`.

Google's injected `com.pairip.licensecheck.LicenseActivity` redirected to Google Play Store. The device had no signed-in Play account. Official Google sign-in reached the authorized tester account's password step. No password was entered/guessed; no licensing or App Check bypass was attempted. ADB installation is not a Play Store install, and the measured 309ms launch-to-activity result is NOT usable app-startup performance.

The reservation was cancelled and a fresh list confirmed no reservations. No paid plan or billing upgrade was enabled.

## Exact verifier failure fixed
The first APK-verification job failed because the default Java runtime lacked the ML-DSA KeyFactory needed for Google's new hybrid signer. The verifier was upgraded to JDK25 and full signature verification then passed. Signature checks were not skipped or weakened. Failed run retained: https://github.com/Cynqra/passway-native-tests/actions/runs/38868373818

## Hosted strict-candidate check
Exact backend runtime source was deployed to a Vercel-authentication-protected preview, with App Check enforced and an explicitly inert SMS credential. **6/6** missing/invalid-attestation rejection checks passed for otpSend, otpVerify, and generateTid. No real SMS, authenticated mutation, positive native attestation, or production promotion is claimed. Result file: `strict-v7-negative-fixture-result.json`. A previous isolated preview deliberately disabled SMS routes; its HTTP404 responses were not counted as attestation passes.

A temporary preview packaging error excluded nested `src/lib` through an unanchored ignore pattern. This affected the staging directory, not application source. The original anchored ignore file was restored; the protected build then passed. Failed deployment diagnostics are retained.

## Remaining release gates
1. Genuine Play Store installation and positive native App Check verification, not a debug token or bypass.
2. Native production two-user flow, including real sign-in, connection consent, bidirectional messages/replies, private notes, block/report/end, reconnect and deletion/retention behavior.
3. Coordinated tested backend / rules / client cutover, followed by actual-production positive and negative checks. The current production API does **not** satisfy the expected missing/invalid App Check rejection contract: all six probes failed that contract. Invalid payloads were used and no SMS/authenticated mutation was attempted. Do not represent HTTP400 or a different HTTP401 as a successful attestation check.
4. Platform/OEM coverage beyond the bounded Android tests; iOS export is not native iOS acceptance.

No claim of zero bugs, positive production attestation, or completed production acceptance is supported.
