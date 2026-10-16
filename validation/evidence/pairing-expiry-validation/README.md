# Pairing-expiry correction: exact-source verification

Source `5f89b86fa1862b8566666de3749bd170aa458436`. New evidence only; previous-revision passes are not inherited.

- Reproduced 15 unit failures and 15 real Firestore transaction failures before changing handlers.
- Full independent CI: 451 regression cases, both TypeScript checks, Android/iOS/web exports passed.
- Static security: completed, zero SARIF results (not a security guarantee).
- Guarded live API preview against real Firebase: 57/57, including all 15 new persisted-expiry corruptions. Separate nonallowlisted-identity and cleanup checks: 3/3.
- Strict guarded preview: 6/6 missing/invalid attestation rejections; inert SMS key and malformed payload only. No SMS sent.
- Dependency mitigation conformance: Forge 829 pass, 4 pre-existing pending; braces 899 pass; raw registry audit remains NOT clean.
- Bounded local Firestore workload: 16 pairs, 160 message intents, 320 send/replay calls, all five invariants passed. This is not production capacity.
- Fresh extended native CI FAILED: peer displayed Connection ended instead of composer; 16 passing checks, then failure, no completion markers. A reproduced client cache-snapshot race is being corrected in a subsequent source revision.

Synthetic fixture cleanup used three bounded message-delete batches and completed in 13,237ms. This changes only the local probe cleanup, not production retention. It is not an Android speed-up claim.

## Release remains blocked

No positive genuine Play-installed attestation or full authenticated production acceptance; Google CLI is not authenticated. Current production fails the strict negative-attestation error contract. No production API/rules promotion, public release, billable upgrade, real-user mutation, real SMS or relaxation of app security was performed.

Only selected sanitized JSON is included. No private configs, tokens, service-account keys or raw authentication dumps.
