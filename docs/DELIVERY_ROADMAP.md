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
| WORLD.03 | Geospatial ETL EPSG PL/CZ + import bieżących danych OSM | PARTIAL REAL SOURCE IMPORT, CI VERIFIED | OSM: 397 budynków, 145 dróg, 13 sektorów; run 39466656392 i 39467589299 |
| WORLD.03b | Walidowany runtime płaskich obrysów Godot | DONE FOR CURRENT 2D SUBSETS | 2 osobne warstwy, 13 sektorów, test ID; Godot run 39525476547 |
| WORLD.03c | Kontrola OSM height i building:levels PL/CZ | CI VERIFIED, NO MEASURED HEIGHT VALUES | 397 budynków; 0 jawnych height, 225 levels; run 39524348026 |
| WORLD.03d | Importer prawdziwej geometrii GUGiK CityGML LoD1 2024 | SOURCE IMPORTER VERIFIED, REAL ARCHIVE PENDING | walidacja 3D posList, CRS, measuredHeight; run 39524991042 |
| WORLD.04 | Pełne historyczne miasta 1:1: Cieszyn/Český Těšín i pozostałe | NOT STARTED (ONLY 2D PARTIAL BASEMAP) | komplet miasta, źródłowe wysokości, teren, fotogrametria i foto-match |
| WORLD.05 | Historyczne warianty i streaming sektorów Android | NOT STARTED | profil urządzenia + zatwierdzona rekonstrukcja |
| WORLD.06 | Debugowy podgląd metrycznych 2 ratuszy i 13 kafli OSM PL/CZ na Android | BUILD VERIFIED; DEVICE UNTESTED | strict Godot runtime run 39525476547; APK run 39525476347 |
| G3 | Modele 3D, facial rig, animacje, tatuaże | NOT STARTED | zatwierdzone modele z wydajnością LOD |
| G4 | 70 pełnych grywalnych rozdziałów | NOT STARTED | scenariusze, sceny, decyzje, aktorstwo, testy |
| G5 | Galeria, 3 DLC, PL/EN, audio source-lock | NOT STARTED | pozytywne testy i zatwierdzenia mediów |
| G6 | Eksport APK, testy urządzeń, podpis produkcyjny | DEBUG APK VERIFIED; RELEASE NOT STARTED | artifact 12313131063; run 39525476347; urządzenia i release pending |

## Reguła statusów
`DONE` tylko dla faktycznie zapisanych i sprawdzonych artefaktów. `DRAFT` nie oznacza akceptacji. `NOT STARTED` nie jest równoznaczne z niemożliwością. Godot CI uruchomił scenę i wyeksportował debug APK. Nie jest to benchmark telefonu, test dotyku, ani dowód osiągnięcia jakości AAA.

## Następny etap
Priorytet: etap WORLD.02 — mapowanie scen książki na konkretne miejsca i daty, a następnie WORLD.03 — pozyskanie rzeczywistych warstw dróg, obrysów budynków, NMT i rekonstrukcji historycznych z GUGiK/ČÚZK. Działający ETL pozyskał dwa bieżące wycinki OSM (397 obrysów budynków, 145 dróg) i sprawdził znaczniki wysokości: 0 height w metrach, 225 budynków z liczbą kondygnacji. Powstał testowany importer oficjalnego CityGML LoD1 2024; rzeczywista paczka powiatowa GUGiK, LiDAR, NMT i historyczne warianty nadal nie zostały zaimportowane. Demo Godot renderuje obrysy bez zmyślonych kondygnacji. Równolegle: rzeczywisty test istniejącego APK na telefonie (instalacja, klatki, interfejs, zapis, zdjęcia i powrót do gry). Potem wymiana scenografii testowej na modele produkcyjne. Równolegle odseparować chronione zasoby, skorygować scenariusz na podstawie wersji książki zatwierdzonej do ekranizacji i ukończyć pipeline modeli.
