import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from moty_pipeline.validate_assets import validate

class AssetEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = self.root / "plan.json"
        self.asset = self.root / "shot.png"
        self.asset.write_bytes(b"fixture bytes (not actual image)")
        self.job = {"job_id": "CH01_S01_IMAGE", "kind": "image", "status": "APPROVED", "reviewer": "qa",
                    "approved_at": "2026-10-23T00:00:00Z", "output_uri": "shot.png",
                    "sha256": hashlib.sha256(self.asset.read_bytes()).hexdigest()}

    def check(self):
        self.plan.write_text(json.dumps({"jobs": [self.job]}))
        return validate(self.plan, self.root)

    def test_approved_file(self):
        self.assertEqual(self.check()["status"], "READY")

    def test_unapproved(self):
        self.job["status"] = "PENDING"
        self.assertEqual(self.check()["status"], "NOT_READY")

    def test_tampered(self):
        self.asset.write_bytes(b"changed")
        self.assertEqual(self.check()["status"], "NOT_READY")

    def test_traversal(self):
        self.job["output_uri"] = "../outside.png"
        self.assertEqual(self.check()["status"], "NOT_READY")

    def test_no_reviewer(self):
        self.job["reviewer"] = None
        self.assertEqual(self.check()["status"], "NOT_READY")

    def test_duplicate(self):
        self.plan.write_text(json.dumps({"jobs": [self.job, self.job]}))
        self.assertEqual(validate(self.plan, self.root)["status"], "NOT_READY")

    def test_empty_plan(self):
        self.plan.write_text(json.dumps({"jobs": []}))
        self.assertEqual(validate(self.plan, self.root)["status"], "NOT_READY")

if __name__ == "__main__":
    unittest.main()
