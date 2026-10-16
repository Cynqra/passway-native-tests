// Credential-free public API rejection monitor. No valid phone, OTP or user token.
const {runChecks}=require('./deployed-contract.cjs');
const MAX_BYTES=65536;
async function boundedJson(response){
  const reader=response.body?.getReader();
  if(!reader) throw new Error('Missing response');
  let bytes=0;const chunks=[];
  try{
    while(true){const {done,value}=await reader.read();if(done)break;
      bytes+=value.byteLength;if(bytes>MAX_BYTES)throw new Error('Oversized response');chunks.push(Buffer.from(value));}
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  }finally{await reader.cancel().catch(()=>{});}
}
async function monitor({fetchImpl=fetch,now=()=>performance.now()}={}){
  const observations=[];
  const report=await runChecks({fetchImpl:async(url,options)=>{
    const started=now();let status=null;
    try{
      const response=await fetchImpl(url,options);status=response.status;
      // Consume within the same AbortSignal deadline, cap bytes, never log bodies.
      const data=await boundedJson(response);
      return {status,json:async()=>data};
    }finally{observations.push({status,durationMs:Math.max(0,Math.round(now()-started))});}
  }});
  return {schemaVersion:1,checkedAt:new Date().toISOString(),...report,
    checks:report.checks.map((c,i)=>({...c,durationMs:observations[i].durationMs})),
    limitations:'Negative App Check contract only. Not positive attestation, SMS delivery, authenticated health, uptime SLA or production certification.'};
}
module.exports={monitor,boundedJson,MAX_BYTES};
if(require.main===module)monitor().then(report=>{
  require('fs').writeFileSync('public-api-health.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report));process.exitCode=report.pass?0:1;
}).catch(()=>{console.error('Monitor execution failed; no health acceptance.');process.exitCode=1;});
