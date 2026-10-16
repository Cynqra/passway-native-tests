# Maintenance and native reliability audit

## Current result

The maintenance correction and the corrected native test harness passed the source, security, signed bundle and two Android acceptance suites described here. This does not certify the application as ready for public production release. The production API has not been promoted, and positive native Store attestation and publisher policy requirements remain separate release gates.

The source revision is bbdfe0735cedc07c5a401ae147cb9abe76f2e6e1. Its complete tracked source archive SHA256 is addea431c5714824d5bc678a3fc3a4f0fde66e9877092305c6384a77a6fb40ed. The accepted protected harness revision is 6cffe32ef4f1f3d9f178ae4a106f38bb1cce84a3. Every final protected acceptance run below used that same revision and source archive. No live patches or different source revisions were substituted during a native attempt.

## Confirmed application correction

A regression reproduced the original defect before the correction. Failed maintenance recorded lastRunAt before completing its work and then suppressed a subsequent retry for fifteen minutes. The corrected implementation uses a transactional owner token and an expiring two minute lease. Only successful work completed during a valid lease advances the successful completion timestamp. Failure releases only the current worker's claim, and an abandoned claim can be recovered after expiry. An older worker cannot clear or certify a replacement worker's claim.

HTTP background maintenance, the authenticated daily cron and the scheduled job share the coordinator. The successful cron response preserves its existing closed and deleted fields; a skipped sweep is explicit. Cleanup and deletion remain idempotent operations. An expiring lease is not a guarantee of exactly once execution.

## Source and security acceptance

Clean source validation passed at https://github.com/naveenbharti310/Paasway/actions/runs/38959132791. The independent protected repeat passed at https://github.com/Cynqra/passway-native-tests/actions/runs/38963743840. Each completed 647 assertions comprising 4 dependency policy, 196 mobile, 316 backend, 35 Firestore rules, 92 real Firestore transaction and 4 real Auth assertions. Both TypeScript checks and platform exports passed. These counts are not added together as distinct coverage merely because the suite ran twice.

The independent synthetic workload verified 160 distinct messages despite 320 send and replay calls across 16 conversations and 32 synthetic participants. Reads, blocked conversations and sixteen parallel account deletions met the workload assertions. Its emulator measurements are not a production capacity or network latency benchmark.

Static security analysis passed at https://github.com/Cynqra/passway-native-tests/actions/runs/38963747764. The downloaded SARIF contained zero results. That finding count is not proof that no vulnerabilities exist.

Five local dependency exploit checks failed against the reused development installation, where the reviewed remedies were not applied. Those failures are retained, not counted as passing. Clean installation jobs verified installed file hashes, exploit rejection and pinned upstream conformance. The raw registry audit still reports 21 high findings in the original build tool versions. The registry audit is not clean, no package versions were relabelled, and reviewed local remedies require continued maintenance until suitable upstream replacements are available. Forge conformance recorded 829 passing tests and 4 existing pending tests; braces recorded 899 passing tests.

## Native failure and correction

The first Android 14 run https://github.com/Cynqra/passway-native-tests/actions/runs/38960254920 failed after 68 passing assertions. Android ActivityManager reported that the test probe process failed to attach. Device logs showed the operating system killing that unattached probe after its startup timeout, before Instrumentation lifecycle methods and UI injection. No underlying memory exhaustion cause is claimed. The original failed run and its results remain failed.

The harness correction permits one relaunch only for the complete, exact operating system failed to attach response naming the probe and the same Android user. A changed user aborts recovery. The original deadline remains in force. A timeout, crash, performed action marker, partial injection error, different package, different user or unknown output cannot trigger replay. All 112 Python harness tests and all 10 SMS response assertion tests passed, including fault injection using the recorded Android failure form.

The corrected Android 14 run passed 81 assertions at https://github.com/Cynqra/passway-native-tests/actions/runs/38963751495. Its coordinator recorded one immutable attempt and 918.47 seconds of test execution. Android 16 passed 81 assertions at https://github.com/Cynqra/passway-native-tests/actions/runs/38963754894, recording one immutable attempt and 976.53 seconds. Both have fresh core, extended and accessibility completion markers. No probe startup recovery event was needed in those two reruns. The specific recovery path is therefore supported by fault injection tests, not an observed device recovery event during those successful reruns.

These are real native UI journeys using controlled local Auth and Firestore services and original candidate handlers. They are not native production SMS, normal browser CORS, positive Store attestation, physical Oppo certification or long duration stability proof. Test durations include extensive probe and Android user switching work; they are not measurements of end user app startup time.

## Signed candidate

The signed candidate passed at https://github.com/Cynqra/passway-native-tests/actions/runs/38963758738. The package is com.passway.app, version 0.3.4, Android version code 10. Its independently recomputed AAB SHA256 is d7b1b4dfe87f3f065555ff44b7e6020c38e9204248f4f500f43689cee1ad5a3e. The artifact is bound to the source revision and archive above. App Check is enabled and diagnostics are disabled in that build. Signature and compiled native security checks passed. Building or signing is not evidence of Store installation or attestation.

An earlier signing dispatch from an evidence branch was rejected by the existing environment protection rule before execution. The correction used the existing authorized protected release branch. Credential protection and identity trust were not broadened. Superseded duplicate native runs were not counted as passing.

## Actual Google Play artifact

Google Play artifact retrieval passed at https://github.com/Cynqra/passway-native-tests/actions/runs/38967167501. The authenticated generated APK API returned version code 10. Its downloaded APK SHA256 was independently recomputed as 2de536f63e0d7b17063d5b3a2d7ca8b71afa0fd8108db59c1aca703462100bf9. The workflow verified the actual Play signing certificate and compiled package version. This proves the identity of the generated Store artifact, not installation through Google Play or positive attestation. No installer spoofing or protection bypass was attempted.

## Independent review

Gemini Argon High reviewed the source included maintenance change with high effort and found no confirmed defect in that narrow scope. A separate high effort review of the probe retry also found no confirmed defect in mutation replay, user isolation or retry deadline handling. Both were reviews only. Neither reviewer executed the tests or certified production readiness.

## Contact and remaining release gates

The user approved public support email Limerencetechnologies@gmail.com was saved in Play Console and verified after a page reload. Delivery, inbox ownership controls and support operations are not verified. The privacy policy remains a draft and has not been published or submitted as an approved policy. Public account deletion instructions and publisher declarations must accurately reflect the final application and operating practices.

The live API is still the older deployment identified by the public monitor. The corrected source is not described as a deployed production fix. The newer App Check enabled client and older App Check disabled internal client require a coordinated transition; blindly switching the API or weakening App Check is not an accepted workaround. Earlier private app sharing attempts returned Google's NOT_PUBLISHED precondition and generated no installation link. Ordinary internal distribution succeeded at https://github.com/Cynqra/passway-native-tests/actions/runs/38966884935 after all required same revision gates passed. The edit was committed to the internal track only, with version code 10 and the exact signed artifact hash recorded above. This is a private test candidate, not an assertion that the current live API is compatible or that Store attestation has passed. No public production rollout is authorized by this report, and no positive native Store attestation is claimed.
