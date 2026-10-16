const {test}=require('node:test'),assert=require('node:assert/strict');
const {monitor,boundedJson,MAX_BYTES}=require('./public-api-monitor.cjs');
const ok=()=>Response.json({error:{status:'UNAUTHENTICATED',message:'This app could not be verified.'}},{status:401});
test('all 26 fixed safe fixtures; no authentication or real SMS data; bounded no-redirect transport',async()=>{
 const calls=[];const r=await monitor({fetchImpl:async(u,o)=>{calls.push([u,o]);return ok();}});
 assert.equal(r.pass,true);assert.equal(calls.length,26);
 for(const [u,o]of calls){assert.equal(new URL(u).origin,'https://passway-api.vercel.app');assert.equal(o.redirect,'error');assert.ok(o.signal);assert.equal(o.method,'POST');assert.equal(o.headers.authorization,undefined);assert.ok(!/\d{10}/.test(o.body));}
 assert.ok(r.checks.every(c=>Number.isInteger(c.durationMs)&&c.durationMs>=0));
});
test('old contract 400, wrong 401 and missing getMessages cannot become green',async()=>{
 for(const status of [200,400,401,404,500]){
  const r=await monitor({fetchImpl:async()=>Response.json({error:{message:'private-secret'}},{status})});
  assert.equal(r.pass,false);assert.ok(!JSON.stringify(r).includes('private-secret'));
 }
});
test('transport, oversized, non-JSON bodies fail closed without disclosure',async()=>{
 for(const impl of [async()=>{throw new Error('private-token');},async()=>new Response('s'.repeat(MAX_BYTES+1)),async()=>new Response('private-html')]){
  const r=await monitor({fetchImpl:impl});assert.equal(r.pass,false);assert.ok(!JSON.stringify(r).includes('private-'));
 }
});
test('exact body ceiling succeeds; oversized body rejected',async()=>{
 assert.deepEqual(await boundedJson(new Response(' '.repeat(MAX_BYTES-2)+'{}',{headers:{'content-type':'application/json'}})),{});
 await assert.rejects(boundedJson(new Response(' '.repeat(MAX_BYTES+1),{headers:{'content-type':'application/json'}})));
});


test('all eleven current callables and both production SMS routes are covered', async () => {
 const report=await monitor({fetchImpl:async()=>ok()});
 const expected=['otpSend','otpVerify','generateTid','redeemTid','deactivateTid',
  'respondToRequest','endConnection','sendMessage','getMessages','fileReport',
  'blockUser','confirmAge','deleteAccount'];
 assert.deepEqual([...new Set(report.checks.map(c=>c.route))],expected);
 for(const route of expected)assert.deepEqual(report.checks.filter(c=>c.route===route).map(c=>c.token),['missing','invalid']);
});

test('concurrent probes bind timings to their own route rather than completion order', async () => {
 let active=0,peak=0;
 const report=await monitor({fetchImpl:async url=>{
  active++;peak=Math.max(peak,active);
  await new Promise(resolve=>setTimeout(resolve,url.endsWith('/otpSend')?30:1));
  active--;return ok();
 }});
 assert.ok(peak>1 && peak<=4);
 const slow=report.checks.filter(c=>c.route==='otpSend');
 assert.ok(slow.every(c=>c.durationMs>=25));
 assert.equal(report.checks.length,26);assert.equal(report.pass,true);
});

test('no retry hides a failed probe and no response body is retained', async () => {
 const calls=new Map();
 const report=await monitor({fetchImpl:async(url,options)=>{
  const key=url+String(options.headers['x-firebase-appcheck']);
  calls.set(key,(calls.get(key)||0)+1);
  if(url.endsWith('/deleteAccount'))throw Error('private-credential');
  return ok();
 }});
 assert.equal(calls.size,26);assert.ok([...calls.values()].every(count=>count===1));
 assert.equal(report.pass,false);assert.equal(report.checks.filter(c=>!c.pass).length,2);
 assert.ok(!JSON.stringify(report).includes('private-credential'));
});

test('correct-looking JSON in an HTML media type is not accepted', async()=>{
 const r=await monitor({fetchImpl:async()=>new Response(JSON.stringify({error:{status:'UNAUTHENTICATED',
  message:'This app could not be verified.'}}),{status:401,headers:{'content-type':'text/html'}})});
 assert.equal(r.pass,false);
});
