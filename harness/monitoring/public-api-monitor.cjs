// Credential-free production boundaries only. No valid phone, OTP or user token.
const { runChecks, readBoundedJson: boundedJson, MAX_BYTES } = require('./deployed-contract.cjs');
async function monitor({ fetchImpl = fetch, now = () => performance.now() } = {}) {
  const report = await runChecks({ fetchImpl, now });
  return { schemaVersion: 2, checkedAt: new Date().toISOString(), ...report,
    limitations: 'Negative App Check contract only. Not positive attestation, SMS delivery, authenticated health, uptime SLA or production certification.' };
}
module.exports = { monitor, boundedJson, MAX_BYTES };
if (require.main === module) monitor().then(report => {
  require('fs').writeFileSync('public-api-health.json', JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report)); process.exitCode = report.pass ? 0 : 1;
}).catch(() => { console.error('Monitor execution failed; no health acceptance.'); process.exitCode = 1; });
