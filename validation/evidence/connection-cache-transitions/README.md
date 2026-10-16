# Connection cache transition correction

Source `54b72953b0a9f3ea0748b3323631227b1d88f7b4`; parent native run 38885268149 **failed**, captured peer Connection ended after acceptance. No completion markers.

Fourteen tests of the real transpiled screen components: parent 5 pass/9 fail, corrected 14 pass/0 fail. Cache-only missing documents are not authoritative closure; metadata-only server transitions are requested; stale callbacks are retired; accepted-request navigation is deduplicated. Confirmed deletion/ending/decline and listener errors remain fail closed. No relaxed security rules, offline body fallback, increased test wait or driver changes.

Complete corrected local gate passed: **127 mobile + 223 backend + 35 rules + 80 real Firestore integration = 465**; TypeScript checks and Android/iOS/web exports passed. Independent CI and fresh native are pending until artifacts are checked.

Entire backend Git tree and all 27 deployed source hashes equal the prior revision, so previous 57 live + 3 isolation/cleanup + 6 negative-attestation checks are retained only for those unchanged backend bytes; they were not newly executed against this client commit. No previous native/client pass inherited.

Production acceptance remains blocked on genuine Play-installed positive attestation, authenticated production flow and coordinated rollout. Raw registry audit remains NOT clean; reviewed hash-bound build-tool fixes and their conformance evidence are separate from upstream advisory resolution.
