# Current Google Play artifact binding

The offline store UI workflow was still pinned to historical download run 38898141494, harness d9450fdd and version 8. A synthetic current version 13 artifact with exact package, hash and size was rejected solely because of the old version pin. Before evidence is retained outside this repository; this correction does not reinterpret prior failures as passes.

NVIDIA Nemotron Super proposed the strict download verifier. Independent integration adds numeric dispatch input validation, bounded trusted run lookup, exact same harness revision/repository/branch/workflow checks, file size bound and fresh regressions. The connected free inference endpoint was used; it was not an autonomous agent executing these tests.

The offline workflow now requires explicit download run ID, version and independently copied authenticated APK SHA256. The download run must be successful, completed, manually dispatched, from this repository's existing authorized branch and the exact current harness revision. Only its named Play APK artifact is fetched. Package/version/hash/size binding must pass. Actual APK signing certificate and compiled package/version are independently reverified before installation. No shell expressions are accepted as run IDs or versions, and artifact data cannot supply a new trusted hash.

The helper does not install, upload, mutate Play tracks, bypass security or claim attestation. Google Play licensing or outdated services remain environment failures, not accepted app behavior. A same revision authenticated download is required after integrating this harness change; do not reuse older harness receipts or rebuild the application source merely to silence a guard. The immutable application archive is unchanged.
