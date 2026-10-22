"""Regression checks for evidence-first production readiness gate."""
import json
import tempfile
import unittest
from pathlib import Path

from release.e2e_gate import inspect


class E2EGateEvidenceTests(unittest.TestCase):
    def test_missing_terrain_does_not_count_as_available(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for city in ("cieszyn_rynek_osm_2026", "cesky_tesin_center_osm_2026"):
                manifest = root / "godot" / "data" / "world" / city / "manifest.json"
                manifest.parent.mkdir(parents=True, exist_ok=True)
                manifest.write_text(json.dumps({"city_id": city, "facades_historical_status": "VERIFIED"}), encoding="utf-8")
            report = inspect(root)
            self.assertFalse(report["source_data_full_city_verified"])
            self.assertFalse(report["gates"]["world_1_to_1"]["technical_evidence_present"])

    def test_gate_stays_blocked_without_independent_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            report = inspect(Path(temp))
            self.assertEqual(report["status"], "NOT_READY")
            self.assertEqual(report["blocked_gate_count"], 12)


if __name__ == "__main__":
    unittest.main()
