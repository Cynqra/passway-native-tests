# Fail fast on a verified Play environment blocker

Eight regression cases fail before the implementation and pass afterward; all 80 harness tests pass. The exact recorded hierarchy and process logs from run 38904704772 replay as wrong-installer, outdated Play Services, and licensing-service-denied.

The offline actual-APK smoke now stops on the FIRST fresh hierarchy matching the observed Google Play error dialog when current app-process logs corroborate the failure. It preserves a FAIL result, no success marker, no positive attestation claim, and structured credential-free environment diagnostics. Unknown app errors retain a bounded timeout, not an invented environment classification. Successful onboarding does not read logs. Nested operations retain the shared 60-second deadline.

This does not repair the protected APK by disabling or spoofing licensing; the correct next environment is a supported, genuinely installed licensed Play device. No repeat of the known-incompatible emulator was launched to manufacture a green result. The APK8 binding remains unchanged; this modification is not version9 Store acceptance evidence.
