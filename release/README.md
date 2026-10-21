# Release E2E — evidence-based acceptance

**No release is authorized by a green CI check alone.** Green CI means only that the gate assessment tool and present stage tests passed.

Run `python -m release.e2e_gate --repo-root . --out /tmp/moty_e2e_status.json`.
Unit tests: `python -m unittest release.test_e2e_gate -v`.

## Acceptance controls
The report separates **CH01 technical greybox** from chapter-by-chapter **approved production**. It requires real chapter scenes `godot/scenes/chapters/ch_NN.tscn` and individually reviewed evidence records `release/evidence/chapters/CHNN.json` for all 70. An index of 70 placeholders does not pass. Other gates include world geometry and historical validation, approved book excerpts, children's recordings/permissions, finished art, full bilingual content, 3 DLC, Android device QA and FPS/RAM, signed release APK and privacy/licensing review.

Evidence file format (not provided with approved values):
```json
{
  "gate": "world_1_to_1",
  "status": "APPROVED",
  "reviewer": "Full identity of human reviewer",
  "evidence_url": "https://trusted-system.example.org/review/123",
  "verified_utc": "2026-10-21T10:00:00Z"
}
```

Reviewers must independently verify claims, signed artifacts, provenance, dates and performance. The gate only performs a schema/file check; it does not cryptographically authenticate remote evidence URLs. Never invent `APPROVED` records or publish private material. A fully green report still requires a final independent human release review.

## Current state
CH01 is a mobile-compatible greybox and has CI E2E checks for PL/EN choice/save/continue. The Android artifact is a **debug** build. There are no accepted 70 production chapters or verified historical full 1:1 cities. No physical Android benchmark or release-signed APK is present. Therefore production readiness is **NOT_READY**, regardless of debug APK success.
