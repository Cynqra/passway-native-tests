import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
import internal_sharing as m

class InternalSharingTests(unittest.TestCase):
    def setUp(self):
        self.bundle=b'fictional bundle, never uploaded';self.digest=hashlib.sha256(self.bundle).hexdigest()
        self.meta={'package':'com.passway.app','versionCode':10,'versionName':'0.3.4','sourceCommit':m.SOURCE,'sourceArchiveSha256':m.ARCHIVE}
        self.payload={'downloadUrl':'https://play.google.com/apps/test/fictional-private-canary','sha256':self.digest,'certificateFingerprint':'ab'*32}
        self.calls=[]
    def send(self,url,**kwargs):
        self.calls.append((url,kwargs));return self.payload
    def test_only_exact_accepted_upload_endpoint_no_edit_track_or_commit(self):
        with patch.object(m,'BUNDLE',self.digest):r=m.upload_shared('fictional-token',self.meta,self.bundle,self.digest,self.send)
        self.assertEqual(r['sha256'],self.digest);self.assertEqual(len(self.calls),1)
        self.assertEqual(self.calls[0][0],m.UPLOAD);self.assertNotIn('/edits',self.calls[0][0]);self.assertEqual(self.calls[0][1]['method'],'POST')
    def test_changed_package_version_source_or_archive_denied_before_network(self):
        for key,value in [('package','wrong'),('versionCode',True),('versionCode',11),('versionName','0.3.5'),('sourceCommit','a'*40),('sourceArchiveSha256','b'*64)]:
            with self.subTest(key=key,value=value),patch.object(m,'BUNDLE',self.digest),self.assertRaises(m.SafeError):m.upload_shared('x',{**self.meta,key:value},self.bundle,self.digest,lambda *a,**k:self.fail('network'))
    def test_changed_bundle_denied_before_network(self):
        with self.assertRaises(m.SafeError):m.upload_shared('x',self.meta,self.bundle,'0'*64,lambda *a,**k:self.fail('network'))
    def test_bad_links_hash_and_fingerprint_denied(self):
        for key,value in [('downloadUrl','https://evil.test/apps/test/x'),('downloadUrl','http://play.google.com/apps/test/x'),('downloadUrl','https://play.google.com@evil.test/apps/test/x'),('downloadUrl','https://play.google.com/apps/test/x?token=x'),('downloadUrl','https://play.google.com:444/apps/test/x'),('downloadUrl','https://play.google.com/other/x'),('sha256','0'*64),('certificateFingerprint','bad')]:
            self.payload={**self.payload,key:value}
            with self.subTest(key=key),patch.object(m,'BUNDLE',self.digest),self.assertRaises(m.SafeError):m.upload_shared('x',self.meta,self.bundle,self.digest,self.send)
            self.setUp()
    def test_archive_identity_is_explicit_and_not_inherited_for_new_source(self):
        p={'sourceRepository':'naveenbharti310/Paasway','sourceCommit':m.SOURCE,'archiveSha256':m.ARCHIVE};m.approved_provenance(p)
        for k,v in [('sourceRepository','evil/repo'),('sourceCommit','f'*40),('archiveSha256','0'*64)]:
            with self.assertRaises(m.SafeError):m.approved_provenance({**p,k:v})
    def test_encrypted_delivery_never_contains_plain_installation_link(self):
        key=pathlib.Path(__file__).parents[1]/'internal-sharing-recipient.pub'
        x=m.encrypt_delivery(self.payload,key);self.assertEqual(x['format'],'passway-private-canary-v1')
        self.assertNotIn(self.payload['downloadUrl'],json.dumps(x));self.assertNotIn('downloadUrl',x)

if __name__=='__main__':unittest.main()
