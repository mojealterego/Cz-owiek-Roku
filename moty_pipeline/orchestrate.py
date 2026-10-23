"""Deterministic cinematic production job planner; does not render media."""
import hashlib
import json
from pathlib import Path

PROVIDERS = {"image": "picsart", "video": "google_flow_or_elevenlabs", "voice_pl": "elevenlabs", "voice_en": "elevenlabs"}

def build_jobs(manifest, shotlist):
    chapters = manifest["chapters"]
    if [c["id"] for c in chapters] != [f"CH{i:02d}" for i in range(1, 71)]:
        raise ValueError("Expected exactly 70 ordered chapters")
    chapter = shotlist["chapter"]
    if chapter not in {c["id"] for c in chapters}:
        raise ValueError("Unknown chapter")
    jobs, seen = [], set()
    for shot in shotlist["shots"]:
        sid = shot["id"]
        if sid in seen or not sid.startswith(chapter + "_S"):
            raise ValueError("Duplicate or invalid shot")
        seen.add(sid)
        for kind, provider in PROVIDERS.items():
            payload = {"chapter_id": chapter, "shot_id": sid, "kind": kind, "provider": provider,
                       "prompt": shot["visual_prompt_pl"] if kind in ("image", "video") else None,
                       "voice_role": shot["voice_role"] if kind.startswith("voice_") else None,
                       "locale": kind[-2:] if kind.startswith("voice_") else None,
                       "target_seconds": shot["duration_s_target"], "camera": shot["camera"]}
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            jobs.append({**payload, "job_id": sid + "_" + kind.upper(), "input_hash": digest,
                         "status": "BLOCKED_SCRIPT_APPROVAL" if kind.startswith("voice_") else "READY_FOR_REFERENCE_REVIEW",
                         "output_uri": None, "rights_status": "AUTHOR_SOURCE; ASSET_REVIEW_PENDING",
                         "reviewer": None, "retry_count": 0, "error": None})
    return jobs

def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "chapters_manifest.json").read_text(encoding="utf-8"))
    shotlist = json.loads((root / "CH01_shotlist.json").read_text(encoding="utf-8"))
    jobs = build_jobs(manifest, shotlist)
    (root / "CH01_production_jobs.json").write_text(json.dumps({"schema": 1, "project": "CZLOWIEK_ROKU", "jobs": jobs}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Planned {len(jobs)} jobs; no media generated")

if __name__ == "__main__":
    main()
