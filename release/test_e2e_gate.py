"""Prevent declaring unfinished game to be complete by existence of an APK."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from release.e2e_gate import ACTS, MANDATORY, TOTAL_CHAPTERS, _manually_accepted, inspect

ROOT = Path(__file__).resolve().parents[1]

class E2EAcceptanceTests(unittest.TestCase):
    def test_four_acts_have_exact_70_canonical_slots(self):
        self.assertEqual(TOTAL_CHAPTERS, 70)
        self.assertEqual(ACTS, {"I": (1, 14), "II": (15, 41),
                                "III": (42, 62), "IV": (63, 70)})
        self.assertEqual(sum(b - a + 1 for a, b in ACTS.values()), TOTAL_CHAPTERS)

    def test_live_repository_does_not_claim_70_completed_chapters(self):
        report = inspect(ROOT)
        self.assertEqual(report["chapter_count_required"], 70)
        self.assertGreaterEqual(report["chapter_3d_greybox_count"], 1)
        self.assertLessEqual(report["chapter_production_approved_count"], 70)
        self.assertEqual(report["ready_for_production"], report["blocked_gate_count"] == 0)
        self.assertEqual(report["blocked_gate_count"], len(report["blocked_gates"]))
        if report["chapter_production_approved_count"] < 70:
            self.assertIn("chapters", report["blocked_gates"])
        self.assertGreaterEqual(len(report["source_basemap_fragments"]), 2)

    def test_unsigned_unreviewed_empty_repo_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = inspect(Path(tmp))
            self.assertEqual(report["chapter_3d_greybox_count"], 0)
            self.assertEqual(report["chapter_production_approved_count"], 0)
            self.assertEqual(set(report["blocked_gates"]), set(MANDATORY))
            self.assertFalse(report["ready_for_production"])

    def test_unsubstantiated_boolean_is_not_an_approval(self):
        self.assertFalse(_manually_accepted({"gate": "chapters", "status": "APPROVED"}, "chapters"))
        self.assertFalse(_manually_accepted({"gate": "chapters", "approved": True}, "chapters"))
        self.assertFalse(_manually_accepted(None, "chapters"))
        self.assertFalse(_manually_accepted({
            "gate": "chapters", "status": "APPROVED", "reviewer": "test",
            "evidence_url": "https://example.org/evidence",
            "verified_utc": "BAD"
        }, "chapters"))

if __name__ == "__main__":
    unittest.main()
