import unittest
from run_neural import hashes


class CoreManifestTests(unittest.TestCase):
    def test_manifest_fingerprints_the_actual_core_sources(self):
        keys = {key.replace('\\', '/') for key in hashes()}
        self.assertIn('../v2/src/network/scheduler.rs', keys)
        self.assertIn('../v2/Cargo.lock', keys)
