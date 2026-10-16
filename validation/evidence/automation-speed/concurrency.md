# Isolated workflow queue contention

Existing native concurrency key includes only mode. Version9 isolated run38905444007 queued behind version8 run38903889888, despite separate runners, per-run Auth/Firestore emulators and immutable app archives. This is queue delay, not app/emulator latency.

Candidate fix adds commit SHA only for isolated-native, isolated-extended and the equivalent default mode. Same-mode/same-revision duplicate tests remain serialized. Release modes retain their shared mode key and cancel-in-progress remainsfalse; no internal Play edit cancellation or parallel release mutation is enabled.

Prepared on a separate branch so frozen version9 acceptance/publication remains bound to revisionb144576. This does not retroactively remove the observed queue time or establish measured app latency. Merge into the testing branch only after the frozen release finishes.
