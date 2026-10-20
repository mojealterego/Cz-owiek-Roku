# CZŁOWIEK ROKU / MAN OF THE YEAR

**Android-first cinematic interactive drama · PL/EN · 4 akty · 70 rozdziałów**

Repozytorium produkcyjne adaptacji książki Andrzeja Mikulskiego. Przewidywany styl: interaktywny dramat TPP, decyzje i konsekwencje, fotografia jako mechanika śledcza, filmowe sceny oraz niezmienny kanoniczny finał. Inspiracje jakościowe: *Heavy Rain* i *Detroit: Become Human*. Bez kopiowania cudzego kodu, scen lub assetów.

> **STATUS: BOOTSTRAP / PREPRODUKCJA.** Nie ma skompilowanej gry, modeli 3D, APK/AAB ani zweryfikowanej wydajności Android. Działający artefakt w repozytorium to tylko referencyjny model stanów narracyjnych w Pythonie.

## Zakres źródłowy

| Akt | Nazwa | Rozdziały |
| --- | --- | --- |
| I | PĘKNIĘCIE | 01–14 |
| II | WALKA Z MUREM | 15–41 |
| III | BEZ PRAWA | 42–62 |
| IV | KONIEC ŚWIATŁA | 63–70 |

Książka (409 stron) jest kanonem. Najnowsze decyzje autora mają pierwszeństwo przed dawnymi raportami technicznymi. Wcześniejszy projekt „Chronos” nie jest samodzielną podstawą fabularną. Tekst książki, prywatne nagrania Zuzi i chronione transkrypty **nie są kopiowane do repozytorium publicznego**.

## Dokumentacja i kod

- [Zasady produkcji Android](docs/ANDROID_ARCHITECTURE.md) — technika, sceny, sterowanie, wydajność, testy.
- [Otwarcie i reżyseria CH01](docs/OPENING_AND_CH01.md) — tytuł, prolog, czerwona kurtyna, pierwszy rozdział, wybory.
- [Kanon, źródła i prawa](docs/CANON_AND_MEDIA_POLICY.md) — co można publikować i kiedy.
- [Indeks 70 rozdziałów](data/chapter_index.json) — stabilne identyfikatory, przypisanie do aktu (nie jest pełnym scenariuszem).
- [Referencyjny silnik narracji](reference/MAN_OF_THE_YEAR_REFERENCYJNY_SILNIK_NARRACJI.py) — logika spotkań z Pauliną, CH59 i 3 odblokowań DLC.
- [Testy silnika](reference/test_MAN_OF_THE_YEAR_REFERENCYJNY_SILNIK_NARRACJI.py) — testy 16 wariantów i integralności stanu.

## Uruchomienie sprawdzalnej części

```bash
python -m unittest discover -s reference -p 'test_*.py' -v
```

Testy narracyjne nie są testami Androida. Ich przejście **nie oznacza** ukończenia prototypu graficznego ani wdrożenia gry.

## Najbliższy etap techniczny

1. Prawidłowy projekt silnika na Android i benchmark na konkretnych urządzeniach.
2. Grywalny vertical slice: prolog, gala CH01, aparat, wybory, checkpoint i interfejs dotykowy.
3. Zatwierdzenie modeli postaci i pipeline motion/facial capture.
4. Projekt i implementacja 70 rozdziałów, 280 sekwencji jako zakres *projektowy* (nie gotowe sceny), DLC i galerii.
5. Dowody CI, build Android, testy na sprzęcie, optymalizacja i odbiór.

Nie używaj nazwisk ani nazw osób z prywatnych materiałów jako dowodów zarzutów. Nie publikuj niezweryfikowanych oskarżeń i danych dzieci.
