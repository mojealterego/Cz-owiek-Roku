# WORLD 1:1 — Specyfikacja produkcyjna geograficznego odwzorowania miast

**Status: wymaganie wiążące; implementacja map 3D NIE ROZPOCZĘTA.**  
**Priorytet: P0 / blokuje akceptację docelowej gry.**  
**Powiązanie:** `data/world/city_reconstruction_manifest.json`, `reference/world_grid.py`, `reference/test_world_grid.py`.

## 1. Jednoznaczne znaczenie 1:1
Gra **nie może** zawierać swobodnie wymyślonego, skompresowanego lub procedurą wygenerowanego „Cieszyna podobnego do Cieszyna”. Obowiązują dwa niezależne kryteria:
1. **Skala metryczna i układ przestrzenny**: jedna jednostka świata gry = jeden metr, odległości, położenie budynków, ulice, place, mosty, rzeźba terenu i charakterystyczne osie widokowe są zakotwiczone w rzeczywistych geodanych i nie są „skracane dla wygody gracza”.
2. **Wierność wizualna / historyczna**: materiały, elewacje, dachy, witryny, oznakowanie, wyposażenie miejsc użytych w scenach i oświetlenie odpowiadają **datom konkretnych zdarzeń z książki**, a nie domyślnie aktualnemu obrazowi w 2026 roku.

**Ważne rozróżnienie:** geometria LoD1/LoD2 BDOT10k nie dowodzi wierności elewacji, wyposażenia wnętrz i stanu historycznego. Uczciwa etykieta `CITY_1_TO_1_ACCEPTED` wymaga osobnego protokołu terenowego, foto-referencyjnego i QA. Również brak ulicy w grze nie może skracać drogi między dwiema istniejącymi ulicami: odległość geograficzna nadal obowiązuje.

## 2. Miasta i zakres
Punkt startowy:
- **Cieszyn + Český Těšín**: jeden logiczny, transgraniczny obszar gry z zachowaniem granicy państwowej, Olzy i poprawnej geometrii mostów.
- **Bielsko-Biała, Żory, Warszawa, Lublin, Łęczna**: odrębne georeferencjonowane światy ze scenami odtwarzanymi zgodnie z chronologią książki.
- **Stonava / rejon ČSM**: początkowo oddzielna lokacja typu `site`, **nie automatycznie pełne miasto**. Teren górniczy weryfikować na podstawie scen książki, nie przenosić fikcyjnego TimeRift i dorosłej Zuzi z błędnych treatmentów.

Lista to **rejestr kandydatów na podstawie dotychczasowej dokumentacji**, a nie ukończony indeks wszystkich 409 stron. Zanim rozpocznie się modelowanie konkretnej lokacji, każda scena otrzyma przypisanie `CHxx → strony źródła → miejsce → data i pora dnia → wymagany obszar rozgrywki`. Nowe miejscowości dodaje się po tej weryfikacji, bez ich zgadywania.

## 3. Dane źródłowe i pochodzenie
| Teren | Wstępne źródło geometrii | Dodatkowa walidacja |
|---|---|---|
| Polska: ulice, obiekty i topografia | GUGiK BDOT10k / państwowy zasób geodezyjny | pomiary lokalne, historyczny przebieg, uzupełniające GIS |
| Polska: bryły budynków | GUGiK CityGML LoD1, miejscami LoD2, ALS/LiDAR, NMT | elewacje i dachy ręcznie/ fotogrametrycznie zgodnie z okresem |
| Czechy: rzeźba terenu | ČÚZK DMR 5G; rejestry topograficzne ČÚZK | budynki i elewacje z dopuszczonych danych, referencji i pomiarów |
| Dodatkowe drogi/POI | OpenStreetMap **dopiero po sprawdzeniu ODbL** | oznaczenie autorstwa, wymagania bazy pochodnej, konfliktów licencyjnych |

Oficjalne źródła:  
- GUGiK: https://www.geoportal.gov.pl/pl/dane/inne-dane/modele-3d-budynkow/  
- GUGiK: https://www.geoportal.gov.pl/pl/dane/baza-danych-obiektow-topograficznych-bdot10k/  
- ČÚZK: https://geoportal.cuzk.cz/  
- OSM: https://www.openstreetmap.org/copyright

**Nie pobieraj / nie publikuj masowo tekstur ze Street View albo portali komercyjnych bez praw do wykorzystania.** Zbiór danych wysokościowych i publiczna usługa podglądu nie stanowią automatycznie licencji na wszystkie elementy świata gry.

## 4. Układy współrzędnych (bez fałszywej lokalizacji)
- Kanoniczna identyfikacja globalna: WGS84 EPSG:4326; źródła PL w EPSG:2180, CZ w EPSG:5514; przy mieszaniu wysokości uzgodnić i udokumentować transformację datumu pionowego.
- ETL w osobnym procesie: GDAL/PROJ/PDAL/QGIS → zweryfikowana transformacja → miejska kotwica geodezyjna → metryczny lokalny układ East/Up/North. Dla każdej transformacji zachowaj wersję i parametry PROJ.
- W Godot mesh musi zachować `1 unit = 1 m`; nie zakładaj, że geodezyjne stopnie można użyć bezpośrednio jako współrzędne świata.
- Każdy obszar to siatka sektorów `256 m × 256 m`, identyfikowana bezstratnie również dla ujemnych współrzędnych. Granice sektorów i mosty mają mieć zgodne punkty styku.
- Dla dużych odległości stosuj rebase/origin shifting w runtime, bez utraty dokładności ruchu i kamer. **Globalny świat ma precyzyjny identyfikator geografii; lokalna scena pracuje w metrach.**

## 5. Architektura Android: 1:1 ≠ cały obszar w RAM
Streaming jest wyłącznie optymalizacją pamięci i renderingu, **nie zwężaniem skali**:
- Globalna geometria miasta: trwała baza sektorów z georeferencją, osobnymi poziomami szczegółowości.
- `TileStreamManager`: async loading/unloading, ring prefetch, budżet RAM i pamięci tekstur.
- `SceneLocationResolver`: mapowanie `chapter/scene_id → city_id → tile_id → temporal_snapshot`.
- `HistoricVariantSystem`: zmiany elewacji, wystaw, reklam, ruchu i stanu obiektów odpowiednio do daty sceny, z dowodem źródłowym.
- `LandmarkLOD`: rzeczywista skala dla wszystkich poziomów; tylko geometria materiałów i liczba trójkątów maleją z odległością.
- `MobileQualityController`: 30 fps docelowo na zatwierdzonej klasie urządzeń, dynamic resolution, LOD/HLOD, culling, kompresja tekstur, testy termiczne. **Brak jeszcze pomiarów**.

**Uwaga:** docelowa liczba sektorów ani budżet GPU/RAM nie mogą być wiarygodnie zadeklarowane, dopóki nie są znane rozmiary map i urządzenia testowe. Nie wolno założyć fotorealistycznego całego miasta przy stałym 60 fps bez benchmarków.

## 6. Etapy budowy miasta
1. `SOURCE_MAPPING` — mapowanie wszystkich rozdziałów i scen na zweryfikowane lokalizacje, bez fikcyjnych adresów.
2. `LICENCE_AND_PROVENANCE` — rejestr licencji, źródłowe daty, prawa do zdjęć i rekonstrukcji przestrzeni prywatnych.
3. `GEOSPATIAL_ETL` — import obrysów, terenu, sieci drogowej; transformacja do wspólnego metrycznego układu gry.
4. `TERRAIN_ROADS_STRUCTURES` — odtworzenie rzeczywistej siatki ulic, zabudowy i mostów w skali.
5. `LANDMARK_SCANS` — niezależna kontrola skali i orientacji najważniejszych lokacji; foto-match, LiDAR i ręczna korekta.
6. `2023_2025_VARIANTS` — wierność okresowi wydarzeń, nie tylko aktualności map.
7. `PERFORMANCE_STREAMING` — osobne pakiety sektorów; testy FPS i RAM na urządzeniu.
8. `ACCEPTANCE` — raport porównania geo/zdjęcia/kadr z niezależnym przeglądem i ścieżkami odtwarzania.

## 7. Jakość i kryteria akceptacji
**Proponowane progi geometryczne — wymagają zatwierdzenia i kalibracji do dokładności poszczególnych źródeł**, nie są wynikami pomiarów:
- krytyczny punkt sceny / wejście do obiektu: błąd poziomy nie większy niż 0,5 m;
- oś ulicy: nie większy niż 1,5 m, poza historycznie uzasadnionymi odstępstwami;
- obrys budynku: do 1 m tam, gdzie źródła mają taką dokładność; inaczej udokumentować faktyczną dokładność;
- teren niezwiązany z bezpośrednimi ujęciami: błąd wysokości nie większy niż 1 m, po wyrównaniu datum;
- wszystkie lokacje krytyczne: manualny foto-match odtwarzanego kadru i wizualna akceptacja autora.

**Bezwzględny warunek:** stan `ACCEPTED` nie może zostać przydzielony bez zweryfikowanych współrzędnych, listy danych źródłowych, pomiarów błędu, zatwierdzenia historycznego i raportu licencyjnego. Potwierdzenie uruchomienia Godot lub debug APK tego nie zastępuje.

## 8. Prywatność i bezpieczeństwo
Domy osób prywatnych, wnętrza mieszkalne i zdarzenia dotyczące dzieci wymagają osobnej analizy danych osobowych i praw do wizerunku/prywatności. Ulice i budynki publiczne mogą być odwzorowane geograficznie, a **wnętrza prywatne rekonstrukcją scenograficzną** na podstawie zatwierdzonych materiałów, bez publikowania rzeczywistych prywatnych planów pomieszczeń. Zakaz publikowania surowych materiałów wrażliwych w otwartym repo.

## 9. Co istnieje na dziś
Obecny `godot/scripts/main.gd` generuje fikcyjne prostopadłościany sali i backstage. **To techniczna makieta, nie Cieszyn 1:1**. Nie zastępuj go losowo generowanym miastem i nie ogłaszaj ukończenia world-building bez danych terenowych.
