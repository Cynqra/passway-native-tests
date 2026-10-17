# Production Firestore rules migration and post-fix acceptance

Observed 2026-10-17 UTC. Canonical API https://passway-api.vercel.app. Runtime source remains bbdfe0735cedc07c5a401ae147cb9abe76f2e6e1; application/native handlers were not changed in this pass.

## Confirmed gap and correction

The live API correctly filtered expired bodies, but deployed Firestore rules still permitted direct participant reads. Disposable fixtures reproduced HTTP200 for an expired body, profile recreation behind a deletion tombstone, deleting-profile mutation and a private-note write while deleting. These were real deployed-rule gaps, not hypothetical failures in an emulator.

All three required composite indexes were READY. The accepted rule SHA256 is 59914db6e5de3b2837a9c0d01327b8a777660c8809d43937832731ff6edb3f06. Old deployed SHA256 was 74f5ff0a79cc9965f9aad1aa417ccefecf3df73f7a5e6c1e34a336b5e9c1579e.

## Corrected authorization diagnosis

Earlier work stopped after the separate rule-testing API returned403 IAM_PERMISSION_DENIED and incorrectly generalized that to inability to deploy. A precise project permission test showed rulesets.create and releases.update ARE granted; rulesets.test and setIamPolicy are not. No IAM role was changed and no new Google sign-in was required. The existing permission was used to create an unpublished immutable ruleset, which validates syntax/semantics, then update the release only after verifying the old binding and migration prerequisites.

Accepted immutable ruleset: projects/passway-2ddc8/rulesets/81dfe9a4-10ea-4567-85c8-f84713307d8e.

Read-only Play check38999260743 confirmed completed internal version10 and no public production release. The internal client's source uses server-only body reads. No store rollout or release edit was committed. This availability check is not positive Store attestation.

## Preserved immediate post-publication failure

The first postcheck observed expired direct reads denied, but the immediately following fresh direct-read assertion failed. Its exact HTTP status was not recorded by that first harness; no unsupported claim of its value is made. The failed report and cleanup remain retained. A separate independently created fixture run later passed22 assertions including cleanup. This is consistent with enforcement propagation, but the evidence does not prove the internal provider cause. No policy was weakened and no automatic rollback to the insecure rules occurred.

## Independent live success

The independent22 checks verified accepted binding/hash, direct fresh/expired body denial, participant metadata and owner profile reads, private peer profiles and notes, nonparticipant denial, private deletion jobs, tombstone recreation denial, client body-write denial, allowed active profile/note writes, denied deleting profile/note writes, compatible server reads and verified absence of owned fixtures.

The public API then passed a separate56-assertion service/concurrency run: nearby pairing, own/remote/reused code denial, decline and retries, concurrent redemption and consent identity preservation, two-way messaging/replies, message retry mismatch and one-copy storage, expiry/quote denial, report idempotency and alternate-chat blocking, explicit block/end/cancel retries, account deletion and revoked-token denial. Maximum8 in-flight requests. Fixture cleanup passed. Counts overlap with earlier checks and must not be summed as unique coverage.

Tests used disposable synthetic accounts, actual Firebase services and ADMIN-issued App Check. No real SMS or real phone data was used. Not native UI, genuine Store attestation, physical-device performance, sustained-load certification or zero-bug proof.

## Drift prevention

Source PR15 adds a read-only ADC deployed-policy gate with27 credential-free unit tests. It checks exact rule bytes, all required composite indexes READY and stable binding. Full local fresh backend regression343/343 passed and backend typechecks passed. No dependency, runtime handler or native byte changes.

The first real parity checker request failed because wildcard index listing rejects explicit nonzero pageSize. A regression failed before correction; omitted/default size now works while response size and page count remain bounded. The corrected live gate passes5/5. That tooling failure was not an application API regression.

PR: https://github.com/naveenbharti310/Paasway/pull/15
Play read-only access: https://github.com/Cynqra/passway-native-tests/actions/runs/38999260743

## Remaining release gates

Genuine Play-installed positive native attestation and physical-device release acceptance remain unverified. Store privacy/deletion process, reviewer access, rating, target audience and Data Safety still require completion and factual validation. Latest registry versions are still braces3.0.3 and node-forge1.4.0; upstream advisories were not declared resolved. Existing reviewed build-tool remediation gates are separate from a clean raw registry audit. No paid plan, public production rollout or permanent IAM privilege increase.

## Final source and provider checks

PR15 merged through successful required checks as e78759090dad915af2df495b113da931acc20068. Main still requires strict regression and dependency-security checks, including administrators; force pushes and deletion remain disabled. Runtime-source comparison against accepted bbdfe07 changes only operator scripts, tests, package scripts, docs and workflows; no application/native handler changes. Post-merge main CI is recorded separately and must finish successfully, not be inferred from PR checks.

Read-only Firebase configuration confirms package com.passway.app and both Play app-signing and upload SHA256 certificates registered. Official provider defaults still require PLAY_RECOGNIZED even with NO_INTEGRITY as the explicit device threshold. License enforcement defaults false. No provider policy was changed and no genuine device verdict is claimed.

The live maintenance endpoint separately rejected missing and invalid credentials2/2. No authorized sweep, deletion job execution or cleanup SLA was exercised by those negative checks.

## Completed merged-main verification

Merged-main run39000055054 completed successfully: regression and dependency-security both pass. This includes the credential-free suites, both backend typechecks, database emulator suites, all-platform exports and the build-only web preview check. It is still not a real Store/device acceptance test.

Read-only production App Check inventory returned zero registered debug tokens with no additional page. No debug registration was revoked or changed. Cloud Functions v1/v2 inventory APIs returned SERVICE_DISABLED. No API was enabled or billing changed; that response is not asserted to prove no historical endpoint exists in any region.
