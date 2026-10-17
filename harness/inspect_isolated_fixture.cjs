// Test control plane: LOCAL demo services and four fictional phone identities only.
// No credential file, arbitrary UID, external host or production mutation accepted.
const fs = require('node:fs'), path = require('node:path');
if (process.env.GCLOUD_PROJECT !== 'demo-passway' ||
    process.env.FIRESTORE_EMULATOR_HOST !== '127.0.0.1:8080' ||
    process.env.FIREBASE_AUTH_EMULATOR_HOST !== '127.0.0.1:9099' ||
    process.env.FIREBASE_SERVICE_ACCOUNT || process.env.GOOGLE_APPLICATION_CREDENTIALS) {
  throw Error('Strict fixture isolation guard failed');
}
const input = JSON.parse(process.argv[2] || '{}');
const allowedPhones = ['9999900001', '9999900002', '9999900003', '9999900004'];
if (!['snapshot', 'expire', 'isolate-extra-fixture'].includes(input.action) ||
    !Array.isArray(input.phones) || !input.phones.length ||
    input.phones.some(p => !allowedPhones.includes(p)) ||
    (input.tid !== undefined && !/^[A-Z0-9]{4}$/.test(input.tid))) {
  throw Error('Unsupported fixture command');
}
if (input.action === 'expire' && !input.tid) throw Error('Expiry requires an owned code');
if (input.action === 'isolate-extra-fixture' &&
    (input.tid !== undefined || input.phones.length !== 1 || !['9999900003', '9999900004'].includes(input.phones[0]))) {
  throw Error('Unsupported fixture cohort command');
}
process.env.METADATA_SERVER_DETECTION = 'none';
const { createRequire } = require('node:module');
const req = createRequire(path.resolve('validation-source/passway-app/functions/package.json'));
const { initializeApp, getApps } = req('firebase-admin/app');
const { getFirestore } = req('firebase-admin/firestore'), { getAuth } = req('firebase-admin/auth');
initializeApp({ projectId: 'demo-passway' });
const db = getFirestore(), auth = getAuth();
const root = path.resolve(process.env.PASSWAY_RESULTS || 'native-results');
fs.mkdirSync(root, { recursive: true });
const mapPath = path.join(root, 'fictional-identities.json');
const identities = fs.existsSync(mapPath) ? JSON.parse(fs.readFileSync(mapPath)) : {};
const millis = v => v && typeof v.toMillis === 'function' ? v.toMillis() : null;
(async () => {
  const profiles = [];
  for (const phone of input.phones) {
    let user;
    try { user = await auth.getUserByPhoneNumber('+91' + phone); }
    catch (e) { if (e.code !== 'auth/user-not-found') throw e; }
    if (user) identities[phone] = user.uid;
    const uid = identities[phone];
    if (uid && !/^[A-Za-z0-9_-]{1,128}$/.test(uid)) throw Error('Invalid saved fixture identity');
    let profile = uid ? await db.collection('users').doc(uid).get() : null;
    if (input.action === 'isolate-extra-fixture') {
      if (!user || !profile?.exists || !['active', 'reported'].includes(profile.data()?.status) ||
          !(typeof profile.data()?.ageConfirmedAt === 'number' && profile.data().ageConfirmedAt > 0)) {
        throw Error('Only an existing eligible local fictional profile can be isolated');
      }
      await profile.ref.update({ automatedTest: true });
      profile = await profile.ref.get();
      if (profile.data()?.automatedTest !== true) throw Error('Fixture cohort readback failed');
    }
    const deletion = uid ? await db.collection('accountDeletions').doc(uid).get() : null;
    profiles.push({ phone, uid: uid || null, authExists: !!user, profileExists: !!profile?.exists,
      profileStatus: profile?.data()?.status || null, testCohortMarker: profile?.data()?.automatedTest === true,
      reservedReviewerBinding: ['9999900001', '9999900002'].includes(phone) && profile?.data()?.phoneHash ===
        require('node:crypto').createHash('sha256').update('passway:phone:+91' + phone).digest('hex'), displayName: profile?.data()?.displayName || null,
      deletionStatus: deletion?.data()?.status || null });
  }
  fs.writeFileSync(mapPath, JSON.stringify(identities, null, 2));
  const uids = profiles.map(p => p.uid).filter(Boolean);
  let code = null;
  if (input.tid) {
    const ref = db.collection('tids').doc(input.tid), snap = await ref.get(), data = snap.data();
    if (snap.exists && !uids.includes(data.generatorId)) throw Error('Code is not owned by selected fictional fixtures');
    if (input.action === 'expire') {
      if (!snap.exists || data.status !== 'active') throw Error('Only an active owned fixture code can expire');
      await ref.update({ expiresAt: Date.now() - 1000 });
      data.expiresAt = Date.now() - 1000;
    }
    if (snap.exists) code = { tid: snap.id, status: data.status, expiresAt: data.expiresAt };
  }
  const connections = [], requests = [], reports = [], blocks = [];
  for (const uid of uids) {
    const cs = await db.collection('connections').where('userA', '==', uid).get();
    for (const d of cs.docs) {
      const c = d.data();
      if (uids.includes(c.userB)) connections.push({ id: d.id, status: c.status, deleteAt: millis(c.deleteAt) });
    }
    const qs = await db.collection('connectionRequests').where('generatorId', '==', uid).get();
    for (const d of qs.docs) {
      const r = d.data();
      if ((!input.tid || r.tid === input.tid) && uids.includes(r.requesterId)) requests.push({ id: d.id, status: r.status });
    }
    const rs = await db.collection('reports').where('reporterId', '==', uid).get();
    for (const d of rs.docs) if (uids.includes(d.data().reportedId)) reports.push({ id: d.id, deleteAt: millis(d.data().deleteAt) });
    for (const other of uids) if (uid !== other && (await db.collection('blocks').doc(uid + ':' + other).get()).exists) blocks.push(uid + ':' + other);
  }
  console.log(JSON.stringify({ profiles, code, connections, requests, reports, blocks, now: Date.now(),
    scope: input.action === 'expire' ? 'Owned emulator code expiry injected; no device-clock or production change' : input.action === 'isolate-extra-fixture' ? 'Only selected third/fourth local fictional profile marked isolated; no production change' : 'Read-only selected fictional fixture state' }));
})().catch(e => { console.error(e.code || e.message); process.exitCode = 1; })
  .finally(async () => { await db.terminate(); await Promise.all(getApps().map(a => a.delete())); });