# WORLD 1:1 — GUGiK CityGML LoD1 / 2024

**Status: importer źródłowy + testy kontraktowe. Dane CityGML powiatu cieszyńskiego nie zostały jeszcze pobrane do repozytorium i nie ma z nich modeli w grze.**

## Fakty potwierdzone przez GUGiK
GUGiK publikuje modele CityGML LoD1 z roku 2024 dla całej Polski. Źródła obejmują obrysy BDOT10k, skaning ALS/LiDAR i NMT 1 m; atrybut `measuredHeight` jest **przybliżoną** wysokością, a nie ręcznym pomiarem każdego budynku. LoD1 to uproszczone graniastosłupy, nie wiernie odtworzone elewacje.

- https://www.geoportal.gov.pl/aktualnosci/nowe-modele-budynkow-3d-z-2024-roku-w-standardzie-lod1-dostepne-dla-obszaru-calego-kraju/
- https://www.geoportal.gov.pl/pl/dane/inne-dane/modele-3d-budynkow/

## Jak pozyskać plik
Geoportal → Dane do pobrania → Topografia → Modele 3D budynków → Budynki LoD1–2024 → wskaż powiat cieszyński → pobierz autentyczną paczkę CityGML. Należy zweryfikować URL i rok przed pobraniem. **Nie ma tu wymyślonego bezpośredniego URL archiwum.**

## Import
```bash
python -m pip install -r geodata/requirements.txt
python -m geodata.citygml_lod1 \
  --input /authorized_download/chunk.gml \
  --output /controlled_generated/cieszyn_citygml_lod1_2024.json \
  --source-crs EPSG:2180 \
  --axis-order east-north --year 2024
```
Ważne: `--source-crs` oraz `--axis-order` trzeba potwierdzić względem rzeczywistych współrzędnych GML; parser odrzuca sprzeczny CRS i odległe punkty, lecz **nie zastępuje** geodezyjnego audytu osi i wysokości. Wartości z GML Z pozostają bez zmiany (z jawnym niezidentyfikowanym datum), a `measuredHeight` jest przechowywane wyłącznie wtedy, gdy znajduje się w pliku.

`geodata/test_citygml_lod1.py` korzysta z **syntetycznej** geometrii do regresji parsera — ten test nie jest modelem żadnego rzeczywistego budynku.

## Bramka produkcyjna
- Pobrać pliki CityGML LoD1–2024 z powiatu cieszyńskiego.
- Potwierdzić CRS/osiowość/wysokości PL-EVRF2007-NH w dokumentach źródłowych i pomiarach kontrolnych.
- Wyciąć geograficzny sektor Cieszyna, porównać `buildingId`/BDOT10k z obrysami i przypisać sceny książkowe.
- Dopiero potem pokazać *rzeczywiste* bryły LoD1 na właściwych wysokościach; wygląd historyczny z 2023–2025 oraz fasady wymagają odrębnego udokumentowania.
