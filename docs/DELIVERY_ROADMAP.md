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
| WORLD.01 | WORLD 1:1 — specyfikacja i manifest geograficzny | SPECIFICATION WRITTEN | kontrakt, 8 rejestrów lokacji, walidacja |
| WORLD.02 | Dopasowanie scen książki do miast i lokalizacji | NOT STARTED | każda użyta lokacja ma rozdział/stronę/datę |
| WORLD.03 | Geospatial ETL EPSG PL/CZ, sektorowanie GIS | ETL IMPLEMENTED, CI VERIFIED; SOURCE DATA PENDING | testy transformacji i clippingu: run 39458562495; brak pełnych danych GIS miast |
| WORLD.04 | Miasta 1:1: Cieszyn/Český Těšín i lokacje pozostałych miast | NOT STARTED | kontrola siatki ulic, budynków, foto-match |
| WORLD.05 | Historyczne warianty i streaming sektorów Android | NOT STARTED | profil urządzenia + zatwierdzona rekonstrukcja |
| WORLD.06 | Debugowy podgląd 2 punktów w skali metrycznej na Android | BUILD VERIFIED; DEVICE UNTESTED | Godot scene run 39458975306; APK run 39458975061 |
| G3 | Modele 3D, facial rig, animacje, tatuaże | NOT STARTED | zatwierdzone modele z wydajnością LOD |
| G4 | 70 pełnych grywalnych rozdziałów | NOT STARTED | scenariusze, sceny, decyzje, aktorstwo, testy |
| G5 | Galeria, 3 DLC, PL/EN, audio source-lock | NOT STARTED | pozytywne testy i zatwierdzenia mediów |
| G6 | Eksport APK, testy urządzeń, podpis produkcyjny | DEBUG APK VERIFIED; RELEASE NOT STARTED | artifact 12281548510; run 39458975061; urządzenia i release pending |

## Reguła statusów
`DONE` tylko dla faktycznie zapisanych i sprawdzonych artefaktów. `DRAFT` nie oznacza akceptacji. `NOT STARTED` nie jest równoznaczne z niemożliwością. Godot CI uruchomił scenę i wyeksportował debug APK. Nie jest to benchmark telefonu, test dotyku, ani dowód osiągnięcia jakości AAA.

## Następny etap
Priorytet: etap WORLD.02 — mapowanie scen książki na konkretne miejsca i daty, a następnie WORLD.03 — pozyskanie rzeczywistych warstw dróg, obrysów budynków, NMT i rekonstrukcji historycznych z GUGiK/ČÚZK. Działający ETL jest przygotowany, ale zawiera obecnie wyłącznie 2 georeferencyjne punkty kontrolne. Równolegle: rzeczywisty test istniejącego APK na telefonie (instalacja, klatki, interfejs, zapis, zdjęcia i powrót do gry). Potem wymiana scenografii testowej na modele produkcyjne. Równolegle odseparować chronione zasoby, skorygować scenariusz na podstawie wersji książki zatwierdzonej do ekranizacji i ukończyć pipeline modeli.
