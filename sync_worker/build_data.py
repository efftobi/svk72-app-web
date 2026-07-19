"""
Erzeugt data.json für die SVK-72-App aus dem DSV-Ergebnisdienst + den
Konfig-Dateien in data/.

Läuft automatisch per GitHub Actions (.github/workflows/update-data.yml).
Sicherheitsnetz: Wenn eine Liga-Seite nicht abrufbar/parsebar ist, bleiben
die bisherigen Daten dieses Teams aus der bestehenden data.json erhalten —
die App zeigt dann einfach den letzten bekannten Stand.

Besonderheiten des DSV-Ergebnisdienstes (dsvdaten.dsv.de), verifiziert am
19.07.2026 per Browser-Sitzung:
- Liga-Seiten (League.aspx) verlangen eine Session: ohne Cookie leitet der
  Server auf die Index-Seite um. Deshalb wärmt der Client zuerst Index.aspx
  an und nutzt denselben Cookie-Jar für alle Liga-Abrufe.
- Der Server drosselt schnelle Klickfolgen ("Rekordtempo"-Seite). Deshalb
  Pausen zwischen den Abrufen. Erkennungsmerkmal: Text "Rekordtempo" bzw.
  keine <table> im HTML -> wie Fehler behandeln (alte Daten behalten).
- Ein Team kann mehrere Quellen haben (Liga + DM-Runden): "urls"-Liste in
  data/teams.json. Spiele werden zusammengeführt, die Tabelle kommt aus der
  ersten URL, die eine liefert (= Liga).
- Liga-Seiten enthalten ALLE Spiele der Liga -> es werden nur Spiele mit
  eigener Beteiligung (eigenes_team im Heim- oder Gastnamen) übernommen.

Aufruf:
    python sync_worker/build_data.py             # normal (holt dsvdaten.dsv.de)
    python sync_worker/build_data.py --offline   # Test ohne Netz (Fixture für u14)
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_teamseite  # noqa: E402

ROOT = Path(__file__).parent.parent
UA = "SVK72-Vereins-App Daten-Update (github.com, Kontakt: tobias@fusten.de)"
INDEX_URL = "https://dsvdaten.dsv.de/Modules/WB/Index.aspx"
PAUSE_SEKUNDEN = 5


def lade_json(pfad: Path, default):
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except Exception:
        return default


def venue_key(rohtext: str | None, venues: dict) -> str | None:
    if not rohtext:
        return None
    low = rohtext.lower()
    for key, v in venues.items():
        if key.startswith("_"):
            continue
        for muster in v.get("erkennung", []):
            if muster and muster.lower() in low:
                return key
    return None


def hole_seite(client: httpx.Client | None, url: str, offline: bool) -> str:
    if offline:
        return (Path(__file__).parent / "fixtures" / "team_page.html").read_text(encoding="utf-8")
    r = client.get(url, timeout=30, follow_redirects=True)
    r.raise_for_status()
    if "rekordtempo" in r.text.lower():
        raise RuntimeError("DSV-Drosselung aktiv (Rekordtempo-Seite)")
    return r.text


def hole_team(team: dict, venues: dict, eigenes_team: str,
              client: httpx.Client | None, offline: bool):
    """Liefert (matches, standings) im App-Format oder None bei Fehler."""
    urls = team.get("urls") or ([team["url"]] if team.get("url") else [])
    alle_spiele, standings = [], []

    for nr, url in enumerate(urls):
        if nr > 0 and not offline:
            time.sleep(PAUSE_SEKUNDEN)
        seite = parse_teamseite(hole_seite(client, url, offline))
        alle_spiele.extend(seite.spiele)
        if not standings and seite.tabelle:
            # Eigene Zeile anhand des Team-eigenen Namens markieren (nicht über den
            # globalen Parser-Fallback — wichtig wegen SG mit Uerdinger SV 08)
            standings = [
                [z.platz, z.mannschaft, z.spiele, z.siege, z.unentschieden,
                 z.niederlagen, f"{z.tore}:{z.gegentore}", z.punkte]
                + ([True] if eigenes_team.lower() in z.mannschaft.lower() else [])
                for z in seite.tabelle
            ]
        if offline:
            break  # Fixture deckt nur eine Seite ab

    # Nur Spiele mit eigener Beteiligung (Liga-Seiten listen die ganze Liga)
    eigene = [s for s in alle_spiele
              if eigenes_team.lower() in s.heim.lower() or eigenes_team.lower() in s.gast.lower()]
    eigene.sort(key=lambda s: s.datum)

    if not eigene and not standings:
        return None  # nichts erkannt -> alte Daten behalten

    matches = []
    for s in eigene:
        m = {
            "d": s.datum.isoformat(),
            "heim": s.heim,
            "gast": s.gast,
            "h": eigenes_team.lower() in s.heim.lower(),
        }
        if s.anpfiff:
            m["zeit"] = s.anpfiff.strftime("%H:%M")
        if s.gespielt:
            m["th"], m["tg"] = s.tore_heim, s.tore_gast
        vk = venue_key(s.venue_rohtext, venues)
        if vk:
            m["ort"] = vk
        matches.append(m)

    return matches, standings


def main() -> None:
    offline = "--offline" in sys.argv

    teams_datei = lade_json(ROOT / "data" / "teams.json", {"teams": []})
    teams_cfg = teams_datei["teams"]
    trainings = {k: v for k, v in lade_json(ROOT / "data" / "trainings.json", {}).items() if not k.startswith("_")}
    venues_cfg = lade_json(ROOT / "data" / "venues.json", {})
    venues = {k: {kk: vv for kk, vv in v.items() if kk != "erkennung"}
              for k, v in venues_cfg.items() if not k.startswith("_")}

    alt = lade_json(ROOT / "data.json", {})
    alt_matches = alt.get("matches", {})
    alt_standings = alt.get("standings", {})

    client = None
    if not offline:
        client = httpx.Client(headers={"User-Agent": UA}, follow_redirects=True)
        try:  # Session anwärmen (League.aspx verlangt Cookie, sonst Redirect zur Index-Seite)
            client.get(INDEX_URL, timeout=30)
            time.sleep(PAUSE_SEKUNDEN)
        except Exception:
            pass

    out_teams, out_matches, out_standings = [], {}, {}
    fehler = []

    for t in teams_cfg:
        eintrag = {k: t[k] for k in ("id", "badge", "name", "liga") if k in t}
        if t.get("jugend"):
            eintrag["jugend"] = True
        eigenes_team = t.get("eigenes_team") or teams_datei.get("eigenes_team", "Krefeld")

        if t.get("url") or t.get("urls"):
            try:
                ergebnis = None if offline and t["id"] != "u14" else \
                    hole_team(t, venues_cfg, eigenes_team, client, offline)
            except Exception as e:
                ergebnis = None
                fehler.append(f"{t['id']}: {e}")
            if ergebnis:
                out_matches[t["id"]], out_standings[t["id"]] = ergebnis
                eintrag["live"] = True
            elif t["id"] in alt_matches:  # Sicherheitsnetz: alten Stand behalten
                out_matches[t["id"]] = alt_matches[t["id"]]
                out_standings[t["id"]] = alt_standings.get(t["id"], [])
                eintrag["live"] = True
                fehler.append(f"{t['id']}: alte Daten beibehalten")
        elif t["id"] in alt_matches:  # Teams ohne URL: gepflegte/Seed-Daten durchreichen
            out_matches[t["id"]] = alt_matches[t["id"]]
            out_standings[t["id"]] = alt_standings.get(t["id"], [])
            eintrag["live"] = True
        out_teams.append(eintrag)

    if client is not None:
        client.close()

    berlin = timezone(timedelta(hours=2))  # Sommerzeit; Winter: +1 (nur Anzeige-Stempel)
    data = {
        "teams": out_teams,
        "matches": out_matches,
        "standings": out_standings,
        "trainings": trainings,
        "venues": venues,
        "stand": datetime.now(berlin).strftime("%d.%m.%Y %H:%M"),
    }
    (ROOT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"data.json geschrieben: {len(out_matches)} Teams mit Daten, "
          f"{sum(len(m) for m in out_matches.values())} Spiele")
    for f in fehler:
        print(f"  ⚠ {f}", file=sys.stderr)
    # Fehler führen NICHT zu Exit 1 — alte Daten bleiben ja erhalten.


if __name__ == "__main__":
    main()
