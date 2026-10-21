# CZŁOWIEK ROKU / MAN OF THE YEAR

**Android-first cinematic interactive drama · PL/EN · 4 akty · 70 rozdziałów**

Repozytorium produkcyjne adaptacji książki Andrzeja Mikulskiego. Przewidywany styl: interaktywny dramat TPP, decyzje i konsekwencje, fotografia jako mechanika śledcza, filmowe sceny oraz niezmienny kanoniczny finał. Inspiracje jakościowe: *Heavy Rain* i *Detroit: Become Human*. Bez kopiowania cudzego kodu, scen lub assetów.

> **STATUS: GRYWALNY GREYBOX CH01 / ANDROID DEBUG BUILD.** Projekt Godot 4.5.2 uruchamia się w headless CI, a pakiet APK ARM64 powstał i został zweryfikowany jako poprawne archiwum. **Nie przeprowadzono testu na fizycznym Androidzie.** Nie istnieją jeszcze fotorealistyczne modele, animacje aktorskie ani pozostałe 69 rozdziałów w postaci gry.

## Bezwzględny wymóg: WORLD 1:1

Miasta i miejsca fabuły muszą być **geograficznie odwzorowane w rzeczywistej skali metrycznej 1:1**, z zgodnością architektury oraz dat 2023–2025. Obecna scena gali to **techniczna makieta**, nie rekonstrukcja żadnego miasta. **[Specyfikacja WORLD 1:1](docs/WORLD_1_TO_1_SPECIFICATION.md)**, [manifest lokalizacji](data/world/city_reconstruction_manifest.json) i [testy przestrzenne](reference/test_world_grid.py) definiują obowiązkowy etap produkcji i bramkę odbioru. Bez rzeczywistych danych przestrzennych, pozwoleń, foto-referencji i testów nie wolno oznaczyć świata jako ukończonego.

### Rzeczywiste obrysy Polski i Czech — import 2026

| Obszar bieżącej mapy OSM | Budynki (obrysy 2D) | Drogi (ways) | Kafle 256 m |
|---|---:|---:|---:|
| Cieszyn, fragment centrum/Rynku | 117 | 66 | 4 |
| Český Těšín, fragment centrum | 280 | 79 | 9 |
| **Razem** | **397** | **145** | **13** |

Pliki źródłowe: [Cieszyn 2026](geodata/snapshots/cieszyn_rynek_osm_2026.geojson) i [Český Těšín 2026](geodata/snapshots/cesky_tesin_center_osm_2026.geojson). Obie próbki to **rzeczywiste, niekompletne dane współczesne © OpenStreetMap contributors na licencji ODbL 1.0**, z tym samym punktem geograficznym i skalą 1 m = 1 jednostka Godot. [Godot map preview](godot/scenes/world_preview.tscn) wyświetla **płaskie obrysy**, nie sfabrykowane budynki 3D.

Testy kodu i geometrii: [Godot CI, bez SCRIPT ERROR](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39525476547). [Android ARM64 debug APK](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39525476347). **Fizyczny Android nie został jeszcze przetestowany**. W publicznym APK nadal brak modeli terenu i zweryfikowanych wysokości budynków w tych dwóch wycinkach i elewacji, LiDAR i weryfikacji wyglądu historycznego 2023–2025.

### Wysokości budynków i dane CityGML — najnowsza iteracja

W dwóch pobranych wycinkach OSM sprawdzono 397 budynków. **Żaden nie posiada znacznika `height=*` z wysokością w metrach**; 225 budynków ma jedynie `building:levels` (36 PL + 189 CZ). Parser [OSM](geodata/osm_extract.py) i [metryczny ETL](geodata/geoetl.py) zachowują rozdzielenie tych informacji. [Godot](godot/scripts/osm_preview_layer.gd) tworzy drucianą bryłę o podanej wysokości **wyłącznie** dla budynków z jawnym źródłowym `height=*`; nie wyznacza wysokości z liczby kondygnacji. [Raport CI](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39524348026).

Dla polskich budynków przygotowano [importer oficjalnych modeli CityGML LoD1 2024](geodata/citygml_lod1.py) i [procedurę pozyskania](docs/WORLD_CITYGML_LOD1_GUGIK_2024.md). Parser obsługuje trójwymiarowe współrzędne powierzchni, `measuredHeight`, CRS i jawny wybór osi; [testy kontraktowe](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39524991042) przeszły. **Oryginalna paczka modeli GUGiK dla powiatu cieszyńskiego nie jest jeszcze pobrana, a testy parsera wykorzystują wyłącznie oznaczoną jako syntetyczną geometrię.** Dopóki nie ma danych LiDAR/NMT i historycznych referencji, żadna bryła nie jest odbierana jako finalny cyfrowy bliźniak.

### Weryfikacja 3D rzeczywistego terenu ČÚZK w Godot

- Oficjalny czeski DMR5G (wysokości Bpv, poziomo EPSG:5514) został pobrany i przekonwertowany na 4 sektory metryczne: 324 próbki i 512 trójkątów.
- Zintegrowany [renderer źródłowego terenu QA](godot/scripts/terrain_qa_layer.gd) poprawnie zbudował siatkę o wysokościach **266,220–273,622 m** w Godot 4.5.2.
- [Test kompletnej ścieżki ČÚZK → GeoTIFF → sektory → mesh Godot](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39574730353): **SUCCESS; 0 błędów**.
- Materiały źródłowe pozostają **wyłącznie na tymczasowym runnerze CI**, bez publikacji rastra lub pochodnej geometrii: weryfikacja praw i pionowe uzgodnienie PL/CZ pozostają otwarte.
- Ten test nie dowodzi jeszcze uruchomienia rzeczywistego terenu w APK, nie zastępuje fotogrametrii, elewacji, modelowania całego miasta ani historycznej zgodności z latami fabularnymi.

Polska strona: zaimplementowano [sondę WCS GUGiK](geodata/gugik_wcs_probe.py), [walidator GetCoverage](geodata/gugik_nmt_live.py) i [sondę punktową NMT](geodata/gugik_nmt_point.py). Usługa udostępniła identyfikator `DTM_PL-KRON86-NH_TIFF` oraz kolejność osi `y,x`. Pobieranie rastra zostało przerwane po stronie serwera, a zapytanie punktowe po korekcie orientacji zakończyło się HTTP 502. **Polskie wysokości nie zostały pozyskane.** [Diagnostyka źródła](docs/WORLD_1_TO_1_GUGIK_NMT_SOURCE.md).

### Obecny postęp WORLD.03

- [Importer GeoJSON PL/CZ w metrach](geodata/geoetl.py) — przeliczenie EPSG:4326/2180/5514, kontrola licencji i pochodzenia, sektorowanie bez kompresji odległości.
- [Instrukcja importu GIS](docs/WORLD_1_TO_1_ETL_IMPLEMENTATION.md) — komendy, wejścia i ograniczenia.
- [Weryfikowane publiczne punkty ratuszy](geodata/fixtures/transborder_reference_points.geojson) — 2 punkty, nie kompletne dane o miastach.
- [Podgląd kontrolny w Godot](godot/scenes/world_preview.tscn) — 2 punkty w rzeczywistej odległości, siatka 256 m, powiększanie i przesuwanie.

**Uwaga:** zaimportowano wyłącznie częściowe, współczesne obrysy budynków i linie dróg OSM (bez wysokości i terenu). Nie istnieją gotowe historyczne cyfrowe bliźniaki obu miast.

## Zakres źródłowy

| Akt | Nazwa | Rozdziały |
| --- | --- | --- |
| I | PĘKNIĘCIE | 01–14 |
| II | WALKA Z MUREM | 15–41 |
| III | BEZ PRAWA | 42–62 |
| IV | KONIEC ŚWIATŁA | 63–70 |

Książka (409 stron) jest kanonem. Najnowsze decyzje autora mają pierwszeństwo przed dawnymi raportami technicznymi. Wcześniejszy projekt „Chronos” nie jest samodzielną podstawą fabularną. Tekst książki, prywatne nagrania Zuzi i chronione transkrypty **nie są kopiowane do repozytorium publicznego**.

## Dokumentacja i kod

- [Zasady produkcji Android](docs/ANDROID_ARCHITECTURE.md) — technika, sceny, sterowanie, wydajność, testy.
- [Otwarcie i reżyseria CH01](docs/OPENING_AND_CH01.md) — tytuł, prolog, czerwona kurtyna, pierwszy rozdział, wybory.
- [Kanon, źródła i prawa](docs/CANON_AND_MEDIA_POLICY.md) — co można publikować i kiedy.
- [Indeks 70 rozdziałów](data/chapter_index.json) — stabilne identyfikatory, przypisanie do aktu (nie jest pełnym scenariuszem).
- [Referencyjny silnik narracji](reference/MAN_OF_THE_YEAR_REFERENCYJNY_SILNIK_NARRACJI.py) — logika spotkań z Pauliną, CH59 i 3 odblokowań DLC.
- [Testy silnika](reference/test_MAN_OF_THE_YEAR_REFERENCYJNY_SILNIK_NARRACJI.py) — testy 16 wariantów i integralności stanu.

## Pobierz i uruchom APK Android

- [GitHub Actions — poprawny build APK i zapis artefaktu](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39525476347). Otwórz `Artifacts → man-of-the-year-android-debug`, pobierz ZIP, rozpakuj `man-of-the-year-debug.apk`.
- Format: Android ARM64, kompilacja debug, 27 733 460 B.
- SHA-256 pliku APK: `6385ea1e993b5bcbc131e75745b985cd4f5af220505b1dfd4ddddc42abd5e17d`.
- Zainstaluj debug APK na urządzeniu obsługującym ARM64 i OpenGL ES 3.0. Jest to eksperymentalny build do odbioru, a nie wersja produkcyjna. Jeśli poprzedni debug APK ma inny klucz podpisu, konieczne może być odinstalowanie poprzedniej wersji (co usuwa jej lokalne dane).

## Natywny prototyp: zawartość

W katalogu [godot/](godot/) są: sala gali z uproszczoną geometrią 3D, ekran tytułowy PL/EN, ekran prologu bez chronionego nagrania, rozsuwana czerwona kurtyna, karta Aktu I i Rozdziału 1, sterowanie dotykowe, oględziny obiektów, wykonanie i przegląd fotografii, dwie odrębne decyzje z checkpointem oraz podgląd dwóch georeferencjonowanych ratuszy oraz 397 obrysów budynków i 145 obiektów drogowych z dwóch wycinków OpenStreetMap; są to obrysy płaskie, nie modele 3D. Podgląd nie odtwarza geometrii budynków ani ulic. Potwierdzono uruchomienie projektu przez 30 klatek w środowisku CI bez GPU i 14 asercji silnika Godot. Testy CI nie dowodzą prawidłowego działania dotyku i grafiki na telefonie.

## Uruchomienie sprawdzalnej części

```bash
python -m unittest discover -s reference -p 'test_*.py' -v
```

Dodatkowo: `godot --headless --path godot --editor --import --quit` oraz `godot --headless --path godot --script res://tests/test_state.gd`. Testy narracyjne nie zastępują rzeczywistego testu Android.

## Najbliższy etap techniczny

1. Zainstalować wyeksportowany debug APK na realnym urządzeniu ARM64 i zebrać logcat, FPS, frametime i temperaturę.
2. Zastąpić uproszczony model gali, sceny i UI wersją zgodną z poziomem reżyserskim i zatwierdzić pełny lektorski prolog 1:1.
3. Zatwierdzenie modeli postaci i pipeline motion/facial capture.
4. Projekt i implementacja 70 rozdziałów, 280 sekwencji jako zakres *projektowy* (nie gotowe sceny), DLC i galerii.
5. Dowody CI, build Android, testy na sprzęcie, optymalizacja i odbiór.

Nie używaj nazwisk ani nazw osób z prywatnych materiałów jako dowodów zarzutów. Nie publikuj niezweryfikowanych oskarżeń i danych dzieci.
