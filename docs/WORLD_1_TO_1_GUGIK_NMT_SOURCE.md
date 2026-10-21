# WORLD.03g — GUGiK: polski NMT, usługa WCS GeoTIFF

Źródło GUGiK: https://www.geoportal.gov.pl/pl/usluga/uslugi-pobierania-wcs/

Metadane dostępnej usługi: https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF?REQUEST=GetCapabilities&SERVICE=WCS

Polski NMT jest bezpłatnie udostępniany przez GUGiK. Dane występują m.in. w układach wysokościowych PL-EVRF2007-NH i PL-KRON86-NH: przed użyciem należy zweryfikować datum konkretnego pliku. Nie wolno automatycznie uznać tych układów za zgodne z czeskim Bpv. Nie wolno przeprowadzać pozornego wyrównania na podstawie wysokości pojedynczych obiektów.

Skrypt `geodata/gugik_wcs_probe.py` odkrywa dostępne Coverage ID i formaty GetCapabilities. Test syntetyczny **nie oznacza pobrania danych NMT**. Następny etap to GetCoverage ograniczonego obszaru Cieszyn Rynek (EPSG:2180), weryfikacja rzeczywistego GeoTIFF, właściwego datumu, hash wejścia i próbkowania sektorów 256×256 m.

W testach i komunikatach CI każde źródło o niepotwierdzonym datum ma status `NOT_VERIFIED`, nie wolno udawać poprawnej transformacji pionowej.

Oficjalne źródła: https://www.geoportal.gov.pl/pl/dane/numeryczny-model-terenu-nmt/ i https://www.gov.pl/web/gugik/dane-udostepniane-bez-platnie-do-pobrania-z-serwisu-wwwgeoportalgovpl

## Diagnostyka usług, 21.10.2026
- Udany WCS `GetCapabilities` dla oficjalnego `DTM_PL-KRON86-NH_TIFF` i `DescribeCoverage`, który zgłosił układ EPSG:2180 i kolejność osi `y,x` ([run 39572299216](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39572299216), [run 39572769470](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39572769470)).
- Po dopasowaniu żądania do osi `y,x` usługa zerwała połączenie podczas `GetCoverage` bez odpowiedzi. **Nie pozyskano rastra NMT** ([run 39572972538](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39572972538)).
- Osobne `GetHByXY` zwróciło przy pierwotnej orientacji niespójną dla Cieszyna wartość 41,9 m. Zmieniono kolejność parametrów zgodnie z konwencją geodezyjną X=północ, Y=wschód, ale powtórna próba zwróciła HTTP 502. **Nie uznajemy żadnej z tych wartości za poprawny pomiar** ([run 39574279502](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39574279502)).
- Żądania sieciowe są teraz **manualne (`workflow_dispatch`)**, żeby awaria zewnętrznego serwera nie powodowała czerwonych testów kodu przy każdym commicie. Kontrola parsowania odpowiedzi pozostaje testowana offline.
