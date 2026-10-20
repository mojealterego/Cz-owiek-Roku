# WORLD.03 — Geospatial importer PL / CZ (wykonany kod, brak pełnych modeli miasta)

## Faktycznie zaimplementowane
- `geodata/geoetl.py`: walidowany import **rzeczywistego GeoJSON** (budynki 2D / ulice / punkty), transformacja EPSG:4326, 2180, 5514 do wspólnego lokalnego układu AEQD w metrach wokół geograficznej kotwicy.
- Sektorowanie **256×256 metrów**, także dla ujemnych indeksów i geometrii przecinającej granice sektora; oryginalna geometria nie jest upraszczana.
- Zweryfikowane **współrzędne dwóch publicznych ratuszy** do testu transgranicznego. Odległość elipsoidalna WGS84 około **584,696 m**. To dwa punkty odniesienia, a nie gotowe budynki.
- Manifest każdego eksportu zawiera SHA-256 wejścia, źródło i licencję, rok, CRS, liczby obiektów/sektorów oraz jawny brak danych o wysokości, terenie i elewacjach.
- Błędy i niebezpieczne zasoby: nieznana projekcja, błędna geometria, duplikat ID, próba zapisania do niepustego katalogu, ponadlimitowy plik, brak informacji o prawach. Bez zatwierdzonej licencji **tylko `--internal-preview`**, nie można użyć trybu produkcyjnego.

## Weryfikacja reprezentacji
Źródła koordynatów ratuszy:
- PL, Ratusz Cieszyn, Rynek 1 (WGS84 18.6332106,49.7481600): https://mapy.com/pl/?id=94209443&source=osm
- CZ, Radnice Český Těšín, náměstí ČSA 1/1 (WGS84 18.62559852404365,49.746341767306085): https://regiony.kurzy.cz/cesky-tesin/namesti-csa/1-1/

Geodezyjne punkty nie są pomiarem granic nieruchomości ani dokumentacją stanu z 2025 r. Dane źródłowe pochodzą z jawnych publicznych informacji o współrzędnych obiektów, nie z kopiowania zdjęć.

## Wywołanie
```bash
python -m pip install -r geodata/requirements.txt
python -m unittest geodata.test_geoetl -v
python -m geodata.geoetl \
  --input geodata/fixtures/transborder_reference_points.geojson \
  --output-dir /tmp/world_reference_tiles \
  --city-id CIESZYN_TRANSBORDER \
  --source-crs EPSG:4326 \
  --anchor-lon 18.6332106 --anchor-lat 49.7481600 \
  --source-id LANDMARKS_VERIFIED_PUBLIC_COORDS \
  --source-url 'https://mapy.com/pl/?id=94209443&source=osm' \
  --license SOURCE_REVIEW_PENDING --internal-preview \
  --year 2025
```

Wynik: `manifest.json` i pliki `E..._N....json` zawierające lokalne współrzędne geometrii w metrach. Do importu większych danych GUGiK BDOT10k i ČÚZK potrzebne będą **pobrane, poprawnie licencjonowane** GeoJSON lub konwersja GPKG/GeoParquet do GeoJSON (GDAL/QGIS z jawnie wskazanym CRS).

## Wciąż niewykonane
- **Nie pobrano** jeszcze baz BDOT10k/ČÚZK, nie ma obrysów budynków ani ulic dla rzeczywistego Cieszyna; niemożność pobrania w bieżącym środowisku nie jest dowodem braku danych.
- Nie ma numerycznego modelu terenu (NMT), pionowego datumu, brył LoD2/elewacji/fotogrametrii ani kompletnej rekonstrukcji historycznej.
- Runtime Godot nie ma jeszcze strumieniowania sektorów — ten moduł przygotowuje deterministyczny format danych wyjściowych, a nie gotowy świat gry.
- Nie wolno nazywać dwóch punktów i konwertera **„odwzorowaniem miasta 1:1”**. Zgodność skali metrycznej jest pierwszą, niewystarczającą bramką jakości.

## Źródła danych do następnej fazy
- GUGiK BDOT10k: https://www.geoportal.gov.pl/pl/dane/baza-danych-obiektow-topograficznych-bdot10k/
- GUGiK 3D: https://www.geoportal.gov.pl/pl/dane/inne-dane/modele-3d-budynkow/
- GUGiK WFS: https://mapy.geoportal.gov.pl/wss/service/PZGIK/BDOT/WFS/PobieranieBDOT10k
- ČÚZK: https://geoportal.cuzk.cz/
- ODbL: https://osmfoundation.org/wiki/Attribution_Guidelines

Przed połączeniem danych źródłowych o różnych licencjach należy wykonać kontrolę obowiązków dla zbioru pochodnego, nie tylko dla grafiki w grze.
