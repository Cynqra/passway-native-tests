# Bounded backend workload, not a production capacity claim

`bounded_backend_workload.cjs` runs after the rules and transaction regressions
inside the same ephemeral Firestore emulator in architecture CI.

- Exact source comes from the SHA-256-verified architecture archive.
- Guards require localhost Firestore, `demo-passway`, and no explicit
  service-account or ADC credential file.
- Creates 16 chats and 32 synthetic participant profiles with create-only writes.
- Sends 160 distinct message intents, immediately replaying each: 320 calls.
- Both participants read all ten messages in each chat; persisted copies are
  checked for duplication.
- Blocks eight pairs and checks that unrelated pairs remain usable.
- Deletes 16 accounts in parallel and checks that peers lose body access.
- Records observed handler latency and total workload time in an artifact.

Firebase Auth deletion is a stub. No OTP, physical device, HTTP transport,
App Check, external moderation or push delivery is exercised. No production
load is generated. The latency numbers are local/CI observations, not an
application SLO or a forecast of real-service capacity.

Correctness failures fail the regression job; performance numbers are measured
rather than compared to an arbitrary hardware-dependent threshold. Run the
native and production-acceptance gates separately.