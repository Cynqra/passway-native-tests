const {createRequire}=require('node:module'),fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
if(process.env.FIRESTORE_EMULATOR_HOST!=='127.0.0.1:8080'||process.env.GCLOUD_PROJECT!=='demo-passway'||process.env.FIREBASE_SERVICE_ACCOUNT||process.env.GOOGLE_APPLICATION_CREDENTIALS)throw Error('Local demo-only guard failed');
process.env.MODERATION_PROVIDER='rules';process.env.METADATA_SERVER_DETECTION='none';
const app=path.resolve(process.env.PASSWAY_FUNCTIONS_DIR||'functions');
const source=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../validation/architecture-provenance.json')));
assert.match(source.sourceCommit,/^[a-f0-9]{40}$/);
const req=createRequire(path.join(app,'package.json'));
const firebase=require(app+'/lib/lib/firebase');
const {sendMessage,getMessages}=require(app+'/lib/handlers/messages');
const {blockUser}=require(app+'/lib/handlers/reports');
const {deleteAccount}=require(app+'/lib/handlers/accounts');
const {acceptContentPolicy}=require(app+'/lib/handlers/contentPolicy');
const {CONTENT_POLICY_VERSION:policyVersion}=require(app+'/lib/lib/contentPolicy');
const {getApps}=req('firebase-admin/app');const {performance}=require('node:perf_hooks');
// Synthetic verified-phone fixtures exist only behind the strict local demo guard above.
const syntheticPhone=uid=>{const m=/^bounded-([ab])(\d+)$/.exec(uid);if(!m)throw Error('Unknown workload fixture');return '+1555555'+String(Number(m[2])*2+(m[1]==='b'?1:0)).padStart(4,'0');};
const call=(fn,uid,data)=>fn.run({auth:{uid,token:{phone_number:syntheticPhone(uid)}},data});const db=firebase.db;
const out={sourceCommit:source.sourceCommit,scope:'Bounded in-process handler workload against local Firestore emulator. Not HTTP, native-device, production capacity, SMS or attestation proof.',pairs:16,syntheticParticipants:32,uniqueMessageIntents:160,sendCallsIncludingReplays:320,checks:[],latencyMs:{}};
function check(name,condition){assert.ok(condition,name);out.checks.push({name,pass:true});}
function quantiles(xs){xs.sort((a,b)=>a-b);return{samples:xs.length,p50:Math.round(xs[Math.ceil(xs.length*.5)-1]*100)/100,p95:Math.round(xs[Math.ceil(xs.length*.95)-1]*100)/100,max:Math.round(xs[xs.length-1]*100)/100};}
(async()=>{
 const start=performance.now(),batch=db.batch(),now=Date.now();
 const pairs=Array.from({length:16},(_,i)=>({a:'bounded-a'+i,b:'bounded-b'+i,c:'bounded-chat'+i}));
 for(const p of pairs){for(const uid of[p.a,p.b])batch.create(db.collection('users').doc(uid),{userId:uid,status:'active',ageConfirmedAt:now,createdAt:now,automatedTest:true});batch.create(db.collection('connections').doc(p.c),{connectionId:p.c,userA:p.a,userB:p.b,status:'active',createdAt:now,lastActivityAt:now});}
 await batch.commit();await Promise.all(pairs.flatMap(p=>[p.a,p.b].map(uid=>call(acceptContentPolicy,uid,{version:policyVersion,accept:true}))));check('All synthetic workload identities explicitly accept the current server policy',true);const sends=[],reads=[];
 await Promise.all(pairs.map(async p=>{
  for(let n=0;n<10;n++){const uid=n%2?p.b:p.a,data={connectionId:p.c,content:'Bounded synthetic intent '+n,clientMessageId:'bounded-intent-'+p.c+'-'+String(n).padStart(4,'0')};const t=performance.now();const first=await call(sendMessage,uid,data);const replay=await call(sendMessage,uid,data);assert.deepEqual(replay,first);sends.push(performance.now()-t);}
  for(const uid of[p.a,p.b]){const t=performance.now(),r=await call(getMessages,uid,{connectionId:p.c});reads.push(performance.now()-t);assert.equal(r.messages.length,10);assert.equal(new Set(r.messages.map(m=>m.messageId)).size,10);}
  assert.equal((await db.collection('connections').doc(p.c).collection('messages').get()).size,10);
 }));check('All 160 distinct messages persisted exactly once despite 320 send/replay calls',true);check('Both directions of all 16 conversations read all ten unique messages',true);
 await Promise.all(pairs.slice(0,8).map(async p=>{await call(blockUser,p.b,{connectionId:p.c});await assert.rejects(call(sendMessage,p.a,{connectionId:p.c,content:'Must fail',clientMessageId:'bounded-block-denied-'+p.c}));await assert.rejects(call(getMessages,p.a,{connectionId:p.c}));}));check('Eight blocked conversations reject later sends and reads',true);
 await Promise.all(pairs.slice(8).map(async p=>{const r=await call(getMessages,p.a,{connectionId:p.c});assert.equal(r.messages.length,10);}));check('Eight unrelated conversations remain readable after other pairs block',true);
 const oldAuth=firebase.auth;firebase.auth={deleteUser:async()=>{}};try{await Promise.all(pairs.map(async p=>{const r=await call(deleteAccount,p.a,{});assert.equal(r.pending,false);assert.equal((await db.collection('users').doc(p.a).get()).exists,false);assert.equal((await db.collection('accountDeletions').doc(p.a).get()).data().status,'complete');await assert.rejects(call(getMessages,p.b,{connectionId:p.c}));}));}finally{firebase.auth=oldAuth;}
 check('Sixteen parallel account deletions complete without leaving peer read access',true);
 out.latencyMs.sendPlusReplay=quantiles(sends);out.latencyMs.read=quantiles(reads);out.elapsedSeconds=Math.round((performance.now()-start)/10)/100;out.passed=true;
})().catch(e=>{out.passed=false;out.failure={type:e.name,code:e.code||null,message:String(e.message).slice(0,180)};process.exitCode=1;}).finally(async()=>{fs.writeFileSync(path.resolve(process.env.PASSWAY_WORKLOAD_RESULTS||'bounded-workload-results.json'),JSON.stringify(out,null,2));await db.terminate();await Promise.all(getApps().map(a=>a.delete()));console.log(JSON.stringify(out));});
