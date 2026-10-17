# Connection cache transition correction

Source `54b72953b0a9f3ea0748b3323631227b1d88f7b4`; parent native run 38885268149 **failed**, captured peer Connection ended after acceptance. No completion markers.

Fourteen tests of the real transpiled screen components: parent 5 pass/9 fail, corrected 14 pass/0 fail. Cache-only missing documents are not authoritative closure; metadata-only server transitions are requested; stale callbacks are retired; accepted-request navigation is deduplicated. Confirmed deletion/ending/decline and listener errors remain fail closed. No relaxed security rules, offline body fallback, increased test wait or driver changes.

Complete corrected local gate passed: **127 mobile + 223 backend + 35 rules + 80 real Firestore integration = 465**; TypeScript checks and Android/iOS/web exports passed. Independent exact-source CI passed the same 465 cases and all platform exports. Static analysis completed with zero SARIF results. Fresh native run **38887947192 passed 75/75 assertions**; artifact source/archive, exit code 0 and both fresh completion markers independently verified. The same peer acceptance/two-way messaging journey that failed on the parent now passes.

Entire backend Git tree and all 27 deployed source hashes equal the prior revision, so previous 57 live + 3 isolation/cleanup + 6 negative-attestation checks are retained only for those unchanged backend bytes; they were not newly executed against this client commit. No previous native/client pass inherited.

Production acceptance remains blocked on genuine Play-installed positive attestation, authenticated production flow and coordinated rollout. Raw registry audit remains NOT clean; reviewed hash-bound build-tool fixes and their conformance evidence are separate from upstream advisory resolution.


Native flow controller duration: 979.30 seconds. Its 779 instrumentation calls account for 588.18 seconds; this is test-driver overhead, not app response latency. No native-driver optimization was implemented and no causal speedup claim is made. Previous parent failure remains preserved.
