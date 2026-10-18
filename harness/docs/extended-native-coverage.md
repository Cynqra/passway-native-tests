# Extended native acceptance, with independent state assertions

Run the existing workflow with `mode=isolated-extended`. It retains the original
fresh APK, core two-user flow, keyboard and offline recovery checks, then reuses
the same emulator and two Android users for additional journeys. Four fictional
Firebase identities prevent needing to erase legitimate person-level blocks.

Additional journeys:

- Profile rename persisted in Firestore and after navigation.
- Cancel code button and Android Back both deactivate the exact server code.
- Canceled/expired code rejection through native UI, without pending requests.
- Decline, with server decision and peer editable-form recovery.
- Actual block submission, closed chats and blocked re-pairing without code consumption.
- Actual report submission, one stored report, person block and evidence retention.
- Cancel the Android account-deletion confirmation without side effects.
- Confirm deletion, remove Auth/profile, complete durable job, close the active
  chat and observe closure on the other native participant.
- Re-register the same fictional phone, receive a different Firebase UID and
  traverse the age gate again.
- Assert the corrected age-data disclosure is actually rendered.

Each case uses visible native controls; critical results also inspect the
specific fictional Auth/Firestore records. The inspector accepts only local
`demo-passway` services, no explicit cloud credentials, four fixed fictional
phone identities and `snapshot`/owned-code `expire` actions.

Expiry is fault-injected in an owned emulator code's server record. It proves
the native UI handles an expired server response; it does not fast-forward,
weaken, or certify the real five-minute on-screen countdown.

One immutable attempt: standard budget 900 seconds; extended budget 1500
seconds. Extended success requires its own newly written marker in addition to
the core completion marker. There is no live patch loop or automatic rerun.

This does not close real SMS, store-signed App Check, production migration,
physical-device or dependency-security release gates.