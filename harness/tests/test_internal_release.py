import hashlib
import importlib.util
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]))
import internal_release as m

class InternalReleaseTests(unittest.TestCase):
    def setUp(self):
        self.bundle=b'fictional signed artifact test bytes'
        self.digest=hashlib.sha256(self.bundle).hexdigest()
        self.meta={'package':'com.passway.app','versionCode':7,'versionName':'0.3.1'}
        self.calls=[]
    def send(self,url,**kw):
        self.calls.append((url,kw))
        if url==m.PUBLISHER:return {'id':'123'}
        if url.endswith('/tracks'):return {'tracks':[{'track':'internal','releases':[{'versionCodes':['6']}]}]}
        if 'uploadType=media' in url:return {'versionCode':7,'sha256':self.digest}
        return {}
    def test_internal_only_validated_commit(self):
        r=m.publish_internal('fictional-token',self.meta,self.bundle,self.digest,self.send)
        self.assertTrue(r['editCommitted']);self.assertFalse(r['publicProductionRollout']);self.assertFalse(r['storeInstallationOrPositiveAttestationVerified'])
        writes=[(u,k) for u,k in self.calls if k.get('method')=='PUT']
        self.assertEqual(len(writes),1);self.assertTrue(writes[0][0].endswith('/tracks/internal'));self.assertEqual(writes[0][1]['body']['track'],'internal')
        self.assertTrue(self.calls[-2][0].endswith(':validate'));self.assertTrue(self.calls[-1][0].endswith(':commit'))
    def test_invalid_package_hash_and_version_denied_before_network(self):
        for meta,digest in [({**self.meta,'package':'wrong'},self.digest),({**self.meta,'versionCode':True},self.digest),(self.meta,'0'*64)]:
            with self.assertRaises(m.SafeError):m.publish_internal('x',meta,self.bundle,digest,lambda *a,**k:self.fail('network'))
    def test_released_version_cannot_be_reused_and_edit_is_deleted(self):
        def send(url,**kw):
            if url.endswith('/tracks'):return {'tracks':[{'releases':[{'versionCodes':['7']}]}]}
            return self.send(url,**kw)
        with self.assertRaises(m.SafeError):m.publish_internal('x',self.meta,self.bundle,self.digest,send)
        self.assertEqual(self.calls[-1][1]['method'],'DELETE');self.assertFalse(any('uploadType' in u for u,k in self.calls))
    def test_wrong_uploaded_digest_never_updates_track(self):
        def send(url,**kw):
            if 'uploadType=media' in url:return {'versionCode':7,'sha256':'wrong'}
            return self.send(url,**kw)
        with self.assertRaises(m.SafeError):m.publish_internal('x',self.meta,self.bundle,self.digest,send)
        self.assertFalse(any(k.get('method')=='PUT' for u,k in self.calls));self.assertEqual(self.calls[-1][1]['method'],'DELETE')
    def test_failed_track_update_does_not_commit_and_cleans_edit(self):
        def send(url,**kw):
            if kw.get('method')=='PUT':raise m.SafeError('fictional failed write')
            return self.send(url,**kw)
        with self.assertRaises(m.SafeError):m.publish_internal('x',self.meta,self.bundle,self.digest,send)
        self.assertFalse(any(':commit' in u for u,k in self.calls));self.assertEqual(self.calls[-1][1]['method'],'DELETE')
    def test_wrong_workflow_branch_source_status_or_repository_denied(self):
        r={'status':'completed','conclusion':'success','event':'workflow_dispatch','head_sha':'a'*40,'head_branch':m.BRANCH,'path':'.github/workflows/passway-fresh-native-smoke.yml','head_repository':{'full_name':m.REPO}}
        m.trusted_run(r,'a'*40,'passway-fresh-native-smoke.yml')
        for k,v in [('status','in_progress'),('conclusion','failure'),('event','pull_request'),('head_sha','b'*40),('head_branch','main'),('path','different.yml'),('head_repository',{'full_name':'untrusted/repo'})]:
            with self.subTest(k=k), self.assertRaises(m.SafeError):m.trusted_run({**r,k:v},'a'*40,'passway-fresh-native-smoke.yml')
