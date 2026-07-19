"""
Diagnose-Lauf: holt die konfigurierte DSV-Liga-Seite (U14) und schreibt die
Seitenstruktur nach debug.txt — damit der Parser bei Bedarf exakt auf die
echte Struktur des Ergebnisdienstes eingestellt werden kann.
(Gleiches Vorgehen wie beim CHTC: erster Lauf -> debug.txt -> Parser v2.)

Lesen: debug.txt im Repo bzw. über
https://raw.githubusercontent.com/<user>/svk72-app-web/main/debug.txt?v=1
(?v=N hochzählen, um den Cache zu umgehen.)
"""
import json
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent.parent
teams = json.loads((ROOT / "data" / "teams.json").read_text(encoding="utf-8"))["teams"]
URL = next((t["url"] for t in teams if t.get("url")), None)

out = []
if not URL:
    out.append("KEINE URL in data/teams.json konfiguriert!")
else:
    out.append(f"URL: {URL}")
    try:
        r = httpx.get(URL, headers={"User-Agent": "SVK72-Vereins-App Diagnose (Kontakt: tobias@fusten.de)"},
                      timeout=30, follow_redirects=True)
        out.append(f"STATUS {r.status_code} LAENGE {len(r.text)} FINALE-URL {r.url}")
        soup = BeautifulSoup(r.text, "html.parser")

        out.append(f"TITEL: {soup.title.get_text(strip=True) if soup.title else '-'}")

        tables = soup.find_all("table")
        out.append(f"ANZAHL TABELLEN: {len(tables)}")
        for nr, table in enumerate(tables):
            ths = [th.get_text(' ', strip=True) for th in table.find_all("th")]
            trs = table.find_all("tr")
            out.append(f"--- TABELLE {nr}: {len(trs)} Zeilen, Header: {ths}")
            for tr in trs[:6]:
                tds = [td.get_text(' ', strip=True)[:40] for td in tr.find_all("td")]
                if tds:
                    out.append(f"    ZEILE: {tds}")

        # Auffällige Klassen/IDs (ASP.NET: ContentPlaceholder, GridView etc.)
        namen = set()
        for el in soup.find_all(True):
            for attr in ("class", "id"):
                v = el.get(attr)
                werte = v if isinstance(v, list) else ([v] if v else [])
                for w in werte:
                    if re.search(r"(spiel|game|match|tab|stand|league|liga|grid|schedule)", str(w), re.I):
                        namen.add(str(w))
        out.append("KLASSEN/IDs: " + " | ".join(sorted(namen)[:60]))

        # Formulare/Links (falls Saison/Gruppe per Auswahl gewechselt wird)
        for form in soup.find_all("form")[:3]:
            selects = [s.get("name") or s.get("id") for s in form.find_all("select")]
            out.append(f"FORMULAR: action={form.get('action')} selects={selects}")
        links = [a.get("href") for a in soup.find_all("a", href=True)
                 if re.search(r"(League|Season|Group|Liga)", a["href"], re.I)][:20]
        out.append("LINKS: " + " | ".join(links))
    except Exception as e:
        out.append(f"FEHLER: {type(e).__name__}: {e}")

Path("debug.txt").write_text("\n".join(out), encoding="utf-8")
print("debug.txt geschrieben")
