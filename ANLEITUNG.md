from datetime import date, time
from pathlib import Path

from parser import parse_teamseite

HTML = (Path(__file__).parent / "fixtures" / "team_page.html").read_text(encoding="utf-8")


def test_spiele_werden_erkannt():
    seite = parse_teamseite(HTML)
    assert len(seite.spiele) == 4

    s1 = seite.spiele[0]
    assert s1.datum == date(2026, 11, 15)
    assert s1.heim == "SV Krefeld 72"
    assert s1.gast == "SV Blau-Weiß Bochum"
    assert (s1.tore_heim, s1.tore_gast) == (12, 9)   # Endstand, nicht die Viertel
    assert "Palmstraße" in s1.venue_rohtext


def test_leere_datumszelle_uebernimmt_voriges_datum():
    seite = parse_teamseite(HTML)
    s = next(x for x in seite.spiele if x.heim == "Duisburger SV 98")
    assert s.datum == date(2026, 11, 15)             # Turniertag: Datum gilt weiter
    assert (s.tore_heim, s.tore_gast) == (7, 15)     # SVK gewinnt auswärts


def test_unentschieden():
    seite = parse_teamseite(HTML)
    s = next(x for x in seite.spiele if x.datum == date(2026, 12, 13))
    assert (s.tore_heim, s.tore_gast) == (10, 10)


def test_geplantes_spiel_ohne_ergebnis_mit_uhrzeit():
    seite = parse_teamseite(HTML)
    s = next(x for x in seite.spiele if x.datum == date(2027, 1, 17))
    assert s.tore_heim is None and s.tore_gast is None
    assert s.anpfiff == time(15, 15)
    assert not s.gespielt


def test_tabelle():
    seite = parse_teamseite(HTML)
    assert len(seite.tabelle) == 5
    erste = seite.tabelle[0]
    assert erste.platz == 1
    assert erste.mannschaft == "SV Krefeld 72"
    assert erste.ist_eigenes_team
    assert (erste.spiele, erste.siege, erste.punkte) == (3, 2, 5)
    assert (erste.tore, erste.gegentore) == (37, 26)
    letzte = seite.tabelle[-1]
    assert letzte.mannschaft == "SG Essen"
    assert not letzte.ist_eigenes_team
