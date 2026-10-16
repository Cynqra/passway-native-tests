const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
if (process.env.GOOGLE_APPLICATION_CREDENTIALS) throw new Error('Refusing explicit service-account credentials');
Object.assign(process.env, {GCLOUD_PROJECT:'demo-passway',FIRESTORE_EMULATOR_HOST:'127.0.0.1:8080',MODERATION_PROVIDER:'rules',METADATA_SERVER_DETECTION:'none'});
const base = path.resolve(process.argv[2] || '/data/passway-source-live/passway-app/functions');
const { MemoryFirestore } = require(path.join(base,'test/support.cjs'));
const firebase = require(path.join(base,'lib/lib/firebase'));
const {sendMessage} = require(path.join(base,'lib/handlers/messages'));
const now=Date.UTC(2026,9,16,12),retention=72*3600000;
const candidates=[NaN,Infinity,-Infinity,undefined,null,'1760000000000',{},new Date(now),0,-1,now,now-1,now+1,now-retention,now-retention+1,now-retention-1,Number.MAX_VALUE];
let state=0x50a55eed; const next=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return state>>>0;};
for(let i=0;i<2048;i++) candidates.push(now+(next()%(retention*4))-retention*2);
const realNow=Date.now, realFetch=global.fetch;
let networkCalls=0,accepted=0,rejected=0;
Date.now=()=>now;global.fetch=async()=>{networkCalls++;throw new Error('Network forbidden');};
(async()=>{try {
 for(const stamp of candidates){
  const db=new MemoryFirestore().seed('users/a',{status:'active',ageConfirmedAt:1}).seed('users/b',{status:'active',ageConfirmedAt:1}).seed('connections/chat',{userA:'a',userB:'b',status:'active',createdAt:now-1000}).seed('connections/chat/messages/target',{sentAt:stamp,content:'Synthetic original',senderId:'b'});
  firebase.db=db;
  const eligible=typeof stamp==='number'&&Number.isFinite(stamp)&&stamp>now-retention&&stamp<=now;
  let error;try{await sendMessage.run({auth:{uid:'a'},data:{connectionId:'chat',content:'Synthetic model reply',replyTo:'target'}});}catch(e){error=e;}
  const writes=[...db.values.entries()].filter(([p])=>p.startsWith('connections/chat/messages/')&&!p.endsWith('/target'));
  if(eligible){assert.equal(error,undefined);assert.equal(writes.length,1);accepted++;}
  else{assert.equal(error?.code,'failed-precondition');assert.equal(writes.length,0);assert.equal(db.read('connections/chat').lastActivityAt,undefined);rejected++;}
 }
 assert.equal(networkCalls,0);
 const result={sourceCommit:'bc5a5918719cb22ea6e915e09c5d7281a5d15ca7',scope:'Actual compiled sendMessage handler, in-memory transactional fixture; not live Firebase or native E2E',seed:'0x50a55eed',trials:candidates.length,accepted,rejected,networkCalls,passed:true};
 fs.writeFileSync(path.resolve(process.argv[3] || 'reply-time-model-result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
}finally{Date.now=realNow;global.fetch=realFetch;}})().catch(e=>{console.error(e);process.exitCode=1;});
