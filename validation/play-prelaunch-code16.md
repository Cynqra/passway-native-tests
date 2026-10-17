# Google Play prelaunch crawl for version 16

The existing `robo-diagnostic.json` is an orchestrated diagnostic, not a
self-contained release crawl. It assumes a seeded chat and a separate live
peer, and predates the explicit use-rules screen. Do not use it as evidence
that the current production release was tested.

`harness/play_prelaunch_script.py` creates a separate private configuration
from the already provisioned, reserved Firebase fictional reviewer accounts.
It does not change app source, the signed version16 bundle, backend policy,
App Check, licensing, permissions, billing or the production release track.
Keep the resulting JSON outside Git because it contains reusable fictional
verification values.

The new flow uses documented conditional contexts and bounded runs rather
than undocumented optional actions or long waits for an inactive test peer.
It handles onboarding, fictional verification, age onboarding if required,
explicit use-rules scrolling and acceptance if presented, Android foreground
permissions, one generated and cancelled code, and settings navigation.
Destructive account actions and unsolicited content are excluded from the
subsequent exploratory crawl. Scripted actions can still target an ignored
control, as specified by Google's Robo format.

Only generate and upload with the private fixture configuration for the
existing reviewer accounts. Generation and upload are not successful
execution. Inspect Google's resulting videos, screenshots, login reachability
and failures separately. This crawl cannot prove real SMS delivery,
two-device production acceptance, physical proximity or successful
production attestation by itself.

Format reference:
https://firebase.google.com/docs/test-lab/android/robo-scripts-reference