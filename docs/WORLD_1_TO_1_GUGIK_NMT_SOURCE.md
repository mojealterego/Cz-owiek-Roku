# WORLD.03g — GUGiK: polski NMT, usługa WCS GeoTIFF

Źródło GUGiK: https://www.geoportal.gov.pl/pl/usluga/uslugi-pobierania-wcs/

Metadane dostępnej usługi: https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF?REQUEST=GetCapabilities&SERVICE=WCS

Polski NMT jest bezpłatnie udostępniany przez GUGiK. Dane występują m.in. w układach wysokościowych PL-EVRF2007-NH i PL-KRON86-NH: przed użyciem należy zweryfikować datum konkretnego pliku. Nie wolno automatycznie uznać tych układów za zgodne z czeskim Bpv. Nie wolno przeprowadzać pozornego wyrównania na podstawie wysokości pojedynczych obiektów.

Skrypt `geodata/gugik_wcs_probe.py` odkrywa dostępne Coverage ID i formaty GetCapabilities. Test syntetyczny **nie oznacza pobrania danych NMT**. Następny etap to GetCoverage ograniczonego obszaru Cieszyn Rynek (EPSG:2180), weryfikacja rzeczywistego GeoTIFF, właściwego datumu, hash wejścia i próbkowania sektorów 256×256 m.

W testach i komunikatach CI każde źródło o niepotwierdzonym datum ma status `NOT_VERIFIED`, nie wolno udawać poprawnej transformacji pionowej.

Oficjalne źródła: https://www.geoportal.gov.pl/pl/dane/numeryczny-model-terenu-nmt/ i https://www.gov.pl/web/gugik/dane-udostepniane-bez-platnie-do-pobrania-z-serwisu-wwwgeoportalgovpl
