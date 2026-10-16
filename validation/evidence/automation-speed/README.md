# Native driver post-action readback optimization

Same immutable app source8a6d79da24454e5373e5b89d34df279b067a1993 / archiveb5bd74a87f8392b9a3a86de52685595aae7dfaee29148a2d6d4a9043c791deb5.

Baseline native run38894446875:75PASS, coordinator1037.54s,779instrumentation calls/644.34s. Driver discarded the native probe's fresh post-action hierarchy and repeated Python sleeps/read instrumentation. Java probe already waits500ms after actions and reacquires the hierarchy.

Optimization: return fresh touch hierarchy; verify setText using its fresh post-action hierarchy rather than discarding it. Never reuse a pre-action snapshot. On mismatch keep all four fresh-read retries. Preserve visible/enabled action targeting, nested deadlines, screenshot assertions,75journeys, one-attempt coordinator, completion markers and test isolation. No app code, Java probe, waits in the journeys, fixture/server logic, production API, signing configuration or acceptance gate changed.

Six new driver regressions; before:19cases/4failures; after:all67harness cases pass. The pre-action-tree rejection and mismatch retry tests remain explicit. Unit verification is not measured native speed improvement. Fresh hosted75assertion comparison is required; no performance or production-readiness claim before inspecting it. Different runner noise limits causal wall-clock comparison; instrumentation call-count reduction is deterministic evidence.
