# Version 11 release acceptance in progress

Exact changed application source: 9b426fcc7e86efc5876a439286b431ac05467896, version 0.3.5, Android code 11. Source PR: https://github.com/naveenbharti310/Paasway/pull/16

Changes add the approved support email and bounded email-app handoff, and correct the phone-use disclosure to include abuse prevention. No backend or database policy changes in this candidate.

Initial Android 14 run 39008975172 and Android 16 run 39008976447 FAILED. The native artifact hierarchy shows Gmail's welcome screen, but the harness only recognized a legacy mResumedActivity field and timed out. Actual Gmail arrival is handoff evidence, not email delivery evidence. No email was sent. Failures are preserved rather than relabeled as passes.

Two new regressions first failed against the old harness. The corrected harness observes the visible native UI package matching the resolved mail client, with the same deadline. Wrong foreground packages still fail. All 121 harness unit tests passed after correction. Harness revision a49452c66dfad400252eefd198e7f688c5fb9401.

Fresh acceptance reruns are in progress: Android 14 39010315994, Android 16 39010317568, signed bundle 39010319012, architecture 39010348470, static security 39010350088. Earlier successful signed run 39008978180 is historical only because release controls require the same harness revision.

Read-only deployed policy recheck passed 5 of 5 checks at 2026-10-17T06:33:51.433Z. This is exact Firestore rules and required-index parity, not production SMS or positive Play attestation.

No version 11 internal publication or public rollout has occurred. Genuine Play-installed positive attestation, current native real-SMS acceptance, and remaining Play declarations are not complete. Private browser input failed before any credential submission; that environment access failure is not evidence of invalid credentials.

## Review correction before merge

The 9b426fc candidate completed Android 14 run39010315994 and Android16 run39010317568 with84/84 assertions on each OS. Both verified actual native support handoff and return. Signed bundle39010319012, architecture39010348470 and static security39010350088 passed. No email was sent. The signed AAB hash was82de7126ffef0afba160390791fd05bd263f0c0bdf7ec12d222a88206474c2b4.

The attempted merge was blocked by an unresolved review conversation, not failing tests. Inspection identified a legitimate omission: phone-based age eligibility enforcement also needed disclosure. A new regression failed before the fix. Source f8d734a73e10757d4f48aa8c080b52ba3910ccdb explicitly includes that purpose. All212 mobile tests passed locally after correction; reused tooling is not clean dependency acceptance. The discussion was addressed with the fix and regression evidence. Branch protections were not bypassed or weakened.

Version11 has NOT been merged or published. All 9b426fc native/signed results are now superseded acceptance for the changed source, preserved here as historical evidence rather than inherited. Corrected-source fresh runs: Android14 39012090085, Android16 39012091066, signed39012092202, architecture39012093928, static39012095861. They use harness b11fefb and the archive recorded in final-app-provenance.json.

Independent production rejection probes passed26/26. Latest registry tags are still node-forge1.4.0 and braces3.0.3, with no newer official releases observed. The raw audit reports21 high package findings derived from the two exact reviewed advisories; local file-hash-bound remediation and complete upstream conformance pass. This is not a clean registry audit. Backend production audit reports zero vulnerabilities.
