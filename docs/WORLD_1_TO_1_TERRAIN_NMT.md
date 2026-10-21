# WORLD.03e — DEM/NMT georeferencyjne (GeoTIFF → metryczne sektory)

**Status: importer + testy; w repozytorium wciąż nie ma rzeczywistych wysokości terenu.**

## Warunki wejścia
- Jednopasmowy GeoTIFF z rzeczywistymi wysokościami w metrach, georeferencją i jawnie zadeklarowanym poziomym EPSG (2180, 2177/78/79, 5514 lub 4326).
- Jawny **pionowy datum** (np. dokładny wariant PL-EVRF2007-NH albo CZ-BPV), potwierdzony na podstawie metadanych źródła; nie wolno uznać wariantów za równoważne.
- Źródło, epoka danych, hasz SHA-256 pliku wejściowego i stan uprawnień. Tryb publicznego wyjścia wymaga pozytywnej weryfikacji praw; inaczej tylko tryb wewnętrzny.
- Można importować faktyczne produkty GUGiK (polski NMT) lub ČÚZK (czeski DMR 5G) po sprawdzeniu formatu i warunków pobrania.

## Działanie
`geodata/terrain_geotiff.py` dokonuje **wyłącznie poziomej** transformacji CRS do wspólnego lokalnego układu metrycznego AEQD z kotwicą Cieszyn Rynek (18.6332106,49.74816). Próbkuje węzły siatki 256 × 256 m z podziałem 8/16/32/64 m. Każdy plik sektora przechowuje źródłowe wysokości i `null` dla NoData. Brak interpolowania brakujących obszarów, generowania pagórków ani przesuwania wysokości do umownego poziomu ulic.

**Bez aktywnego wyrównania datum pionowego nie wolno** mieszać danych PL/CZ z geometrią CityGML ani rysować dróg OSM jako dopasowanych do NMT. Manifest celowo zwraca `vertical_registration_to_game=NOT_VERIFIED` oraz `historical_facades_validated=false`.

## Przykład na *własnym, zatwierdzonym* GeoTIFF
```bash
python -m pip install -r geodata/requirements.txt
python -m pip install rasterio==1.4.3 numpy==2.2.6
python -m geodata.terrain_geotiff \
  --input /private_sources/PL_GUGIK_NMT_Cieszyn.tif \
  --output-dir /private_outputs/CIESZYN_NMT_QA \
  --city-id PL_CIESZYN --source-id GUGIK_NMT_VERIFIED \
  --source-url https://www.geoportal.gov.pl/ \
  --license-id OFFICIAL_TERMS_TO_REVIEW \
  --vertical-datum PL-EVRF2007-NH \
  --source-epoch 2024 \
  --west -1 --east 0 --south -1 --north 0 --spacing-m 32 \
  --internal-preview
```
Powyższa nazwa pliku jest **przykładem**, nie istniejącym ani pobranym zasobem. Weryfikacja oznaczenia datumu jest odpowiedzialnością audytu metadanych źródła. Nie utożsamiaj roku produktu źródłowego ze stanem historycznym miasta.

## CI
`python -m unittest geodata.test_terrain_geotiff -v` uruchamia syntetyczne dane oznaczone `TEST_ONLY`. Weryfikuje zero sztucznych wysokości, NoData, identyczność krawędzi sąsiednich sektorów, geometrię PL/CZ i kontrolę praw. Test nie stanowi dowodu pozyskania DEM ani poprawności na Androidzie.

## Dalsze kroki
Pobrać **rzeczywiste** GeoTIFF/ASCII NMT z publicznych zasobów, zatwierdzić prawo publikacji i epokę, potwierdzić pionowy datum i dokładność, wykonać import z rzeczywistym rasterem, a następnie dodać renderer terenu do Godot **dopiero po kontroli pionowej kompatybilności z budynkami**.
