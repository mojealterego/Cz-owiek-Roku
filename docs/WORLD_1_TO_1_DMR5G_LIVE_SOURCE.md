# ČÚZK DMR 5G — oficjalne źródło wysokości, pobranie QA

**Prawa redystrybucji wymagają odrębnego przeglądu.** Publiczny ImageServer z dostępem do wysokości nie oznacza automatycznej zgody na umieszczenie GeoTIFF i pochodnych kafli w publicznym repozytorium.

Źródło: https://ags.cuzk.gov.cz/arcgis2/rest/services/dmr5g/ImageServer

Ustalona metadana usługi: poziomo S-JTSK (EPSG:5514), pionowo Bpv (identyfikator VCS 8357), 2 m/piksel, jedna warstwa F32. Oryginalny DMR 5G oparto na skanowaniu 2009–2013. Daty skanowania terenu nie są automatycznie stanem z lat 2023–2025.

## Sposób działania
`geodata/cuzk_dmr5g_fetch.py` sprawdza metadane, prosi serwer o mały fragment GeoTIFF, weryfikuje magic bytes, rozmiar, georeferencję EPSG:5514 oraz rzeczywistą obecność numerycznych próbek. Następnie `geodata/terrain_geotiff.py` używa tylko surowych wysokości do sektorów QA.

[Live CI](https://github.com/mojealterego/Cz-owiek-Roku/actions/workflows/cuzk-dmr5g-live-qa.yml) **nie publikuje** danych surowych, kafli, zdjęć ani plików ZIP. Nie oznacza to wykonanej, zatwierdzonej rekonstrukcji terenu. Weryfikacja przeniesienia wysokości do świata Androida wymaga zgodnego pionowego datum i rzeczywistych danych referencyjnych przy budynkach.

## Nadal do wykonania
Potwierdzić licencję i warunki tworzenia pochodnego zbioru, doprowadzić polski NMT do zgodnego układu wysokości, zatwierdzić epokę i poprawność NMT w najważniejszych lokacjach oraz rozwinąć runtime streaming i siatkę terenu. Bez realnych pomiarów nie twierdzić, że cyfrowy bliźniak 1:1 został zrealizowany.

## QA z 21 października 2026
Próbne pobranie usługi ImageServer zakończyło się sukcesem. Format GeoTIFF źródła zawierał niepełną definicję `LOCAL_CS` z autorytetem EPSG:5514; po potwierdzeniu CRS, geograficznych granic i rozdzielczości zakodowano pełne odniesienie poziome EPSG:5514 bez modyfikowania współrzędnych ani wartości wysokości. Wykryto również zerowe próbki w źródle, które w tym obszarze nie mogą być bez weryfikacji uznane za powierzchnię terenu. Tryb `--zero-is-unverified-nodata` oznacza je jako brak danych **tylko w sektorach QA**, zachowując oryginalny plik niezmieniony. Weryfikacja historyczna, prawna oraz pionowe zestrojenie z budynkami nadal pozostają otwarte.

## Wynik testu produkcyjnego QA — 21.10.2026
- Run: https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39570793520 (success).
- Źródłowy raster: 450 × 450 pikseli Float32, Bpv, układ poziomy 5514; 26 561 wartości zero w pełnym wycinku wymagających ostrożnego traktowania jako potencjalny brak danych.
- Wybrane cztery sektory 256 × 256 m: 324 próbek rzeczywistych, zero braków po zastosowaniu maski kontrolnej. **Nie oznacza to kompletnego pokrycia miasta.**
- Dokładności pionowej oraz zgodności z polskim datum nie przyjęto jako zweryfikowanej. Zabezpieczono wynik przed automatycznym eksportem publicznym.
