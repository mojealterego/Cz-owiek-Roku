# Android — architektura i warunki techniczne

**Docelowy produkt:** jakościowy, filmowy dramat 3D TPP z systemem scen i portretami postaci (PL/EN).

## Wybór silnika: decyzja robocza
Zalecany kandydat: **Unreal Engine 5**, z natywnym targetem Android, C++ w systemach stanu i dopasowanym rendererem mobilnym. Decyzja o wersji silnika i rendererze musi zostać potwierdzona *na sprzęcie docelowym*, po sprawdzeniu bieżącego wsparcia urządzeń i warunków licencji. Lumen i Nanite **nie są domyślną podstawą mobilnej wersji**; projektuj osobne lightmaps/probes, LOD/HLOD, prostsze materiały i mobilną ścieżkę cieni. Porównanie Unity/URP oraz UE5 i wyniki benchmarków mają być zapisane w ADR, a nie deklarowane na podstawie screenshotów z PC.

## Docelowy profil (założenia, nie benchmark)
- High tier Android: 30 fps stabilne w rozgrywce; 60 fps jako opcja po pomiarach.
- Skalowanie rozdzielczości, budżet termiczny, adaptacyjne cienie, texture streaming i profil urządzenia.
- Streaming rozdziałów, prefetch następnej sceny, szybkie checkpointy; brak ogromnego otwartego miasta.
- Interfejs poziomy (landscape), duże touch targets, napisy PL/EN, tryb QTE bez czasu, regulowana czułość, dostępność koloru i kontrastu.
- Offline-first; zapisy atomowe z wersjonowaniem schematu i kopią ratunkową, idempotentne zaliczanie kampanii.

## Moduły
1. `NarrativeGraph`: deterministyczne przejścia i inwariant zakończenia.
2. `ChoiceLedger`: decyzje, konsekwencje, ścieżki NG+.
3. `SceneDirector`: Sequencer, rig kamer, timed choices, przejście po konwergencji.
4. `CameraEvidence`: kadrowanie, zapis fotografii, identyfikacja dowodów przez tagi aktorów i walidację widoczności.
5. `Gallery`: fotografia istniejąca lub wykonana → odblokowanie portretu i tekstu z zatwierdzonego źródła.
6. `MediaLock`: transkrypt CH14/CH60 i media dzieci chronione przed edycją; checksums.
7. `Localization`: String Tables PL/EN, dwukierunkowa synchronizacja napisów i kwestii.
8. `Progression`: 70 rozdziałów, CH59 bezwarunkowy, DLC po pełnych przejściach.
9. `AndroidInput`: sterowanie dotykowe i gamepad, pomijanie cinematic przy powtórkach.

## Model zdarzenia
```json
{
  "event_id": "CH01-CHOICE-01",
  "chapter": 1,
  "source_status": "PROPOSED_ADAPTATION",
  "options": ["PHOTOGRAPH_AUDIENCE", "OBSERVE_AUDIENCE"],
  "convergence": "CH01-S04",
  "canonical_outcome_locked": true
}
```

## Gate odbioru
`G0` repo/dokumentacja i testy offline → `G1` kompilowalny projekt Android z otwarciem → `G2` vertical slice CH01 na urządzeniu z profilem frametime → `G3` certyfikacja modeli/assetów i mediów → `G4` produkcja 70 rozdziałów → `G5` QA/funkcjonalne DLC i tłumaczenia → `G6` signed package Android, instalacja, pomiary i akceptacja.

**Aktualny gate: G0 w toku.** Referencyjne testy w Pythonie nie dowodzą przejścia G1/G2.
