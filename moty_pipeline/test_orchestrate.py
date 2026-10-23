import unittest
from moty_pipeline.orchestrate import build_jobs

class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {"chapters": [{"id": f"CH{i:02d}"} for i in range(1, 71)]}
        self.shotlist = {"chapter": "CH01", "shots": [{"id": "CH01_S01", "visual_prompt_pl": "Scena", "voice_role": "narrator", "duration_s_target": 6, "camera": "closeup"}]}

    def test_four_jobs(self):
        jobs = build_jobs(self.manifest, self.shotlist)
        self.assertEqual(len(jobs), 4)
        self.assertEqual(len({j["input_hash"] for j in jobs}), 4)
        self.assertTrue(all(j["output_uri"] is None for j in jobs))

    def test_duplicate_rejected(self):
        self.shotlist["shots"].append(self.shotlist["shots"][0])
        with self.assertRaises(ValueError):
            build_jobs(self.manifest, self.shotlist)

    def test_incomplete_manifest_rejected(self):
        self.manifest["chapters"].pop()
        with self.assertRaises(ValueError):
            build_jobs(self.manifest, self.shotlist)

    def test_voice_blocked(self):
        jobs = build_jobs(self.manifest, self.shotlist)
        self.assertEqual(sum(j["status"] == "BLOCKED_SCRIPT_APPROVAL" for j in jobs), 2)

if __name__ == "__main__":
    unittest.main()
