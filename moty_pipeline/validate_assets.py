"""Verify actual cinematic deliverables; queued jobs are never considered complete."""
import argparse
import hashlib
import json
from pathlib import Path

EXTENSIONS = {"image": {".png", ".jpg", ".jpeg", ".webp"}, "video": {".mp4", ".webm", ".ogv"}, "voice_pl": {".wav", ".mp3", ".ogg"}, "voice_en": {".wav", ".mp3", ".ogg"}}

def validate(plan_path, asset_root):
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    root = Path(asset_root).resolve()
    failures, verified, seen = [], [], set()
    jobs = plan.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        return {"status": "NOT_READY", "verified": 0, "total": 0, "failures": ["missing jobs"]}
    for job in jobs:
        jid, kind = job.get("job_id"), job.get("kind")
        if not jid or jid in seen:
            failures.append(f"{jid}: missing or duplicate job ID")
            continue
        seen.add(jid)
        if kind not in EXTENSIONS:
            failures.append(f"{jid}: unsupported media kind")
            continue
        if job.get("status") != "APPROVED" or not job.get("reviewer") or not job.get("approved_at"):
            failures.append(f"{jid}: missing approval evidence")
            continue
        uri = job.get("output_uri")
        if not isinstance(uri, str) or not uri or Path(uri).is_absolute():
            failures.append(f"{jid}: missing or absolute asset path")
            continue
        path = (root / uri).resolve()
        if not path.is_relative_to(root) or path.suffix.lower() not in EXTENSIONS[kind] or not path.is_file():
            failures.append(f"{jid}: invalid asset path or format")
            continue
        if not path.stat().st_size or hashlib.sha256(path.read_bytes()).hexdigest() != job.get("sha256"):
            failures.append(f"{jid}: empty file or incorrect SHA256")
            continue
        verified.append(jid)
    return {"status": "READY" if not failures and len(verified) == len(jobs) else "NOT_READY", "verified": len(verified), "total": len(jobs), "failures": failures}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plan", type=Path, default=Path(__file__).parent / "CH01_production_jobs.json")
    p.add_argument("--assets", type=Path, required=True)
    args = p.parse_args()
    result = validate(args.plan, args.assets)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if result["status"] == "READY" else 1)

if __name__ == "__main__":
    main()
