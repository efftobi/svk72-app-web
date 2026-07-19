# SVK-72-App — Betrieb über GitHub

Die App läuft komplett über dein GitHub-Repository, kostenlos:

- **GitHub Pages** liefert die App aus.
- **GitHub Actions** holt nach Zeitplan die Spieldaten vom
  DSV-Ergebnisdienst (dsvdaten.dsv.de) und schreibt sie in `data.json`.
- Die App lädt bei jedem Öffnen die aktuelle `data.json` — niemand muss
  etwas neu installieren.

## Wichtig: Die Besonderheit gegenüber der CHTC-App

Beim Wasserball kommen die Ligadaten vom **DSV-Ergebnisdienst**
(dsvdaten.dsv.de). Der Parser wurde am 19.07.2026 **gegen die echten
Seiten eingestellt** (per Browser-Sitzung verifiziert): U14 NRW Gruppe A/B
und alle DM-Runden der U14 werden korrekt gelesen. Drei Eigenheiten des
DSV-Systems, die der Daten-Lauf bereits berücksichtigt:

1. **Session-Pflicht:** Liga-Seiten ohne Cookie leiten zur Startseite um —
   der Daten-Lauf ruft deshalb zuerst die Index-Seite auf.
2. **Drosselung:** Bei zu schnellen Abrufen zeigt der Server eine
   „Rekordtempo"-Pausenseite — der Daten-Lauf macht Pausen zwischen den
   Abrufen und behält bei Drosselung einfach die alten Daten.
3. **Saison-URLs:** Die Saison 2025/26 ist beendet; die App zeigt deren
   komplette echte Daten. **Beim Saisonstart 2026/27** die neuen Liga-URLs
   in `data/teams.json` eintragen (Ligenübersicht: Index.aspx → Saisons →
   Saison wählen → Liga anklicken → URL kopieren). Falls der DSV sein
   Layout ändert: Workflow **„Diagnose DSV"** laufen lassen und `debug.txt`
   an Claude geben.

**Fairness/Rechtliches:** Vor dem Dauerbetrieb beim DSV bzw. beim
Schwimmverband NRW kurz anfragen, ob die automatisierte Nutzung der
Ergebnisdaten für eine Vereins-App in Ordnung ist (gleiche Empfehlung wie
beim CHTC gegenüber WHV/DHB). Bis dahin kann die App problemlos mit manuell
gepflegten Daten laufen — siehe unten.

## Einmalig einrichten (nach dem Hochladen dieses Pakets)

1. Alle Dateien/Ordner hochladen (siehe ANLEITUNG.md, Schritt 1).
2. Reiter **Actions** → ggf. „enable" bestätigen.
3. Workflow **„Daten-Update vom DSV-Ergebnisdienst"** → „Run workflow".
   Ergebnis (grüner Haken/rotes ✗ + Log) an Claude melden.

## Wie aktualisiert sich die App?

**Spiele, Ergebnisse, Tabellen — automatisch**, sobald die DSV-Anbindung
steht: tagsüber alle 2 Stunden, am Wochenende (Spieltage) alle 20 Minuten.
Ist der Ergebnisdienst mal nicht erreichbar oder ändert sein Layout, bleibt
einfach der letzte bekannte Stand stehen — die App geht nie kaputt.

**Bis dahin — manuell in 2 Minuten:** Spielpläne/Ergebnisse können direkt
in der Datei `data.json` gepflegt werden (Abschnitt `"matches"` → `"u14"`;
Format ist selbsterklärend: Datum, Heim, Gast, `th`/`tg` = Tore). Auf
GitHub: Datei anklicken → Stift-Symbol → ändern → „Commit changes".

**Trainingszeiten, Bäder-Adressen, Teams:** die Dateien in `data/` sind
bewusst einfach — `trainings.json` (Trainingszeiten, Vorlage liegt drin),
`venues.json` (Bäder mit Adressen), `teams.json` (Mannschaften + DSV-URL).
Änderungen übernimmt der nächste Daten-Lauf automatisch.

## Gut zu wissen

- Bei öffentlichen Repositories sind GitHub Actions und Pages kostenlos.
- GitHub pausiert Zeitpläne nach ~60 Tagen ohne Aktivität — dann im Reiter
  Actions auf „Enable" klicken (beim Saisonstart im Herbst dran denken).
- Wasserball-Saison läuft ca. September–Juni (eine Saison, kein
  Feld/Halle-Wechsel wie beim Hockey) — Saisonwechsel heißt hier nur:
  neue Liga-URLs in `data/teams.json`.
- Später möglich (wie beim CHTC geplant): Push-Benachrichtigungen über
  eine native Flutter-App, Original-Logo, weitere Teams.
