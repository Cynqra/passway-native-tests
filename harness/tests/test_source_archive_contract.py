"""A candidate snapshot, provenance, and sha256sum sidecar are one atomic contract."""
import hashlib,json,pathlib,unittest
ROOT=pathlib.Path(__file__).parents[2]
class SourceArchiveContract(unittest.TestCase):
 def test_actual_archive_matches_provenance_and_shell_sidecar(self):
  archive=ROOT/'validation/architecture-source.tar.gz'
  digest=hashlib.sha256(archive.read_bytes()).hexdigest()
  provenance=json.loads((ROOT/'validation/architecture-provenance.json').read_text())
  sidecar=(ROOT/'validation/architecture-source.sha256').read_text().split()
  self.assertEqual(sidecar,[digest,'validation/architecture-source.tar.gz'])
  self.assertEqual(provenance['archiveSha256'],digest)
  self.assertEqual(provenance['sourceRepository'],'naveenbharti310/Paasway')
  self.assertRegex(provenance['sourceCommit'],r'^[0-9a-f]{40}$')
  self.assertRegex(provenance['sourceTree'],r'^[0-9a-f]{40}$')
