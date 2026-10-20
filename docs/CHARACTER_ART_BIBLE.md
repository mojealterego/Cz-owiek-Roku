# MAN OF THE YEAR — CHARACTER ART BIBLE v1

**Status:** `USER_DIRECTED`. To kontrakty artystyczne postaci do procesu `character concept → sculpt → topology → rig → materials → LOD → facial/animation → acceptance`, a nie dowód wyprodukowania ich modeli 3D.

## Wiek rzeczywisty a referencja wizualna
Dwa niezależne pola: `story_age` (kanon) oraz `visual_age_target` (instrukcja look-dev). Model 3D nie może losowo postarzać postaci przez zastosowanie nadmiernych zmarszczek, zapadniętych policzków ani przesadnej faktury skóry.

### ANDRZEJ
- `story_age=43`, `visual_age_target≈35`; naturalna, szczupła, sprawna fizycznie sylwetka; twarz gładko ogolona; zadbana modna fryzura, okulary.
- Strój bazowy: elegancka koszula niebieska **lub** czarna; beżowe spodnie w kratę; brązowy pasek; elegancki czarny zegarek.
- Widoczne zawsze przy standardowym ubiorze: tatuaże na dłoniach, przedramionach, szyi, aż za uszy.
- Rig: oddzielne kontrolery mimiki zmęczenia, wahania, dłoni i chwytu aparatu; subtelna gestykulacja zamiast stałego „paska szaleństwa”.
- W scenach bez koszuli: kompletna mapa tatuaży niżej; nie zastępuj ich losowymi ornamentami ani generatywnym noise.

### WERONIKA
- `story_age=40`, `visual_age_target≈30`.
- Atrakcyjna blondynka, różowe pasemka; elegancka, realistyczna twarz; kontrolowane chłodne mikroekspresje i język ciała.
- Negatywna ocena zachowania należy do **perspektywy narratora**; model, opisy i reklama gry nie powinny stawiać diagnozy psychiatrycznej rozpoznawalnej osobie.

### PAULINA
- `story_age=29`, `visual_age_target=29`.
- Projektowana jako najbardziej olśniewająca wizualnie postać gry: naturalna atrakcyjność, długie proste ciemne włosy **poniżej pośladków**, duże intensywnie niebieskie oczy, długie lecz naturalne rzęsy.
- Tatuaże: **lewe ramię** i **lewa dłoń**. Zakaz lustrzanego odwrócenia tekstur na modelu.
- Animacja włosów wydajna mobilnie (guide strands / cards / LOD); naturalne zachowanie przy ruchu, bez penetracji przez ubranie.

### WIOLA (SIoSTRA PAULINY)
- `story_age=23`, twarz i kolorystyka podobne do Pauliny; pełniejsza sylwetka, pogodna ekspresja, tatuaż na **przedniej** części szyi.
- W pierwszej styczniowej okazji do rozmowy `PAU-OP1` idzie razem z Pauliną. To nie dowodzi, że identycznie nazwana osoba bonusowa w galerii jest tą samą Wiolą — rozdziel postacie do czasu autorskiego potwierdzenia.
- Jeśli autor potwierdzi tożsamość, wykonaj migrację referencji; nie łącz postaci przez zbieżność imienia.

## ANDRZEJ — ANATOMICZNA MAPA 10 GRUP TATUAŻY

Zawsze używaj **anatomicznej prawej/lewej strony postaci**, nie strony obrazu widzianej w lustrze.

| Grupa | Obszar | Wymagana ikonografia |
|---|---|---|
| 01 | Prawa noga | Spiralna taśma filmowa z pięcioma scenami życia Zuzi i nagłówkiem daty |
| 02 | Lewa noga | Ciężka industrialna biomechanika: tryby, śruby, przewody, tłoki, rozdarta iluzorycznie skóra |
| 03 | Prawe żebra | Mistyczny szaman z kapturem, naszyjnik, iglasty las i mgła, różowo-fioletowo-żółte akcenty |
| 04 | Lewe żebra | Nordycki wojownik Harald z runami na twarzy, brodą, futrem, amuletem, lasem |
| 05 | Brzuch | Pierwotny wojownik inspirowany archetypem Ragnara, war paint, skrzydła kruka, mglisty las |
| 06 | Klatka piersiowa | Dynamiczna scena bitewna: dwaj wojownicy, czaszka, znaki runiczne, ciemny las |
| 07 | Plecy | Santa Muerte: dekoracyjna kobieca czaszka, koronki, nasycone **niebieskie włosy**, oczy fiolet/pomarańcz/żółć; niżej czerwone róże |
| 08 | Lewe ramię i dłoń | Wojownik/bóg inspirowany Thorem, Ivar, twarz z geometrią spiralną, kobieta-czaszka w rust-mesh |
| 09 | Prawe ramię i dłoń | Ragnar + okręty + róża; Floki na wewnętrznym bicepsie; Bjorn z tarczą; oko w siatce na dłoni |
| 10 | Cała szyja | Przód: realistyczna czaszka przechodząca w kręgosłup. Boki: kobiece sugar skull z falującymi włosami i różami |

### Prawa noga — zawartość 1:1
Nagłówek w kroju typewriter: `SCENY Z ŻYCIA ZUZIA 07.07.2016`.

Pięć kadrów taśmy: (1) noworodek w kocu, (2) uśmiechnięta dziewczynka do obiektywu, (3) czuły pocałunek rodziców, (4) dziecko trzymające kredki, (5) gest obronny dziecięcych dłoni i inna dłoń wyciągnięta w tęsknocie.

Dodatkowa typografia: `STOP PARENTAL ALIENATION`; `Art. 111 § 1 KRiO`; `PAS 04.03.2024r`. Przy stopie otwarta kaseta filmowa i polaroid przedstawiający góry.

### Shader/materiały/wydajność
- PBR skóry z odrębnymi maskami tuszu, sub-surface na podstawie docelowego mobilnego renderera; bez decal draw-call explosion.
- Atlas tekstur o poziomach jakości, skompresowane tekstury mobilne i kontrola mip-map. Priorytet: spójne UV, brak odwróconych stron i zniekształconych napisów.
- Materiały skóry projektuj na wielu ekspozycjach; kolorowa Santa Muerte zachowuje niebieskie włosy i pomarańczowe akcenty oczu niezależnie od neutralności oświetlenia.

### Character acceptance checklist
- [ ] 360° neutral + expression sheet PL/EN labels
- [ ] Front/side/back i kompletne UV dla wszystkich 10 grup
- [ ] Dokładne napisy nóg bez generatywnych błędów literowych
- [ ] Ciała odległe i bliskie: LOD oraz kontrola faktury/ciągłości tatuażu
- [ ] Stabilny rig twarzy i blendshapes, synchronizacja w scenach dialogowych
- [ ] Użytkownik zatwierdził wygląd przed finalną produkcją
- [ ] Ustalono prawa do wzorów, wizerunków i ewentualnych fotografii referencyjnych

Wizualne archetypy historyczne i serialowe służą tylko jako inspiracja; nie kopiować twarzy aktorów.
