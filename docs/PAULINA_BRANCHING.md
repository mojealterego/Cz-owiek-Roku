# Paulina / Wiola — kontrakt narracyjny i testów

**Obowiązujące:** 4 opcjonalne okazje w styczniu 2025; pierwsza scena to Paulina idąca z siostrą Wiolą. Niezależnie od wyborów Paulina pojawia się w lodziarni w CH59. Podejście otwiera zadania i wcześniejsze relacje; zignorowanie wszystkich okazji odcina wyłącznie gałąź opcjonalną.

## Kanon i lokacja
Występ Pauliny w lodziarni w rozdziale 59 jest `SOURCE_VERIFIED`; wcześniejsze spotkania styczniowe i dodatkowe questy stanowią `PROPOSED_ADAPTATION`, do osadzenia przez reżysera w prawidłowej chronologii w oknie CH54. Nie twierdzić, że wymyślone dialogi i miejsca są cytatami z książki.

## State machine
```text
JANUARY_OPEN
  ├─ OP1: Paulina + Wiola -> APPROACH => MET_EARLY (Wiola świadkiem)
  │                            PASS     => UNMET
  ├─ OP2: możliwość podejścia; jeśli już znana -> FOLLOW_UP
  ├─ OP3: możliwość podejścia; jeśli już znana -> FOLLOW_UP
  └─ OP4: ostatnie styczniowe spotkanie -> JANUARY_CLOSED
                         ↓
               CH59 / LODZIARNIA
     (PAULINA_PRESENT zawsze prawdziwe)
               ├─ KNOWN_CUSTOMER
               └─ FIRST_MEETING_CUSTOMER
                         ↓
         CANONICAL_ENDING (bez zmian)
```

**Uwaga do referencyjnego modelu Python:** Funkcja `record_paulina_opportunity` obecnie przyjmuje wybory APPROACH/PASS dla wszystkich czterech okazji; interpretuje pierwsze APPROACH jako pierwsze poznanie, a kolejne jako zapis zainteresowania, ale nie generuje właściwych FOLLOW_UP animacji. Te należy zrealizować w silniku 3D. Zachowaj rozróżnienie `branch_available` (poznali się wcześniej) i `canonical_icecream_shop_present` (zawsze true).

## Warianty i konsekwencje
| Wariant | Poznanie | Wiola przy poznaniu | Questy Pauliny | CH59 |
|---|---|---|---|---|
| Podejście w OP1 | w OP1 | tak | otwarte | wspólna historia |
| PASS OP1, podejście w OP2 | w OP2 | niepotwierdzone | otwarte, inne tempo | wspólna historia |
| PASS OP1–2, podejście w OP3 | w OP3 | niepotwierdzone | otwarte, mniej czasu | wspólna historia |
| PASS OP1–3, podejście w OP4 | w OP4 | niepotwierdzone | otwarte, późno | wspólna historia |
| PASS wszystkich | dopiero CH59 | nie | poboczne styczniowe utracone | pierwsze spotkanie |

Reguły: idempotentne zdarzenia, jednokierunkowa chronologia, jawny zapis wyboru, nieingerowanie w zakończenie, brak blokady kampanii przez poboczny quest. Relacja ma konsekwencje w dopuszczonych sekwencjach: inne spojrzenia, kontakt, fotografie, pamięć i dialogi. Po OP4 dalszych retroaktywnych zmian stycznia w bieżącym przejściu nie ma.

## Testy obowiązkowe
1. Wylicz wszystkie 16 kombinacji PASS/APPROACH na 4 okazjach.
2. Każda dochodzi do CH59 i potwierdza obecność Pauliny.
3. Tylko co najmniej jedno APPROACH odblokowuje wcześniejsze questy.
4. Wiola przy pierwszym poznaniu dokładnie w OP1.
5. Nie wolno zmienić już zatwierdzonej decyzji; identyczny replay jest idempotentny.
6. CH59 nie może pojawić się przed rozliczeniem styczniowych spotkań.
7. Replay save/load zachowuje typy flag i nie nadpisuje wcześniejszych decyzji.
8. Wszystkie 70 rozdziałów zakończone → pojedyncze odblokowanie DLC na jedno `run_id` (max trzy dodatki).
9. Test na Androidzie: gesty i reakcje sceniczne odpowiadają tej samej macierzy, nie tylko testowi Python.

Zobacz `reference/test_MAN_OF_THE_YEAR_REFERENCYJNY_SILNIK_NARRACJI.py` — test jednostkowy, NIE E2E gry.
