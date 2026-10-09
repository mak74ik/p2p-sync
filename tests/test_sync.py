import os
import shutil
import tempfile
import unittest
from p2p_sync.crypto import SyncCrypto
from p2p_sync.manifest import SyncManifest, get_file_hash

class TestP2PSync(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.crypto_key = SyncCrypto.generate_new_key()
        self.crypto = SyncCrypto(self.crypto_key)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_crypto_roundtrip(self):
        msg = b"Confidential P2P data block payload."
        encrypted = self.crypto.encrypt(msg)
        self.assertNotEqual(msg, encrypted)
        decrypted = self.crypto.decrypt(encrypted)
        self.assertEqual(msg, decrypted)

    def test_manifest_scanning_and_diff(self):
        file1 = os.path.join(self.temp_dir, "test1.txt")
        with open(file1, "w", encoding="utf-8") as f:
            f.write("Hello P2P World")

        manifest_mgr = SyncManifest(self.temp_dir)
        m = manifest_mgr.scan()

        self.assertIn("test1.txt", m)
        self.assertEqual(m["test1.txt"]["size"], 15)
        self.assertTrue(len(m["test1.txt"]["hash"]) == 64)

        # Test diff calculation
        remote_m = {
            "test1.txt": m["test1.txt"],
            "remote_only.txt": {"hash": "abc", "size": 10, "mtime": 100}
        }
        to_pull, to_push = SyncManifest.diff(m, remote_m)
        self.assertEqual(to_pull, ["remote_only.txt"])
        self.assertEqual(to_push, [])

if __name__ == "__main__":
    unittest.main()
