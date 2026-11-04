import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from build_manifest import check_entry, fetch


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.tmp.cleanup)
        self.cache = Path(self.tmp.name)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('fabric.mod.json', json.dumps({'id': 'fixture', 'version': '1'}))
        self.data = buffer.getvalue()
        self.entry = {'file': 'fixture.jar', 'url': 'https://cdn.modrinth.com/fixture.jar',
                      'sha256': hashlib.sha256(self.data).hexdigest(), 'sha512': hashlib.sha512(self.data).hexdigest()}

    def test_https_only(self):
        self.entry['url'] = 'http://cdn.modrinth.com/fixture.jar'
        with self.assertRaisesRegex(ValueError, 'host not allowed'):
            check_entry(self.entry)

    def test_untrusted_host(self):
        self.entry['url'] = 'https://cdn.modrinth.com.evil.invalid/fixture.jar'
        with self.assertRaisesRegex(ValueError, 'host not allowed'):
            check_entry(self.entry)

    def test_embedded_credentials(self):
        self.entry['url'] = 'https://user:password@github.com/fixture.jar'
        with self.assertRaisesRegex(ValueError, 'host not allowed'):
            check_entry(self.entry)

    def test_filename_traversal(self):
        self.entry['file'] = '../fixture.jar'
        with self.assertRaisesRegex(ValueError, 'Unsafe filename'):
            check_entry(self.entry)

    def test_hash_format(self):
        self.entry['sha256'] = 'not a hash'
        with self.assertRaisesRegex(ValueError, 'Invalid SHA'):
            check_entry(self.entry)

    def test_verified_cache_preserves_manifest(self):
        (self.cache/'fixture.jar').write_bytes(self.data)
        with patch('build_manifest.urlopen', side_effect=AssertionError('No download needed')):
            item, evidence = fetch(self.entry, self.cache)
        self.assertEqual(item['path'], 'mods/fixture.jar')
        self.assertEqual(item['hashes']['sha512'], self.entry['sha512'])
        self.assertEqual(item['fileSize'], len(self.data))
        self.assertEqual(evidence['id'], 'fixture')

    def test_corrupt_download_is_refused(self):
        (self.cache/'fixture.jar').write_bytes(b'corrupt cache')
        with patch('build_manifest.urlopen', return_value=io.BytesIO(b'corrupt response')):
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                fetch(self.entry, self.cache)
        self.assertFalse((self.cache/'fixture.part').exists())

    def test_second_hash_is_checked(self):
        (self.cache/'fixture.jar').write_bytes(self.data)
        self.entry['sha512'] = '0'*128
        with self.assertRaisesRegex(ValueError, 'SHA-512 mismatch'):
            fetch(self.entry, self.cache)


if __name__ == '__main__':
    unittest.main()
