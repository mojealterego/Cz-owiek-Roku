# Reżyseria otwarcia i CH01 — wersja wykonawcza koncepcji

**Pierwszeństwo: instrukcja autora, następnie książka (strony PDF 3 i 17–20).**

## SEQ-000 — TITLES / PL+EN
- Pełna czerń, brak HUD.
- Po ciszy dźwięk mechanicznej migawki fotograficznej; centralny napis `CZŁOWIEK ROKU`; wariant `MAN OF THE YEAR` zgodny z lokalizacją.
- Minimalna typografia w kości słoniowej. Nie używaj UI Quantic Dream ani ich muzyki.

## SEQ-001 — PROLOG / „SŁOWO OD CZŁOWIEKA ROKU”
- Montaż filmowy bez sterowania: obiektyw i wizjer aparatu; reflektory gali; nagrody; pokój dziecka i pusty korytarz; zerwane połączenie telefoniczne.
- Lektor **czyta całe „Słowo od Człowieka Roku” ze strony 3 książki**; wersja polska zachowuje dokładne brzmienie, przekład EN wymaga autoryzacji. Do momentu otrzymania zatwierdzonego tekstu i voice-overu produkcyjny asset pozostaje niedostarczony; nie używaj fikcyjnego „oryginalnego” audio.
- Kamera: 24 fps w cinematics wyłącznie przy zaakceptowanym profilu urządzenia; runtime gameplay ma cel 30 fps. Żaden kadr nie może ujawnić finału.
- Dźwięk muzyki stopniowo zanika przed wejściem kurtyny.

## SEQ-002 — KURTYNA I AKT I
- Fizycznie animowana, ciężka, bordowo-czerwona aksamitna kurtyna zasłania pełny ekran.
- Na kurtynie: `AKT I — PĘKNIĘCIE`; poniżej cytat `Każde pęknięcie zaczyna się od milczenia.`
- Po 2–4 s (podlega reżyserii i opcji pominięcia po ukończeniu raz) poły kurtyny odsuwają się na lewą i prawą stronę z odgłosem ciężkiej tkaniny.
- Zamiast przejść od razu do gameplayu: pojawia się osobna karta `ROZDZIAŁ I`, cytat `Piekło to inni.` — Jean-Paul Sartre, następnie książkowy dopisek Andrzeja o Cieszynie. Autor nakazał w planszy datę `Cieszyn 2023 r.`; oznacz jako `USER_DIRECTED`.
- Wznowienie obrazu z perspektywy Andrzeja stojącego **za kurtyną gali**.

## CH01 — PIERWSZY POZIOM, CIESZYN / GRUDZIEŃ 2023

### Scena 01: za kulisami
Kamienny hol, drewniana scena, ciemnoczerwone kulisy, kurz oświetlony reflektorami, szmer widowni. Bohater poprawia okulary, dotyka aparatu. Kamera zza prawego ramienia. Sterowanie ruchem dopiero po zakończeniu karty rozdziału.

### Scena 02: fotografia kontra wizerunek
Opcjonalne badanie 3 przedmiotów: aparat, program gali, fotografia rodzinna. Wizjer jest interaktywny — wybór kadru powoduje zapis obserwacji, ale nie automatyczne uznanie interpretacji za fakt. HUD tylko w trybie interakcji. Obiekty mają stabilne `evidence_id`.

### Scena 03: decyzja
`CH01-CHOICE-01`:
- A: fotografuj pierwszy rząd widowni — otrzymujesz zapamiętany kadr i inny późniejszy komentarz narratora.
- B: opuść aparat i obserwuj ludzi — otrzymujesz ślad pamięci dźwiękowej i inny komentarz.
Obie decyzje muszą mieć odrębne animacje, dźwięk, wpis `choice_ledger` i dialogiczną reakcję. Nie zmieniają wręczenia nagrody ani kanonu.

### Scena 04: nieuchronna konwergencja
Andrzej wychodzi na scenę, otrzymuje wyróżnienie. Światła chwilowo prześwietlają kadr. Potem krótka cisza i przejście do CH02. Przy przejściu system zapisuje `CH01_COMPLETED`, `CH01-CHOICE-01`, ewentualny wpis do galerii oraz checkpoint.

## Kryteria odbioru pierwszego poziomu
- Prolog bez grywalności i prawidłowe otwieranie kurtyny; epigraf osobno.
- PL i EN, kontrast i czytelność tekstu na ekranach 16:9 do 22:9.
- Dwie realne reakcje na wybór; zapis stanu po ponownym uruchomieniu.
- Obsługa dotyku (lewy wirtualny joystick, prawa strefa kamery, kontekstowa interakcja, aparat, pauza).
- Brak ukończenia, dopóki nie istnieje rzeczywisty wykonywalny build na Androidzie.

## Projekt stycznia 2025 — celowo oddzielny
Szczegółowy projekt Pauliny należy osadzić w oknie czasowym CH54 i opcjonalnych sekwencjach `PAU-OP1..PAU-OP4`. Pierwsza okazja: Paulina (29) idzie z siostrą Wiolą (23). Gracz może podejść lub przejść obok, a przy kolejnych okazjach zapoczątkować znajomość. W CH59 Paulina **zawsze** pojawia się w lodziarni; wczesny kontakt otwiera poboczne questy, ale nie zmienia głównego finału. Dodatkowe spotkania są `PROPOSED_ADAPTATION` i nie wolno udawać, że pochodzą bezpośrednio z tekstu książki.
