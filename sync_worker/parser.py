"""
Parser für Liga-Seiten des DSV-Ergebnisdienstes Wasserball (dsvdaten.dsv.de).

Zwei Strategien:
1. "DSV-Tabellen-Strategie" (primär): Der Ergebnisdienst ist eine klassische
   ASP.NET-Seite, die Spielplan und Tabelle als HTML-<table> ausliefert.
   Spieltabellen werden an ihren Spaltenköpfen erkannt (Heim/Gast bzw.
   Heimmannschaft/Gastmannschaft), die Tabelle an Mannschaft + Punkte.
   Die Spaltenpositionen werden dynamisch aus dem Header ermittelt.
   WICHTIG: Die genaue Struktur wird nach dem ersten Diagnose-Lauf
   (debug.yml -> debug.txt) verifiziert und bei Bedarf nachjustiert —
   gleiches Vorgehen wie beim CHTC-Parser (dort war es v2, der saß).
2. Generische Fallback-Strategie: erkennt Spiele über Datums-Muster und
   Tabellen über Spaltenköpfe — falls der Ergebnisdienst anders aufgebaut
   ist oder sein Layout ändert.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, time

from bs4 import BeautifulSoup

EIGENES_TEAM = "Krefeld"  # Fallback-Erkennung; wegen der Spielgemeinschaft mit dem
# Uerdinger SV 08 setzt build_data.py die Markierung je Team selbst (eigenes_team).

MONATE = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4, "mai": 5, "juni": 6,
    "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}

RE_DATUM_NUM = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b")
RE_DATUM_TXT = re.compile(r"\b(\d{1,2})\.\s*([A-Za-zäöüÄÖÜ]+)\s*(\d{4})\b")
RE_UHRZEIT = re.compile(r"\b(\d{1,2})[:.](\d{2})\s*(?:Uhr)?\b")
RE_ERGEBNIS = re.compile(r"(?<!\d)(\d{1,2})\s*:\s*(\d{1,2})(?!\d)")


@dataclass
class Spiel:
    datum: date
    anpfiff: time | None
    heim: str
    gast: str
    tore_heim: int | None
    tore_gast: int | None
    venue_rohtext: str | None = None
    viertel: list | None = None   # ["2:4", "2:4", "3:0", "5:3"]
    ew: str | None = None         # Entscheidungswerfen-Abschnitt, z. B. "4:2"

    @property
    def gespielt(self) -> bool:
        return self.tore_heim is not None


@dataclass
class TabellenZeile:
    platz: int
    mannschaft: str
    spiele: int
    siege: int
    unentschieden: int
    niederlagen: int
    tore: int
    gegentore: int
    punkte: int
    ist_eigenes_team: bool = False


@dataclass
class TeamSeite:
    spiele: list[Spiel] = field(default_factory=list)
    tabelle: list[TabellenZeile] = field(default_factory=list)


# ----------------------------------------------------------------- Helpers
def parse_datum(text: str) -> date | None:
    m = RE_DATUM_NUM.search(text)
    if m:
        d, mo, y = (int(x) for x in m.groups())
        if y < 100:
            y += 2000
        if 1 <= mo <= 12 and 1 <= d <= 31:
            try:
                return date(y, mo, d)
            except ValueError:
                return None
    m = RE_DATUM_TXT.search(text)
    if m:
        d, name, y = m.group(1), m.group(2).lower(), m.group(3)
        if name in MONATE:
            return date(int(y), MONATE[name], int(d))
    return None


def parse_uhrzeit(text: str) -> time | None:
    m = RE_UHRZEIT.search(text)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    return time(h, mi) if h < 24 and mi < 60 else None


def _zahl(s: str) -> int:
    m = re.search(r"-?\d+", s)
    return int(m.group()) if m else 0


def _saubere_mannschaft(t: str) -> str | None:
    t = re.sub(r"\s+", " ", t or "").strip()
    # Zusätze abschneiden: "... - dir. Vergleich: ..." / "... - eig. Tabelle: ..."
    t = re.split(r"\s+-\s+(?:dir\.|eig\.)", t)[0].strip()
    return t or None


# ----------------------------------------------------- Strategie 1: DSV-Tabellen
def _header_von(table) -> list[str]:
    """Spaltenköpfe: bevorzugt <th>, sonst die erste Zeile.
    Normalisierung: klein, Fußnoten-Sternchen und Punkte entfernen
    (DSV-Tabelle: 'S*', 'U*', 'N*', 'TD*', 'Pkt.')."""
    def norm(el):
        return el.get_text(" ", strip=True).lower().rstrip(".*")
    ths = table.find_all("th")
    if ths:
        return [norm(th) for th in ths]
    erste = table.find("tr")
    if erste:
        return [norm(td) for td in erste.find_all("td")]
    return []


def _spalte(header: list[str], *namen: str) -> int | None:
    """Index der passenden Header-Spalte: erst exakter Treffer, dann
    Teilstring — Kurznamen (1–2 Zeichen wie 's', 'u', 'n') nur exakt,
    sonst würde 's' z. B. schon auf 'mannschaft' passen."""
    for n in namen:
        for i, h in enumerate(header):
            if h == n:
                return i
    for n in namen:
        if len(n) < 3:
            continue
        for i, h in enumerate(header):
            if n in h:
                return i
    return None


def parse_spiele_dsv(soup: BeautifulSoup) -> list[Spiel]:
    spiele: list[Spiel] = []
    gesehen: set[tuple] = set()

    for table in soup.find_all("table"):
        header = _header_von(table)
        i_heim = _spalte(header, "heim")
        i_gast = _spalte(header, "gast")
        if i_heim is None or i_gast is None:
            continue  # keine Spieltabelle

        i_datum = _spalte(header, "datum", "tag")
        i_zeit = _spalte(header, "zeit", "beginn", "anwurf")
        i_erg = _spalte(header, "ergebnis", "resultat", "erg")
        i_ort = _spalte(header, "bad", "halle", "ort", "austragung", "schwimm")

        aktuelles_datum: date | None = None
        zeilen = table.find_all("tr")
        for tr in zeilen:
            tds = tr.find_all("td")
            if not tds:
                continue
            texte = [td.get_text(" ", strip=True) for td in tds]
            zeilentext = " ".join(texte)

            # Datum: eigene Spalte, sonst irgendwo in der Zeile; leere Zelle -> Datum
            # der vorigen Zeile gilt weiter (Turnier-Layout mit Datums-Zwischenzeile).
            d = None
            if i_datum is not None and i_datum < len(texte):
                d = parse_datum(texte[i_datum])
            if d is None:
                d = parse_datum(zeilentext)
            if d is not None:
                aktuelles_datum = d
            if aktuelles_datum is None:
                continue

            if i_heim >= len(texte) or i_gast >= len(texte):
                continue
            heim = _saubere_mannschaft(texte[i_heim])
            gast = _saubere_mannschaft(texte[i_gast])
            if not heim or not gast or heim == gast:
                continue
            # Kopfzeilen, die als <td> daherkommen, überspringen
            if heim.lower().startswith("heim") or gast.lower().startswith("gast"):
                continue

            th = tg = None
            viertel = ew = None
            if i_erg is not None and i_erg < len(texte):
                erg_text = texte[i_erg]
                m = RE_ERGEBNIS.search(erg_text)  # erster Treffer = Endstand (Viertel dahinter)
                if m:
                    th, tg = int(m.group(1)), int(m.group(2))
                # Viertelergebnisse aus der Klammer: "12:11 (2:4, 2:4, 3:0, 5:3)";
                # bei "n.EW" ist der 5. Abschnitt das Entscheidungswerfen.
                klammer = re.search(r"\(([^)]*)\)", erg_text)
                if klammer:
                    seg = [f"{a}:{b}" for a, b in RE_ERGEBNIS.findall(klammer.group(1))]
                    if len(seg) >= 4:
                        viertel = seg[:4]
                        if len(seg) >= 5 and "n.EW" in erg_text:
                            ew = seg[4]

            anpfiff = None
            if i_zeit is not None and i_zeit < len(texte):
                # DSV-Spalte "Beginn" enthält Datum UND Zeit ("15.11.25, 19:15 Uhr")
                # -> Datum erst entfernen, sonst würde "15.11" als Uhrzeit gelesen
                anpfiff = parse_uhrzeit(RE_DATUM_NUM.sub(" ", texte[i_zeit]))
            if anpfiff is None and th is None:
                # geplantes Spiel: Zeit steht evtl. woanders in der Zeile
                ohne_datum = RE_DATUM_NUM.sub(" ", zeilentext)
                anpfiff = parse_uhrzeit(ohne_datum)

            venue = texte[i_ort] if (i_ort is not None and i_ort < len(texte) and texte[i_ort]) else None

            key = (aktuelles_datum, heim.lower(), gast.lower())
            if key in gesehen:
                continue
            gesehen.add(key)
            spiele.append(Spiel(aktuelles_datum, anpfiff, heim, gast, th, tg, venue,
                                viertel=viertel, ew=ew))

    spiele.sort(key=lambda s: s.datum)
    return spiele


def parse_tabelle_dsv(soup: BeautifulSoup) -> list[TabellenZeile]:
    for table in soup.find_all("table"):
        header = _header_von(table)
        if not header:
            continue
        hat_punkte = any(("pkt" in h or "punkte" in h) for h in header)
        i_name = _spalte(header, "mannschaft", "team", "verein")
        if not hat_punkte or i_name is None:
            continue
        # Spieltabellen (Heim/Gast) ausschließen
        if _spalte(header, "heim") is not None and _spalte(header, "gast") is not None:
            continue

        i_platz = _spalte(header, "platz", "rang", "#") or 0
        i_sp = _spalte(header, "spiele", "sp")
        i_s = _spalte(header, "siege", "s")
        i_u = _spalte(header, "unentschieden", "u")
        i_n = _spalte(header, "niederlagen", "n")
        i_tore = _spalte(header, "tore")
        i_pkt = _spalte(header, "pkt", "punkte")

        zeilen: list[TabellenZeile] = []
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 4:
                continue
            texte = [td.get_text(" ", strip=True) for td in tds]
            if i_name >= len(texte):
                continue
            name = _saubere_mannschaft(texte[i_name])
            platz = _zahl(texte[i_platz]) if i_platz < len(texte) else 0
            if not name or platz <= 0 or name.lower() in ("mannschaft", "team", "verein"):
                continue

            def wert(i):
                return _zahl(texte[i]) if (i is not None and i < len(texte)) else 0

            tore = gegen = 0
            if i_tore is not None and i_tore < len(texte):
                tm = re.search(r"(\d+)\s*:\s*(\d+)", texte[i_tore])
                if tm:
                    tore, gegen = int(tm.group(1)), int(tm.group(2))
                else:
                    tore = _zahl(texte[i_tore])

            zeilen.append(TabellenZeile(
                platz=platz, mannschaft=name,
                spiele=wert(i_sp), siege=wert(i_s),
                unentschieden=wert(i_u), niederlagen=wert(i_n),
                tore=tore, gegentore=gegen, punkte=wert(i_pkt),
                ist_eigenes_team=EIGENES_TEAM.lower() in name.lower(),
            ))
        if len(zeilen) >= 3:
            return zeilen
    return []


# ----------------------------------------------------------------- Strategie 2: Fallback
def parse_spiele_generisch(soup: BeautifulSoup) -> list[Spiel]:
    spiele: list[Spiel] = []
    gesehen: set[tuple] = set()

    for el in soup.find_all(["tr", "li", "div", "article"]):
        text = el.get_text(" ", strip=True)
        if len(text) > 400 or EIGENES_TEAM.lower() not in text.lower():
            continue
        datum = parse_datum(text)
        if datum is None:
            continue
        if any(parse_datum(c.get_text(" ", strip=True) or "") and
               EIGENES_TEAM.lower() in (c.get_text(" ", strip=True) or "").lower()
               for c in el.find_all(["tr", "li", "div", "article"])):
            continue

        kandidaten = [c.get_text(" ", strip=True)
                      for c in el.find_all(class_=re.compile(r"(team|club|home|away|heim|gast)", re.I))]
        kandidaten = [k for k in kandidaten if 2 < len(k) < 60]
        rest = RE_UHRZEIT.sub(" ", RE_DATUM_TXT.sub(" ", RE_DATUM_NUM.sub(" ", text)))
        if len(kandidaten) >= 2:
            heim, gast = kandidaten[0], kandidaten[1]
        else:
            m = re.search(r"([A-ZÄÖÜ][^–\-:]{2,50})\s*[–\-]\s*([A-ZÄÖÜ][^–\-:]{2,50})", rest)
            if not m:
                continue
            heim, gast = m.group(1).strip(), m.group(2).strip()

        erg = RE_ERGEBNIS.search(rest)
        th, tg = (int(erg.group(1)), int(erg.group(2))) if erg else (None, None)

        v = el.find(class_=re.compile(r"(venue|ort|location|bad|halle)", re.I))
        venue = v.get_text(" ", strip=True) if v else None

        key = (datum, heim.lower(), gast.lower())
        if key in gesehen:
            continue
        gesehen.add(key)
        spiele.append(Spiel(datum, parse_uhrzeit(text), heim, gast, th, tg, venue))

    spiele.sort(key=lambda s: s.datum)
    return spiele


def parse_tabelle_generisch(soup: BeautifulSoup) -> list[TabellenZeile]:
    for table in soup.find_all("table"):
        header_text = " ".join(th.get_text(" ", strip=True).lower() for th in table.find_all("th"))
        if "mannschaft" not in header_text or ("punkte" not in header_text and "pkt" not in header_text):
            continue
        zeilen: list[TabellenZeile] = []
        for tr in table.find_all("tr"):
            tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if len(tds) < 6:
                continue
            try:
                platz, mannschaft = _zahl(tds[0]), tds[1]
                sp, s, u, n = (_zahl(x) for x in tds[2:6])
                tm = re.search(r"(\d+)\s*:\s*(\d+)", tds[6] if len(tds) > 6 else "")
                tore, gegen = (int(tm.group(1)), int(tm.group(2))) if tm else (0, 0)
                punkte = _zahl(tds[7]) if len(tds) > 7 else _zahl(tds[-1])
            except (ValueError, IndexError):
                continue
            if platz <= 0 or not mannschaft:
                continue
            zeilen.append(TabellenZeile(platz, mannschaft, sp, s, u, n, tore, gegen, punkte,
                                        ist_eigenes_team=EIGENES_TEAM.lower() in mannschaft.lower()))
        if len(zeilen) >= 3:
            return zeilen
    return []


# ----------------------------------------------------------------- Einstieg
def parse_teamseite(html: str) -> TeamSeite:
    soup = BeautifulSoup(html, "html.parser")
    spiele = parse_spiele_dsv(soup) or parse_spiele_generisch(soup)
    tabelle = parse_tabelle_dsv(soup) or parse_tabelle_generisch(soup)
    return TeamSeite(spiele=spiele, tabelle=tabelle)
