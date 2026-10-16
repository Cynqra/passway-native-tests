# Real hosted staging verification — ec65e82

This is additional hosted-cloud evidence, not production acceptance.

- Source: `ec65e826e456f406a9087da843c4d4d6425d886d`; unchanged from the 634-case clean and 81-case Android14/16 native candidate. Every deployed `src/**/*.ts` hash matches that candidate in both previews.
- Protected original API entrypoint: **16/16** checks passed. Missing/invalid App Check rejected on six callable routes. Four OTP routes intentionally disabled (404), not proof of OTP attestation or SMS delivery. Cron omitted. No authenticated mutation was sent to this preview.
- Separate diagnostic preview: **40/40** assertions passed through real hosted HTTP, real Firebase Auth and real Firestore. Exact two-disposable-UID guard, one-hour expiration, OTP routes and maintenance/cron removed; App Check explicitly OFF only in this preview. This is **not positive attestation proof**.
- Includes code generation, self/remote-code denial, redemption and acceptance, four concurrent lost-ACK retries recovering one request, changed-intent rejection, recovery after acceptance, bidirectional server reads, exactly-once retries including eight concurrent sends, message expiry/replies, malformed/underage/account-state denial, person-level blocking across channels, connection ending, and both account deletions.
- All disposable fixture Auth accounts and participant-owned database documents independently checked absent after cleanup. The diagnostic deployment was deleted after testing. Production deployment remained `dpl_HwzmiRmbLnjuwvZTnWYPpZFooKEe` throughout; no production release/rule/policy mutation.
- All three required composite indexes are READY, including deletion jobs. Both message-expiry query indexes are READY. Native Firestore TTL is not configured; transactional cleanup is the retention mechanism. Do not enable TTL blindly: the cleanup code rechecks/repairs parent evidence holds transactionally.
- Android registration and upload/Play certificate fingerprints are readable. Effective Play Integrity policy permits NO_INTEGRITY devices, requires PLAY_RECOGNIZED by default, and does not require LICENSED by default. Configuration is not a positive Store-installed verdict. No policy strengthening was performed without device acceptance.

## Remaining release boundary

The live production API remains older and fails the earlier 8-case negative contract (including missing getMessages). Do not promote the fixture wrapper or deploy deny-body-read rules in isolation. Complete controlled client/API/rule migration, genuine Play-installed positive App Check, real 2factor delivery and sign-in acceptance, monitoring/backlog budgets, and residual upstream dependency risk disposition. The Google AI Pro/Argon review and clean emulator tests do not close these gates. No billing or paid API enablement occurred.

## Stronger token-enforced hosted verification

A subsequent protected two-account preview, using the identical source modules, passed **43/43** assertions with `ENFORCE_APP_CHECK=true`. Requests used a real Firebase-issued **ADMIN custom App Check token**, not a debug bypass. Authenticated requests with missing/invalid App Check were explicitly rejected. This repeats the 40-case journey under token enforcement; do not count repeated cases as 83 unique cases. Both fixture users/documents were independently confirmed removed and that preview was deleted.

## Unpromoted production-configuration backend

The complete original backend (including original API entrypoint and configuration) was deployed with `--prod --skip-domain`, consuming existing production environment settings, with no security bypass or SMS override. Immutable candidate: `dpl_2hWYWikzCJmK5vchMXNRgh9rwQWa`.

- **8/8** actual production-configuration missing/invalid App Check rejection checks passed, including OTP routes and getMessages. This is the candidate's unique deployment URL, **not the public live API**.
- **4/4** checks with the Firebase-issued ADMIN App Check token passed: missing/invalid Firebase Auth rejected, malformed OTP send/verify inputs rejected before provider/database work. No SMS, Auth users or Firestore records were created by these four checks.
- Native Play-installed attestation and actual SMS delivery were **not** verified by admin tokens. Do not use this as Store acceptance.
- Tooling defect caught: Admin SDK `createToken()` already performs the custom-token exchange. An initial diagnostic mistakenly exchanged its result again and received403 `App attestation failed`. After inspecting SDK implementation, the duplicate exchange was removed; all four actual server checks passed. This was a diagnostic harness error, not evidence that native Play Integrity is broken. The failed diagnostic is retained.
- Vercel left the public app API alias unchanged, but automatically assigned its secondary project-scoped alias to the candidate despite `--skip-domain`. The secondary alias was explicitly restored. Both aliases were independently verified pointing to the existing live deployment. A promotion request for the old deployment returned409 because it was already current; no promotion of the candidate occurred. Do not assume skip-domain alone preserves every alias.
- Both live aliases remain on `dpl_HwzmiRmbLnjuwvZTnWYPpZFooKEe`. The candidate is retained without either live alias for further acceptance. Old live production contract failure is NOT relabeled as fixed.

## Controlled cutover sequence, not blanket approval

1. Preserve both old alias mappings and production deployment ID. Confirm all candidate/module/config provenance and indexes match this evidence.
2. Complete genuine Play-installed signed-client/App Check and 2factor delivery acceptance in the internal release process; an admin token cannot close either gate. Keep public Store rollout blocked.
3. Coordinate secure-client availability, API promotion, minimum-client upgrade communication and deny-body-read rules. Old direct-read clients must not be left silently incompatible.
4. Verify the public alias's real negative gate after cutover, plus authenticated two-user/foreground/expiry/deletion behavior. Roll back API aliases if operational checks fail, but do not silently restore privacy-insecure rules as a compatibility fallback.
5. Establish and exercise retention/deletion backlog, error/latency and SMS-budget alerts; resolve or explicitly disposition remaining upstream dependency risk before public release.

Current status: **production candidate validated more deeply; production readiness NOT accepted**. No paid service or billing was enabled.
