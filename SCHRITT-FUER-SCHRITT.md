# SVK-72-App: Schritt für Schritt zu GitHub — und danach

Diese Anleitung führt einmal komplett durch: Veröffentlichen, aufs iPhone,
Automatik einschalten, laufender Betrieb. Zeitbedarf: ca. 15 Minuten.
(Alles wie bei der CHTC-App — inklusive der bekannten Stolpersteine.)

---

## Teil 1: ZIP entpacken (2 Min.)

1. Im Ordner `Dokumente → Claude → Projects → Apps → SVK App` liegt
   `svk72-app-web.zip`.
2. Rechtsklick auf die ZIP → **„Alle extrahieren…"** → Extrahieren.
3. Es entsteht ein Ordner `svk72-app-web` mit allen App-Dateien.
   **Wichtig:** Darin liegt auch der versteckte Ordner `.github` — falls du
   ihn nicht siehst: im Explorer oben **Anzeigen → Einblenden →
   „Ausgeblendete Elemente"** anhaken.

## Teil 2: Repository auf GitHub anlegen (3 Min.)

1. Auf **github.com** einloggen (dein Account: efftobi).
2. Oben rechts **„+" → „New repository"**.
3. Repository name: **`svk72-app-web`** · Sichtbarkeit: **Public** ·
   sonst nichts anhaken → **„Create repository"**.

## Teil 3: Dateien hochladen (5 Min.)

1. Im neuen (leeren) Repo auf den Link **„uploading an existing file"**
   klicken (bzw. „Add file → Upload files").
2. Im Explorer den entpackten Ordner öffnen, **alles markieren (Strg+A)**
   und ins Browserfenster ziehen — auch die Ordner `data`, `sync_worker`
   und `.github`.
3. Unten auf den grünen Button **„Commit changes"**.
4. **Kontrolle (wichtig, CHTC-Stolperstein!):** Im Repo müssen jetzt zu
   sehen sein: `index.html`, `data.json`, Ordner `data`, `sync_worker`
   und `.github`. Fehlt `.github`:
   - „Add file → **Create new file**"
   - als Dateiname eintippen: `.github/workflows/update-data.yml`
     (die Schrägstriche erzeugen die Ordner automatisch)
   - Inhalt der gleichnamigen Datei aus dem entpackten Ordner
     (mit Editor/Notepad öffnen) hineinkopieren → Commit.
   - Das Gleiche für `.github/workflows/debug.yml`.

## Teil 4: GitHub Pages einschalten (2 Min.)

1. Im Repo: **Settings** (Zahnrad-Reiter) → links **Pages**.
2. Bei „Branch": **`main`** und **`/ (root)`** auswählen → **Save**.
3. 1–2 Minuten warten. Die App ist dann erreichbar unter:
   **`https://efftobi.github.io/svk72-app-web/`**
   (Die URL steht oben auf der Pages-Seite; ggf. Seite neu laden.)

## Teil 5: Aufs iPhone (2 Min.)

1. Die URL in **Safari** öffnen (wichtig: Safari, nicht Chrome).
2. Teilen-Symbol (Quadrat mit Pfeil) → **„Zum Home-Bildschirm"** →
   Hinzufügen.
3. Fertig: „SVK 72" liegt mit dem Vereinswappen auf dem Home-Bildschirm,
   startet im Vollbild und funktioniert dank Offline-Cache auch bei
   schlechtem Empfang am Beckenrand.
4. Den Link kannst du jetzt an Eltern und Spieler der U14 weitergeben —
   die installieren ihn genauso.

## Teil 6: Automatik testen (3 Min.)

1. Im Repo den Reiter **Actions** öffnen. Falls ein Hinweis kommt:
   „I understand my workflows, enable them" bestätigen.
2. Links **„Daten-Update vom DSV-Ergebnisdienst"** anklicken → rechts
   **„Run workflow"** → grüner Button. Das ist ein manueller Testlauf.
3. Nach ca. 1–2 Minuten: grüner Haken ✓ = alles gut. Im Repo erscheint
   dann ggf. ein Commit „Daten-Update …" vom `svk72-daten-bot`.
4. **Das Ergebnis bitte an Claude melden** (grüner Haken oder rotes ✗ und
   was im Log steht). Hintergrund: Der Parser ist auf die echten
   DSV-Seiten eingestellt, aber der allererste Lauf aus GitHub heraus ist
   die Feuerprobe (Session/Drosselung des DSV-Servers). Schlägt er fehl,
   zeigt die App einfach weiter die eingebauten Saisondaten — es geht
   also nichts kaputt.

---

## Und danach? Der laufende Betrieb

**Automatisch:** Der Zeitplan läuft tagsüber alle 2 Stunden, am Wochenende
alle 20 Minuten. Neue Ergebnisse landen von selbst in der App — niemand
muss etwas installieren oder aktualisieren.

**Trainingszeiten eintragen (wenn du sie hast):** Im Repo
`data/trainings.json` anklicken → Stift-Symbol → nach der Vorlage in der
Datei ausfüllen → „Commit changes". Beim nächsten Daten-Lauf (oder sofort
über Actions → „Run workflow") steht es in der App.

**Bäder-Adressen verfeinern:** `data/venues.json` genauso per Stift
bearbeiten — aktuell stehen dort Städte-Platzhalter; echte Bad-Namen und
Adressen machen die „Route öffnen"-Funktion besser.

**Saisonstart 2026/27 (ca. September):** Die neuen Liga-URLs in
`data/teams.json` eintragen. Wo man sie findet und was zu tun ist, steht
in **BETRIEB.md** — oder einfach Claude machen lassen: kurz melden, sobald
die Saison auf dsvdaten.dsv.de sichtbar ist.

**Wenn etwas klemmt:** Actions-Reiter → roten Lauf anklicken → Log
kopieren und an Claude geben. Notfalls Workflow „Diagnose DSV" starten —
der schreibt `debug.txt` ins Repo, damit Claude die Seitenstruktur sieht.

**Noch offen / empfohlen:**
- Beim DSV bzw. Schwimmverband NRW kurz anfragen, ob die automatisierte
  Nutzung der Ergebnisdaten für die Vereins-App okay ist.
- Weitere Teams (U16, U18, Herren …) können jederzeit dazukommen — es
  fehlen nur die Liga-URLs in `data/teams.json`.
- GitHub pausiert Zeitpläne nach ~60 Tagen ohne Aktivität (z. B. über die
  Sommerpause): dann im Actions-Reiter auf „Enable" klicken.
