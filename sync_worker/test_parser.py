from datetime import date, time
from pathlib import Path

from parser import parse_teamseite

HTML = (Path(__file__).parent / "fixtures" / "team_page.html").read_text(encoding="utf-8")


def test_spiele_werden_erkannt():
    seite = parse_teamseite(HTML)
    # Wertungs-Spiel ohne Datum (Zeile 626) wird übersprungen -> 4 Spiele
    assert len(seite.spiele) == 4

    s1 = seite.spiele[0]
    assert s1.datum == date(2025, 11, 15)
    assert s1.heim == "ASC Duisburg"
    assert s1.gast == "SV Krefeld 1972"
    assert (s1.tore_heim, s1.tore_gast) == (9, 6)   # Endstand, nicht die Viertel
    assert s1.anpfiff == time(17, 45)               # nicht "15:11" aus dem Datum!
    assert s1.venue_rohtext == "Duisburg"


def test_ergebnis_nach_entscheidungswerfen():
    seite = parse_teamseite(HTML)
    s = next(x for x in seite.spiele if x.datum == date(2025, 12, 2))
    assert (s.tore_heim, s.tore_gast) == (14, 12)   # "14:12 n.EW (...)"


def test_heimsieg():
    seite = parse_teamseite(HTML)
    s = next(x for x in seite.spiele if x.datum == date(2026, 2, 8))
    assert s.heim == "SV Krefeld 1972"
    assert (s.tore_heim, s.tore_gast) == (12, 11)


def test_geplantes_spiel_ohne_ergebnis_mit_uhrzeit():
    seite = parse_teamseite(HTML)
    s = next(x for x in seite.spiele if x.datum == date(2026, 9, 15))
    assert s.tore_heim is None and s.tore_gast is None
    assert s.anpfiff == time(18, 0)
    assert not s.gespielt
    assert s.venue_rohtext == "Krefeld-Uerdingen"


def test_tabelle():
    seite = parse_teamseite(HTML)
    assert len(seite.tabelle) == 6
    dritte = seite.tabelle[2]
    assert dritte.platz == 3
    assert dritte.mannschaft == "SV Krefeld 1972"   # "dir. Vergleich"-Zusatz entfernt
    assert dritte.ist_eigenes_team
    assert (dritte.spiele, dritte.siege, dritte.punkte) == (10, 5, 15)
    assert (dritte.tore, dritte.gegentore) == (103, 102)
    erste = seite.tabelle[0]
    assert erste.mannschaft == "ASC Duisburg"
    assert (erste.siege, erste.unentschieden, erste.niederlagen) == (9, 0, 1)
    assert not erste.ist_eigenes_team
