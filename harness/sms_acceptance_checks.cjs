'use strict';
// Test evidence only; NEVER an authentication implementation or JWT verifier.
// Call only after Firebase Admin verifyIdToken(token, true) succeeds.
function verifiedSessionChecks({tokenVerified, claims, persisted, account, phone, projectId}) {
 return {
  firebaseSignatureExpiryAndRevocationValid: tokenVerified===true,
  storedUidMatchesVerifiedSubject: typeof claims?.uid==='string'&&claims.uid===persisted?.uid,
  verifiedPhoneMatchesRequested: typeof phone==='string'&&claims?.phone_number===phone,
  storedPhoneMatchesRequested: typeof phone==='string'&&persisted?.phone===phone,
  existingPhoneAccountMatchesVerifiedSubject: typeof claims?.uid==='string'&&account?.uid===claims.uid&&account?.phoneNumber===phone,
  projectAudienceMatches: typeof projectId==='string'&&claims?.aud===projectId,
  customTokenProviderConfirmed: claims?.firebase?.sign_in_provider==='custom',
 };
}
module.exports={verifiedSessionChecks};
