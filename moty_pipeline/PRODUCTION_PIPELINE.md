# Człowiek Roku — cinematic production pipeline

Source: author-provided 554-page ebook. Canon: 70 chapters / four acts / fixed ending.

## CH01
Eight planned shots from the December 2023 Cieszyn gala. The storyboard and the generated job queue are tracked separately. Each shot requires image, video, Polish voice and English voice deliverables.

## Production gates
1. Source extraction and adaptation review.
2. Character identity and visual reference review (reuse the book's fictional visual designs).
3. Approved PL/EN dialogue before synthetic voice generation.
4. Picsart / Firefly keyframes; Google Flow or ElevenLabs video; ElevenLabs speech.
5. Human artistic review, file SHA-256, rights and consent review.
6. Godot 4.5.2 import, Android playback, device performance and release E2E.

The planner does not call paid media APIs. No generated footage or speech is implied by queued jobs. Real likeness in 'Ten który to pisał' requires separate handling. Real-world allegations in autobiographical narration are not independently verified.

Run tests: `python -m unittest discover -s moty_pipeline -p 'test_*.py' -v`.
Run planner: `python moty_pipeline/orchestrate.py`.
