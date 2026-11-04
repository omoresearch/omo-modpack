import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_compatibility as compat


class CompatibilityGuards(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.base=self.root/'base.mrpack'
        self.proposal=self.root/'scope.json'
        self.jar=self.root/'mod.jar'
        self.base.write_bytes(b'not the approved base')
        self.proposal.write_bytes(b'not the approved scope')
        self.jar.write_bytes(b'not the approved jar')

    def build(self):
        return compat.build(self.base,self.proposal,self.jar,self.root,self.root/'out')

    def test_changed_base_refused(self):
        with self.assertRaisesRegex(ValueError,'Base candidate changed'):
            self.build()
        self.assertFalse((self.root/'out').exists())

    def test_changed_scope_refused(self):
        # Isolate this guard from the preceding base guard.
        with patch.object(compat,'BASE_SHA256',hashlib.sha256(self.base.read_bytes()).hexdigest()):
            with self.assertRaisesRegex(ValueError,'Compatibility scope changed'):
                self.build()

    def test_changed_jar_refused(self):
        self.proposal.write_text(json.dumps({'addition':{'file':'fixture.jar','sha256':'0'*64}}))
        with patch.object(compat,'BASE_SHA256',hashlib.sha256(self.base.read_bytes()).hexdigest()), patch.object(compat,'PROPOSAL_SHA256',hashlib.sha256(self.proposal.read_bytes()).hexdigest()):
            with self.assertRaisesRegex(ValueError,'Compatibility JAR hash mismatch'):
                self.build()


if __name__=='__main__':
    unittest.main()
