# WORLD.05a — aktywne sektory świata i budżet pamięci (Godot 4.5.2)

**Status:** działający strumieniowy podgląd rzeczywistych sektorów OSM (2D, rok 2026), weryfikacja CI. **Nie jest to ukończony otwarty świat 1:1.**

## Implementacja
- `godot/scripts/osm_tile_streamer.gd`: czyta **indeks nazw sektorów**, a nie wszystkie duże pliki z geometrią, zanim pojawi się pozycja kamery.
- `world_preview.gd`: dwa niezależne kontrolery (Cieszyn i Český Těšín), ustawiające środek mapy jako punkt aktywacji; widok pokazuje liczbę aktywnych sektorów i meshy.
- `osm_preview_layer.gd`: dotychczasowa walidacja i renderer z opcjonalnym wyłączeniem automatycznego pełnego importu; jeden węzeł sektora renderuje tylko własną geometrię.
- Wspólny układ AEQD, metry (1 jednostka = 1 metr), siatka **256 × 256 m**, referencja obu miast bez przesuwania geograficznych obrysów.
- Maksymalnie **6 sektorów rezydentnych na miasto** i **2 nowe sektory na klatkę na miasto**, kolejka najbliższych punktowi zainteresowania, zwalnianie opuszczonych sektorów.
- Odczyt wyłącznie danych OSM z kontrolą licencji ODbL, źródła, roku, identyfikatora i prawidłowego originu sektora. Warianty historyczne i właściwy NMT nie są mieszane do tego podglądu.

## Dowody
[CI Godot #39586189163](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39586189163) testuje jednocześnie oryginalny import całości i dynamiczny streamer, przejścia PL → CZ, limity RAM, zwalnianie i walidację źródeł.
[Android debug #39586189203](https://github.com/mojealterego/Cz-owiek-Roku/actions/runs/39586189203) wyeksportował poprawny APK ARM64. Nie ma jeszcze potwierdzenia zachowania na fizycznym Androidzie.

## Ograniczenia i następny etap
1. Testy powstały na małych wycinkach OSM: nie sprawdzają rzeczywistego, pełnego miasta.
2. Dekodowanie plików JSON i budowa `ImmediateMesh` odbywa się nadal na głównym wątku. Budżet 2 sektory/klatkę **nie gwarantuje 30 FPS**. Wymagane benchmarki, dłuższe sesje, pamięć i szybkość przesuwania kamery.
3. Dla złożonego świata należy wprowadzić ograniczenia według liczby wierzchołków i RAM, LOD oraz asynchroniczne przygotowanie danych. Nie należy włączać niezweryfikowanego terenu 3D ani mieszać datum Bpv/KRON86.
4. Mapa nadal pokazuje współczesne obrysy i drogi; brak weryfikacji fotogrametrycznej elewacji z lat książki 2023–2025.
