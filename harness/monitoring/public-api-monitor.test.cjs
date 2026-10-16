const {test}=require('node:test'),assert=require('node:assert/strict');
const {monitor,boundedJson,MAX_BYTES}=require('./public-api-monitor.cjs');
const ok=()=>Response.json({error:{status:'UNAUTHENTICATED',message:'This app could not be verified.'}},{status:401});
test('eight fixed safe fixtures; no authentication or real SMS data; bounded no-redirect transport',async()=>{
 const calls=[];const r=await monitor({fetchImpl:async(u,o)=>{calls.push([u,o]);return ok();}});
 assert.equal(r.pass,true);assert.equal(calls.length,8);
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
 assert.deepEqual(await boundedJson(new Response(' '.repeat(MAX_BYTES-2)+'{}')),{});
 await assert.rejects(boundedJson(new Response(' '.repeat(MAX_BYTES+1))));
});
