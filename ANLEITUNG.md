# SVK 72 Wasserball Web-App — in 10 Minuten auf deinem iPhone

Die App in diesem Ordner ist eine fertige PWA (Progressive Web App) nach dem
Muster der CHTC-App. Damit sie aufs iPhone kommt, muss sie einmal ins
Internet (kostenlos), danach installierst du sie in Safari mit zwei Tipps.

## Schritt 1: Veröffentlichen (einmalig, kostenlos)

**GitHub Pages (empfohlen, wie bei der CHTC-App):**
1. Auf github.com ein neues Repository anlegen, z. B. `svk72-app-web` (public).
2. Alle Dateien aus diesem Ordner hochladen (Drag & Drop im Browser:
   „Add file → Upload files"). Wichtig: auch die Ordner `data`, `sync_worker`
   und `.github` — falls sich `.github` nicht ziehen lässt: „Add file →
   Create new file", als Namen `.github/workflows/update-data.yml` eintippen
   und den Inhalt hineinkopieren (dito für `debug.yml`).
   (Das war beim CHTC der Stolperstein Nr. 1.)
3. Im Repo: **Settings → Pages** → unter „Branch" `main` und `/ (root)` wählen → Save.
4. Nach 1–2 Minuten ist die App erreichbar unter:
   `https://DEIN-GITHUB-NAME.github.io/svk72-app-web/`

## Schritt 2: Auf dem iPhone installieren

1. Die URL in **Safari** öffnen (wichtig: Safari, nicht Chrome).
2. Teilen-Symbol (Quadrat mit Pfeil) → **„Zum Home-Bildschirm"** → Hinzufügen.
3. Auf dem Home-Bildschirm liegt jetzt „SVK 72" mit eigenem Icon — startet
   im Vollbild wie eine normale App und funktioniert dank Offline-Cache
   auch bei schlechtem Empfang am Beckenrand.

Den Link kannst du an alle Eltern/Spieler der U14 weitergeben.

## Was die App aktuell kann

- **U14** (Pilot-Team, wie die wU12 beim CHTC) mit der **kompletten echten
  Saison 2025/26 vom DSV-Ergebnisdienst**: alle 10 Ligaspiele der U14 NRW
  Gruppe A samt Tabelle (Platz 3) und alle 9 DM-Spiele — Vorrunde in
  Berlin, Zwischenrunden-Heimturnier in Krefeld und die Endrunde in
  Düsseldorf mit **Platz 8 der Deutschen Meisterschaft**. Inkl.
  Spiel-Details, Karten-Link und „In Kalender"-Funktion.
- **U14 · 2** mit allen 12 Spielen der U14 NRW Gruppe B samt Tabelle
  (Platz 3, dank direktem Vergleich vor dem ASC Duisburg II).
- Favoriten (Stern) werden auf dem Gerät gespeichert.
- Übrige Teams (U10–U18, 1.–3. Herren) sind angelegt; ihre Spieldaten
  kommen, sobald die Liga-URLs der Saison 2026/27 eingetragen sind.
- Trainingszeiten: bitte in `data/trainings.json` eintragen (Vorlage liegt
  drin) — direkt auf GitHub editierbar.

## Eigenes Logo

Aktuell nutzt die App ein von Claude gestaltetes SVK-Wappen (Blau/Gelb mit
Wasserball). Sobald du das Original-Vereinslogo hast (z. B. im Logos-Ordner
wie beim CHTC), tauscht Claude die Icons aus.

## Automatischer Betrieb

Wie die App im laufenden Betrieb aktuell bleibt (automatisches Daten-Update
vom DSV-Ergebnisdienst über GitHub Actions), steht in **BETRIEB.md** —
inklusive des wichtigen ersten Diagnose-Laufs.
