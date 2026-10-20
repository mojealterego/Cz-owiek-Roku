# Roadmap MAN OF THE YEAR — stan oparty na dowodach

| ID | Zakres | Status | Kryterium zakończenia |
| --- | --- | --- | --- |
| G0.1 | Połączenie repo GitHub i zapis na main | DONE | SHA commitu oraz odczyt GitHub |
| G0.2 | Manifest 4 aktów / 70 identyfikatorów | DONE (indeks) | 70 wpisów, bez oznaczenia jako gotowe poziomy |
| G0.3 | Referencyjny model Pauliny / CH59 / DLC | DONE (Python) | 8 testów + 16 ścieżek |
| G0.4 | Dokument reżyserii otwarcia CH01 | DRAFT | źródłowa rewizja reżyserska i akceptacja autora |
| G0.5 | Character Art Bible | DRAFT | komplet QA i zatwierdzone visual refs |
| G1 | Godot 4.5.2: projekt Android, ruch TPP, kamera, zapisy | CI VERIFIED, DEVICE UNTESTED | źródła Godot + runtime smoke + profilowanie na telefonie |
| G2 | Prolog/kurtyna/CH01 jako mobile greybox | IMPLEMENTED; APK EXPORTED | interakcje i start potwierdzić na urządzeniu; prolog audio nieobecny |
| G3 | Modele 3D, facial rig, animacje, tatuaże | NOT STARTED | zatwierdzone modele z wydajnością LOD |
| G4 | 70 pełnych grywalnych rozdziałów | NOT STARTED | scenariusze, sceny, decyzje, aktorstwo, testy |
| G5 | Galeria, 3 DLC, PL/EN, audio source-lock | NOT STARTED | pozytywne testy i zatwierdzenia mediów |
| G6 | Eksport APK, testy urządzeń, podpis produkcyjny | DEBUG APK VERIFIED; RELEASE NOT STARTED | artifact 12277449892; run 39450159089; urządzenia i release pending |

## Reguła statusów
`DONE` tylko dla faktycznie zapisanych i sprawdzonych artefaktów. `DRAFT` nie oznacza akceptacji. `NOT STARTED` nie jest równoznaczne z niemożliwością. Godot CI uruchomił scenę i wyeksportował debug APK. Nie jest to benchmark telefonu, test dotyku, ani dowód osiągnięcia jakości AAA.

## Następny etap
Priorytet: rzeczywisty test istniejącego APK na telefonie (instalacja, klatki, interfejs, zapis, zdjęcia i powrót do gry). Potem wymiana scenografii testowej na modele produkcyjne. Równolegle odseparować chronione zasoby, skorygować scenariusz na podstawie wersji książki zatwierdzonej do ekranizacji i ukończyć pipeline modeli.
