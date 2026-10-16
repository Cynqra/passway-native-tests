# Passway v0.3.2 / Android 8 — internal candidate evidence

Source `8a6d79da24454e5373e5b89d34df279b067a1993`; frozen harness `d9450fddf19c4e80866698f8858a4a6cdbb9cd3c`.

## Verified

- Regression/dependency workflow 38894440223: **465 source cases** (127 mobile, 223 backend, 35 rules, 80 real Firestore), typechecks and Android/iOS/web exports.
- Static workflow 38894443506: zero SARIF findings, not a penetration-test claim.
- Fresh native workflow 38894446875: **75/75 assertions**, coordinator exit 0, both fresh completion markers, exact archive/source match. Fictional SMS / isolated Firebase routing explicitly scoped. Includes both Android users, messaging, keyboard edit/dismissal, offline recovery, notes, profile, cancel/decline, person blocking/reporting, deletion/re-registration and fatal/ANR capture.
- Signed workflow 38894449954: version 0.3.2 / code8, exact source archive, manifest controls, actual upload signer, artifact SHA-256. Local `jarsigner` is unavailable; actual signature validation ran in the signed CI and again in the publication guard. Local certificate/hash/manifest verification is additional, not falsely called a local cryptographic signature check.
- Internal publication 38897935089: exact-source regression, static, native, signed artifact gates required; Play edit committed for **internal only**. No public production rollout.

## Precisely measured testing cost

Native coordinator 1,037.54s. 779 instrumentation calls total 644.34s (62.1%); 542 hierarchy reads alone total340.71s. These are automation costs, not app latency or a claimed speed fix. Reducing assertions or inflating deadlines would not resolve application defects.

## Still blocked — do not label production ready

Fresh six empty-body production attestation checks at 2026-10-16T12:05:19Z **0/6 match the strict rejection contract**. No SMS was sent and no authenticated user mutation was made by those checks. Existing production API is not the newly validated backend. Do not deploy deny-message-body rules alone or force attestation before the genuine Store-installed client is verified; either can lock out existing users.

No genuine Play-installed positive attestation, real-SMS production two-user acceptance or coordinated production cutover is claimed. An authenticated Google CLI, successful internal upload, downloadable Play-signed APK or ADB sideload is not a licensed Store-install proof. Physical phone was released rather than consuming minutes waiting on Google Play tester credentials. Google recognized the intended tester account; do not misdiagnose the work-account heading alone as a policy denial.

Raw registry audit remains **21 propagated high entries from two upstream advisories**; reviewed byte-bound patches and executable security gates do not make that registry audit clean.

Earlier live backend results (57 assertions +3 isolation +6 negative preview attestation) are retained only by verified entire-backend-tree equivalence plus27 source hashes; they are not fresh client or Store-attestation evidence.

## Independent post-publication checks

Play readback run38898138210 confirmed internal version8 completed, no public production release, temporary edit deleted. Authenticated generated-APK download run38898141494 verified package/version, cryptographic APK signatures (v2/v3/v3.2), SourceStamp and expected Play signing certificate. Local artifact hash independently matched `6bcc69919bed10d4e1178ff96abd9eda52cdc84a9f708bee8637567b92f4e63c`. This remains download/signature evidence, NOT Store installation or positive attestation.

## Read-only Firebase control-plane verification

At12:08:26Z Play Integrity was configured and the exact Play signing SHA-256 was registered. `deviceIntegrity.minDeviceRecognitionLevel` is `NO_INTEGRITY`: this setting does not require a device-recognition verdict. It does not by itself prove an app-token bypass, and registration is not a positive token test. Assess the supported-device policy and verify a genuine signed client before tightening a project-wide setting; no blind production lockout or control-plane mutation was performed.
