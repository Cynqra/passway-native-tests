# Real SMS acceptance — unchanged ec65e82 source

One real 2factor SMS request, one successful OTP verification, and real Firebase custom-token login completed. Seven independent persisted-session/token/account identity checks passed. Existing user account retained; temporary browser login storage and diagnostic preview removed. No second SMS or account deletion.

The first harness assertion falsely required `localId` in the REST custom-token response. The original failed row is retained, not relabelled. Official response-schema evidence and independent signature/expiry/revocation/identity verification resolve that harness defect. Ten new harness regression cases cover correct identity validation and mismatch rejection.

Scope: unchanged PhoneAuthScreen in a temporary web diagnostic preview, original unpromoted production-configuration API candidate, test browser adapter attaching real ADMIN-issued App Check tokens and protected-deployment headers. This is actual SMS/authentication acceptance, **not** Play-installed native attestation, normal browser CORS acceptance, or public production deployment acceptance. No phone, OTP, token, UID or service-account key is published here.
