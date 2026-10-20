# ADR-0001: Godot 4.5.2 for Android proof-of-concept

**Date:** 2026-10-20. **Status:** Accepted for *vertical slice only*, conditional for final production.

## Context
The source repository contained documents and a Python state model but no executable Android engine project. Goal: deliver a real 3D, Android-targeted input/choice/photo prototype with reliable headless CI rather than perpetuating documentation.

## Decision
Use Godot 4.5.2 GDScript and Compatibility (OpenGL ES 3) renderer for the first native Android prototype. Keep cinematic logic source-driven and standalone state model. Adopt a modular replacement path if Unreal Engine 5 or another technology benchmarks better for final character/render quality.

## Non-goals and evidence
No claim of visual parity with Heavy Rain or Detroit: Become Human. Geometry in this iteration is procedural blocking (no character scans, no motion capture). No original protected voiceover or child audio is bundled. No 70 3D levels are present.

## Why this engine now
- Open source, native Android export path, scene editor and scripting runnable in CI.
- Compatibility renderer covers older devices; modern mobile path may be evaluated after device testing.
- Project can be opened directly in the official Android Godot editor or a desktop editor.
- Unit/smoke tests can run headless without graphics acceleration.

## Trade-offs
- Less mature photo-real facial pipeline than UE5; final production engine remains subject to benchmark and art-direction decision.
- Before releasing a debug Android package, supply a verified `export_presets.cfg`, matching Android templates and SDK credentials in CI; **source import success is not APK export success**.
- Game currently implements CH01 only as a playable 3D greybox. `SŁOWO OD CZŁOWIEKA ROKU` is a blocked protected reading and requires separately approved audio.

## References
- https://godotengine.org/download/archive/4.5.2-stable/
- https://docs.godotengine.org/en/4.5/tutorials/rendering/renderers.html
- https://docs.godotengine.org/en/4.5/tutorials/export/exporting_for_android.html
- https://github.com/chickensoft-games/setup-godot
