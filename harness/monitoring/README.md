# Public API security-contract monitor

Hourly credential-free negative tests against the fixed public API only. Eight invalid/missing App Check cases, no valid phone, OTP, user token, SMS sends or authenticated mutation. Requests have a 15-second total abort deadline, reject redirects and cap response JSON at64KiB. Output excludes response bodies and exception text. Latency is observed, not a proven SLO.

The deployed-contract helper is an exact copy from app source ec65e826e456f406a9087da843c4d4d6425d886d. This monitor does not deploy app source or inherit acceptance of another revision. A failing current public deployment MUST remain red; do not loosen expectations to match it.

GitHub Actions failure notifications follow the repository subscriber's settings; email receipt has not been tested. Scheduled runs depend on GitHub availability and may be delayed. This is not retention/backlog monitoring, authenticated two-user synthetic coverage, positive Store attestation or production certification. No paid services enabled; public-repository standard runner only. PR runs exercise local monitor tests, not live endpoints. Schedule becomes active on default branch only.
