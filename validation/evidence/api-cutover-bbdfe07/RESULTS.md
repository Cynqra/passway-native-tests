# Canonical API cutover and production service acceptance

Observed 2026-10-16 UTC. API runtime source bbdfe0735cedc07c5a401ae147cb9abe76f2e6e1, archive SHA256 addea431c5714824d5bc678a3fc3a4f0fde66e9877092305c6384a77a6fb40ed. Production API deployment dpl_8xyA4os4SKu4vvDDk6UVidty9zxD, promoted after staged acceptance. Canonical API https://passway-api.vercel.app.

## Verified now

The old live deployment mismatch, including missing getMessages, was resolved by controlled promotion after 26 boundary and 48 business assertions passed on the protected candidate. The public canonical address then passed all 26 boundary probes and 50 service assertions against real Firebase services. All disposable fixtures were cleaned up.

A separate bounded-concurrency pass succeeded on 56 assertions. Maximum eight requests in flight. Three concurrent redemptions and six consent decisions retained one identity per intent; eight copies of one send intent stored one message; four reports retained one report identity. All acknowledgements and cleanup passed. These counts overlap and must not be summed as unique test cases.

There were 72 timed service requests in the bounded-concurrency pass: p50 721 ms, p95 2296 ms, maximum 2819 ms. This is operator-harness timing from one network, not mobile performance, a cold-start SLA, a sustained-load benchmark or production availability certification.

Real flows included age gating, decline and retries, nearby pairing, third-party denial, two-way messages and replies, expired message visibility/quote denial, report and alternate-chat block enforcement, explicit block/end/cancel retries, deletion and revoked-token rejection. ADMIN-issued App Check and disposable Firebase users were used. No SMS was sent. This is not positive native/Store-issued attestation evidence.

Noncanonical unique deployment URLs and the secondary alias reject unauthenticated requests at Vercel authentication. The old protected deployment is retained for rollback. The public canonical API rejects missing/invalid App Check; no debug bypass was added.

Future preview deployments no longer receive production Firebase Admin or cron credentials. Production values were not rotated, printed or copied. App Check remains enabled. Git auto-deployment is disconnected; deployment remains a deliberate evidence-bound operation.

The tested stacked source was consolidated through source PR13; PR14 removed CI path filters that could leave mandatory checks pending. Main is protected with strict regression and dependency-security checks, including administrators. Pull requests are required, but this single-maintainer policy requires zero separate approvers and is not independent human review. Historical patched-APK workflows were disabled without deleting history. The trusted fresh-source native workflow was not changed.

## Preserved failed assertions and corrections

The first hosted fixture failed because Firebase Admin App Check TTL was below the SDK minimum. The fixture was corrected to 30 minutes; the production handler was not changed.

The next hosted assertion incorrectly expected non-owner consent HTTP403. The intentional contract is HTTP400 FAILED_PRECONDITION to conceal request availability. The corrected assertion also verifies that the pending request and absent connection remain unchanged. Production authorization was not relaxed.

Two deployment exposure observations initially assumed an HTML login response or application-level rejection on the secondary alias. Actual Vercel authentication responds with JSON401. Corrected classification checks the provider protection flag and error code. Prior failed assumptions are retained. Response bodies and callback nonces are not retained.

Maintenance observation is read-only: the system record contained only lastRunAt. It establishes a successful coordinated maintenance run, not explicit cron invocation or retention SLA proof.

## Durable independent checks

Source clean CI: https://github.com/naveenbharti310/Paasway/actions/runs/38974449958
Source PR13: https://github.com/naveenbharti310/Paasway/pull/13
Source PR14: https://github.com/naveenbharti310/Paasway/pull/14
Protected main CI: https://github.com/naveenbharti310/Paasway/actions/runs/38976790336
Source live boundary check: https://github.com/naveenbharti310/Paasway/actions/runs/38976295586
Public monitor: https://github.com/Cynqra/passway-native-tests/actions/runs/38976293479
Read-only keyless Play access: https://github.com/Cynqra/passway-native-tests/actions/runs/38977258348

Play access uses short-lived OIDC federation, not a stored publisher JSON key. It confirmed internal version10 completed, no public production release, and deleted the temporary edit. It did not upload or publish a release.

## Remaining release gates

Not production-ready certification. Genuine Play-installed positive native attestation and real-device release flow remain unverified. Prior Android14/16 emulator results (81 assertions each) are historical accepted-source evidence, not new native production tests in this pass. Genuine store/installer licensing must not be spoofed.

Store privacy policy, off-app deletion request process, reviewer access, content rating, target audience and Data Safety require completion and factual validation. Raw dependency advisories remain visible; hash-bound reviewed build-tool remediations and exploit/conformance gates pass, which is not a claim of zero upstream advisories. No claim of zero possible bugs, no paid upgrade and no public rollout.
