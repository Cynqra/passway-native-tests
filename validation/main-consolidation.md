# Validated harness consolidation into main

This merge combines canonical validation commit576bd184774516fbb8c8eaf9e95f892b8984a608 with default-branch monitoring commitd69573f136266488fe746ece3688fb42568eb4e4. It preserves the exact app source snapshot736d469c5b7b36be52bc31f2975431c38eb920e4 and its archive checksum. No app source, signed client, backend deployment, Google Play release or cloud permission is changed.

The combined fast CI runs all Python harness regressions and all Node monitor tests. The 28-probe monitor keeps consent-route coverage, strict no-store checks, bounded transport, credential-free invalid fixtures and no automatic retries. Existing signed-client/native results retain their original exact-source scope; merging the test repository is not a new device execution. Minor trailing whitespace in imported harness files is normalized.

Keyless Google release operations remain restricted by the existing federation policy to validation/isolated-current-native and its exact workflow identity. This consolidation does not broaden trust to main or copy release credentials. Use the documented trusted branch for those operations. Isolated validation and credential-free monitoring can run from main. The canonical branch remains available; superseded stacked PRs may be closed only after ancestry confirms their commits are included in main.
