"""Evidence-first E2E acceptance gate for MAN OF THE YEAR, not a sales checklist.

Run: python -m release.e2e_gate --repo-root . --out /tmp/moty-e2e.json
Uses ONLY existing repo files and checked evidence, never fake placeholders.
CI success means "assessment script ran", NOT "full 70-chapter game is done".
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

TOTAL_CHAPTERS = 70
ACTS = {"I": (1, 14), "II": (15, 41), "III": (42, 62), "IV": (63, 70)}
MANDATORY = (
    "chapters", "world_1_to_1", "historical_locations",
    "approved_book_assets", "child_recordings_and_consent",
    "art_animation", "bilingual_content", "three_dlc",
    "physical_android_qa", "mobile_performance",
    "release_signed_apk", "privacy_legal_review",
)
EVIDENCE = "release/evidence"
ACCEPTED_FILENAME = re.compile(r"^CH(0[1-9]|[1-6][0-9]|70)\\.json$")


def _load(path: Path) -> dict[str, Any] | None:
    if not path.is_file() or path.stat().st_size > 64 * 1024:
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _manually_accepted(document: Any, key: str) -> bool:
    if not isinstance(document, dict):
        return False
    # No accepting a boolean alone: reviewer and traceable evidence required.
    return (
        document.get("gate") == key
        and document.get("status") == "APPROVED"
        and isinstance(document.get("reviewer"), str)
        and len(document["reviewer"].strip()) >= 4
        and isinstance(document.get("evidence_url"), str)
        and document["evidence_url"].startswith("https://")
        and len(document["evidence_url"]) > 18
        and isinstance(document.get("verified_utc"), str)
        and bool(re.fullmatch(r"20[0-9]{2}-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z", document["verified_utc"]))
    )


def inspect(root: Path) -> dict[str, Any]:
    root = root.resolve()
    godot = root / "godot"
    fixture = godot / "scenes" / "main.tscn"
    main = godot / "scripts" / "main.gd"
    state = godot / "scripts" / "narrative_state.gd"
    base_demo = (
        fixture.is_file() and main.is_file() and state.is_file()
        and 'func _enter_world()' in main.read_text(encoding="utf-8")
        and 'func _commit_choice(' in main.read_text(encoding="utf-8")
    )
    historical = root / "docs" / "WORLD_1_TO_1_SPECIFICATION.md"
    map_sources = [
        godot / "data" / "world" / "cieszyn_rynek_osm_2026" / "manifest.json",
        godot / "data" / "world" / "cesky_tesin_center_osm_2026" / "manifest.json",
    ]
    manifest_status: list[dict[str, Any]] = []
    for path in map_sources:
        entry = _load(path)
        if entry is None:
            continue
        manifest_status.append({
            "city_id": entry.get("city_id"),
            "source_features": entry.get("source_features"),
            "tile_count": entry.get("tile_count"),
            "source_year": entry.get("historical_year"),
            "history_verified": entry.get("facades_historical_status") == "VERIFIED",
            "terrain_available": entry.get("terrain_status") != "MISSING",
        })
    approved_chapters: list[int] = []
    for chapter in range(1, TOTAL_CHAPTERS + 1):
        source = _load(root / EVIDENCE / "chapters" / f"CH{chapter:02d}.json")
        scene = godot / "scenes" / "chapters" / f"ch_{chapter:02d}.tscn"
        if scene.is_file() and _manually_accepted(source, f"chapter_{chapter:02d}"):
            approved_chapters.append(chapter)
    gates: dict[str, dict[str, Any]] = {}
    for gate in MANDATORY:
        document = _load(root / EVIDENCE / f"{gate}.json")
        manually = _manually_accepted(document, gate)
        # Some gates additionally demand actual source artifacts.
        technical = True
        if gate == "chapters":
            technical = len(approved_chapters) == TOTAL_CHAPTERS
        elif gate == "world_1_to_1":
            technical = bool(historical.is_file() and len(manifest_status) >= 2
                and all(v["history_verified"] and v["terrain_available"] for v in manifest_status))
        elif gate == "release_signed_apk":
            technical = (root / "release" / "verified_release_sha256.txt").is_file()
        elif gate == "mobile_performance":
            technical = (root / EVIDENCE / "physical_android_qa.json").is_file()
        elif gate == "physical_android_qa":
            technical = (root / EVIDENCE / "physical_android_qa.json").is_file()
        gates[gate] = {
            "status": "PASS" if (manually and technical) else "BLOCKED",
            "human_review_present": manually, "technical_evidence_present": technical,
        }
    blocked = [key for key, value in gates.items() if value["status"] == "BLOCKED"]
    report = {
        "schema_version": 1,
        "project": "CZLOWIEK_ROKU_MAN_OF_THE_YEAR",
        "assessment_kind": "EVIDENCE_BASED_RELEASE_GATE",
        "ready_for_production": not blocked,
        "status": "READY_FOR_HUMAN_RELEASE_REVIEW" if not blocked else "NOT_READY",
        "chapter_count_required": TOTAL_CHAPTERS,
        "chapter_3d_greybox_count": 1 if base_demo else 0,
        "chapter_production_approved_count": len(approved_chapters),
        "chapter_production_approved": approved_chapters,
        "source_basemap_fragments": manifest_status,
        "source_data_full_city_verified": bool(manifest_status and all(
            v["history_verified"] and v["terrain_available"] for v in manifest_status)),
        "gates": gates,
        "blocked_gate_count": len(blocked),
        "blocked_gates": blocked,
        "note": (
            "This report is not a physical device benchmark or proof that 70 chapters "
            "are implemented. APPROVED files require independent review of their URLs; "
            "this checker only validates format and repository evidence."
        ),
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = inspect(args.repo_root)
    encoded = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    print(encoded)
    # No nonzero exit for known missing chapters/assets. That is the expected
    # honest project state, not a broken CI tool.


if __name__ == "__main__":
    main()
