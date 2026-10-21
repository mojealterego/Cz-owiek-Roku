# Godot — źródłowy DEM → rzeczywista geometria terenu 3D

Wprowadzono `godot/scripts/terrain_qa_layer.gd`, ładujący lokalne **jedynie QA** pliki JSON wygenerowane z oficjalnego GeoTIFF. Nie jest to jeszcze włączenie czeskiego ani polskiego terenu do publicznego APK.

## Weryfikacje
- Metryczne sektory 256m, spacing 8/16/32/64m; podział zgodny z importerem Python.
- Trójkąty generowane **tylko** gdy wszystkie cztery wierzchołki mają rzeczywiste wartości. `null` tworzy fizyczną lukę, nie „wypełniony” fragment.
- Oryginalna wysokość w metrach źródłowego datum, bez sztucznego zera, zniekształcenia skali i domyślnego przesunięcia.
- Test ciągłości sąsiadujących sektorów (m.in. brak rozbieżności na granicy i zera przeciw `null`).
- Walidacja nazwy miasta, identyfikatora źródła, SHA-256, datum, prawa do wydania, statusu pionowej rejestracji i odrzucanie niezamierzonych deklaracji ukończenia świata.
- Przed uruchomieniem wymagany jawny `qa_mode_enabled`. W projekcie gry i publicznym eksporcie **nie ustawiono go**.
- W testach Godot fixtures syntetyczne powstają wyłącznie wewnątrz `user://`; nie trafiają do katalogu modeli / eksportu Android.

## Ważne
Czeski DMR5G Bpv nie jest automatycznie kompatybilny z polskim PL-KRON86-NH lub PL-EVRF2007-NH. Nie można łączyć siatki terenu z drogowym OSM 2D ani CityGML jako gotowego miasta, zanim nie ustali się fizycznego poziomu odniesienia i praw do źródłowych danych.

**Status: silnik siatki QA działa po teście CI; rzeczywiste wysokości terenu nie są jeszcze wbudowane w grę.**
