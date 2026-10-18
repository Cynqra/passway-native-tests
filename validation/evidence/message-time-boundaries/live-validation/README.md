## Live continuation: exact-source backend bc5a591

Vercel authorization was restored. The previously blocked live phase has now executed; no historical preview result is being reused as proof for this backend revision.

- **42/42 live candidate backend checks passed** against a protected, exact-source preview and live Firebase. Uses newly created, automated-test fixture identities and custom-token sign-in, not SMS. Includes generation/redemption/acceptance, bidirectional persisted reads, eight concurrent retries creating one message, expired reads/replies, all five new malformed/future timestamp cases, unknown/under-age state rejection, cross-channel person blocks, ending, deletion and fixture cleanup.
- **3/3 separate access-boundary/cleanup checks passed**: a valid but nonallowlisted disposable identity was rejected before both generation and message reads; independent fixture absence was checked afterwards.
- **6/6 strict candidate negative-attestation checks passed** in a second protected preview. Original candidate HTTP/security handlers, `ENFORCE_APP_CHECK=true`, inert SMS-key fixture, malformed request payloads only, no maintenance/cron execution. This is missing/invalid token rejection, **not positive store-device attestation**.
- **Current production passed 0/6 strict rejection checks (all six failed)**: OTP routes returned 400 rather than App Check rejection; generation returned authentication failure rather than the expected App Check verification message. This failure remains visible as `release/production-app-check=failure`. No SMS was sent and no authenticated production mutation was made by these probes.
- Fresh keyless Play capability/readback succeeded: https://github.com/Cynqra/passway-native-tests/actions/runs/38881307717 . Temporary Play edit was deleted, internal version **7** confirmed, no public production release present, no bundle or track changed.
- Database/control-plane placement read back as `asia-south1`; candidate Functions `asia-south1` and Vercel `bom1` are aligned in Mumbai. No speculative region migration was made.

49 synthetic preview HTTP calls measured p50 1079 ms, p95 1917 ms, max 3002 ms, including network/cold-start/Auth/Firestore and the fixture wrapper's extra token verification. These are **not production/native response SLO measurements**. The earlier native-instrumentation overhead report remains separate.

All original source files in the first preview were independently hash-compared with bc5a591 before execution. Both previews remain protected and separate from the production alias. No production backend/rules cutover, App Check bypass in production, signing change, public release, real SMS, device reservation, or paid upgrade was performed.

### Remaining release boundary

The restored official Android CLI has no saved Google sign-in after the earlier local snapshot reset. Its supported Google browser authorization has been prepared; no paid/reserved device is waiting while sign-in is incomplete. Genuine Play-store installation/positive attestation and the full production two-user acceptance are still unverified. API/client/rules must be cut over together after those gates, not by weakening enforcement or deploying deny-read rules alone. Raw registry audit is still advisory-positive despite verified installed-code local remediation.

Durable sanitized evidence: `validation/evidence/message-time-boundaries/live-validation` on `Cynqra/passway-native-tests` branch `validation/isolated-current-native`, commit `2c8dc8c`.
