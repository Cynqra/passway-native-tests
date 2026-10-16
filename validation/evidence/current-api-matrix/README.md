# Current-source Android coverage, not historical APK reuse

The current-source isolated native workflow now accepts only API 34, 35 or 36 (default 36). Before installing/testing it verifies the actual booted API equals the selected API and stores the observed value. Isolated queues are keyed by source revision AND API. Release/cloud modes still share their existing serialized keys; API input cannot split release locks.

Two new/updated configuration regressions fail before the change and pass after; all 81 harness tests pass locally. An API34 extended run must independently establish 75 passing checks and fresh completion markers for the same source archive before any Android14 result is claimed. No older prebuilt APK or historical native suite can substitute for the current-source run. Existing version9/API36 acceptance remains attached to its immutable prior run.
