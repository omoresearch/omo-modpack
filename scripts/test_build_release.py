import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from build_release import build


class BuilderTests(unittest.TestCase):
    def setUp(self):
        # Synthetic unit fixture only. Not a real mod, launcher or compatibility test.
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.jars = self.root / 'jars'
        self.jars.mkdir()
        self.data = b'unit-test bytes; not a Minecraft mod'
        (self.jars / 'fixture.jar').write_bytes(self.data)
        self.lock = {'format': 1, 'minecraft': '26.2', 'fabric_loader': '0.19.5', 'release': 'test', 'mods': [{
            'file': 'fixture.jar', 'sha256': hashlib.sha256(self.data).hexdigest(),
            'redistribution': 'approved', 'privacy': 'approved',
            'permission_evidence': 'https://example.invalid/LICENSE',
            'source': 'https://example.invalid/source', 'notices': {'LICENSE': 'Unit-test notice only'}
        }]}

    def run_build(self, name='pack.zip'):
        p = self.root / 'lock.json'
        p.write_text(json.dumps(self.lock))
        return build(p, self.jars, self.root / name)

    def test_deterministic_and_no_extra_host_files(self):
        (self.jars / 'accounts.json').write_text('must not be copied')
        a = self.run_build('a.zip')
        b = self.run_build('b.zip')
        self.assertEqual(a['sha256'], b['sha256'])
        with zipfile.ZipFile(self.root / 'a.zip') as archive:
            self.assertNotIn('accounts.json', '\n'.join(archive.namelist()))
            self.assertEqual(archive.read('.minecraft/mods/fixture.jar'), self.data)
            self.assertNotIn('/home/', archive.read('instance.cfg').decode())
            self.assertIn('notices/fixture.jar/LICENSE', archive.namelist())

    def test_unreviewed_permission_refused(self):
        self.lock['mods'][0]['redistribution'] = 'UNREVIEWED'
        with self.assertRaisesRegex(ValueError, 'Unreviewed mod'):
            self.run_build()
        self.assertFalse((self.root / 'pack.zip').exists())

    def test_unreviewed_privacy_refused(self):
        self.lock['mods'][0]['privacy'] = 'UNREVIEWED'
        with self.assertRaisesRegex(ValueError, 'Unreviewed mod'):
            self.run_build()

    def test_corrupt_jar_refused(self):
        (self.jars / 'fixture.jar').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
            self.run_build()

    def test_path_traversal_refused(self):
        self.lock['mods'][0]['file'] = '../fixture.jar'
        with self.assertRaisesRegex(ValueError, 'Unsafe filename'):
            self.run_build()

    def test_duplicate_refused(self):
        self.lock['mods'].append(copy.deepcopy(self.lock['mods'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate filename'):
            self.run_build()

    def test_symlink_refused(self):
        (self.root / 'outside.jar').write_bytes(self.data)
        (self.jars / 'fixture.jar').unlink()
        (self.jars / 'fixture.jar').symlink_to(self.root / 'outside.jar')
        with self.assertRaisesRegex(ValueError, 'Unsafe source path'):
            self.run_build()

    def test_missing_notices_refused(self):
        self.lock['mods'][0]['notices'] = {}
        with self.assertRaisesRegex(ValueError, 'Missing notices'):
            self.run_build()

    def test_notice_traversal_refused(self):
        self.lock['mods'][0]['notices'] = {'../../escape': 'bad'}
        with self.assertRaisesRegex(ValueError, 'Invalid notice'):
            self.run_build()


if __name__ == '__main__':
    unittest.main()
