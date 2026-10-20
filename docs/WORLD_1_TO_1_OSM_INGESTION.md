# WORLD.03b — rzeczywiste obrysy Cieszyna, automatyczny import OSM

Status: importer i jednorazowy workflow CI. **Dane geometrii liczą się dopiero po zakończonym pobraniu, walidacji i commicie; nie należy utożsamiać samego istnienia skryptu z importem.**

Źródło: https://api.openstreetmap.org/api/0.6/map?bbox=18.631%2C49.7468%2C18.634%2C49.7492

## Zakres i bezpieczeństwo
- Wycinany obszar: Cieszyn, centrum w okolicach Rynku. Nie jest to pełny Cieszyn ani obszar całego Czeskiego Cieszyna.
- Kategoria: **building** — tylko poprawne, domknięte poligony OSM typu way; wysokości nie są znane, nie wolno ich zgadywać.
- Kategoria: **road** — linie ways oznaczone `highway`, bez dopisywania szerokości, chodników, tekstur lub ruchu pojazdów.
- Niezaimplementowane: relacje multipolygon, poziomy budynków, wysokości, LiDAR, elewacje, granice działek, historyczne zmiany z lat 2023–2025.
- Input: pobrany XML OSM (bounded API). Parser wykorzystuje `defusedxml` i waliduje współrzędne, zamknięcia budynków, identyfikatory oraz limity wielkości.
- Licencja: **© OpenStreetMap contributors, ODbL 1.0**. Szczegóły: https://www.openstreetmap.org/copyright i https://opendatacommons.org/licenses/odbl/1-0/ . Publikowany wycinek GeoJSON i kafle wynikowe objęte informacją ODbL. Osobno kontrolować wymagania atrybucji w aplikacji oraz warunki udostępnienia pochodnej bazy danych.
- Historia: `2026 CURRENT_BASEMAP_NOT_HISTORICALLY_VERIFIED` — **nie wolno** przypisywać tych danych jako wiarygodnego stanu ulic i fasad z 2023–2025.

## Pipeline
1. `geodata/osm_extract.py` pobiera mały XML i tworzy GeoJSON z oryginalnymi identyfikatorami OSM, bez importu danych edytorów/właścicieli.
2. `geodata/geoetl.py` przelicza WGS84 → lokalny metryczny AEQD i obcina geometrię na granicach sektorów po 256 m.
3. Manifest eksportu podaje źródło, licencję, hash wejściowego GeoJSON, `tile_count`, `source_features` i jawną informację o braku terenu/wysokości.
4. GitHub Actions `osm-city-import.yml` waliduje minimum obrysów i zapisuje geometrię do `godot/data/world/cieszyn_rynek_osm_2026`.
5. Podczas gry wyświetlanie może używać **płaskich obrysów**, nie fikcyjnej trójwymiarowej zabudowy.

## Weryfikacja
```bash
python -m pip install -r geodata/requirements.txt
python -m unittest geodata.test_osm_extract geodata.test_geoetl -v
```

## Następne iteracje
Dla Česky Těšín i pozostałych miast wykonać analogiczne, ograniczone wycinki. Dane GUGiK/ČÚZK mają docelowo zastąpić roboczy OSM tam, gdzie zapewnią większą dokładność i historyczne referencje. Nie wolno uznać żadnego budynku za skan 3D ani scenografię 1:1 bez fotogrametrii/geometrycznych pomiarów.
