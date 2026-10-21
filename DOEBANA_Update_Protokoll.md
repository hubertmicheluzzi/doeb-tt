# DOEBANA_update — Protokoll & Checkliste

**Stand: 21.10.2026 · ersetzt die alte `SU9ANA_Update_Protokoll.md` (su9-tt-Repo) vollständig — SU9Ana ist Geschichte.**

Diese Datei gehört ins Repo **`doeb-tt`** (GitHub Pages: `https://hubertmicheluzzi.github.io/doeb-tt/`), Root-Ebene, neben `index.html`, `archiv.html`, `REAna.html`.

---

## Auslöser
Neues Spielergebnis liegt vor. Befehl: `DOEBANA_update`

---

## Ablauf im Überblick

1. Daten vom Web abrufen (Schritt 1 unten)
2. Auf Claude ausführen: `DOEBANA_update` → liefert geänderte LIVE-Files + AR-File zum Download
3. Zip herunterladen, entpacken, Dateien in `~/HM_ARCHIV-2026/HM-KI-PROJEKTE-2026/HM-DOEB-TT/` einspielen
4. Im Terminal:
   ```
   python3 ~/HM_ARCHIV-2026/HM-KI-PROJEKTE-2026/HM-DOEB-TT/doeb_push.py
   ```
   (ersetzt die früheren manuellen `git add`/`commit`/`push`-Befehle)
5. GitHub Pages: ~40 Sekunden bis live

---

## Schritt 1: Ergebnis holen

XTTV-Seiten aufrufen (Browser) — Team-IDs Saison 2026/27:

- W1 (WTTV, 3. Klasse B): `https://oettv.xttv.at/ed/index.php?tid=55340&do=spiele`
- W2 (WTTV, Gruppe VIb): `https://oettv.xttv.at/ed/index.php?tid=55341&do=spiele`
- V1 (VÖB, 1. Klasse B): `https://voeb.xttv.at/ed/index.php?tid=3106&do=spiele`
- V2 (VÖB, 4. Klasse): `https://voeb.xttv.at/ed/index.php?tid=3107&do=spiele`

> Diese `tid`-Werte sind pro Saison neu vergeben (die alten 52678/52679/3090/3091 waren von der Vorsaison). Falls sie nächste Saison nicht mehr passen: über `https://oettv.xttv.at/ed/index.php?do=vereinstermine&vid=394&sjid=XX&oid=196` (DOEB-Vereinsseite, zeigt alle Mannschaften mit Team-Link) bzw. `https://voeb.xttv.at/ed/index.php?do=vereinstermine&vid=4000739&sjid=XX` die aktuellen `tid`/`lid` ablesen — dieselbe Quelle, die auch `doeb-termine` automatisch nutzt (siehe unten).

Notieren:
- DG + Runde
- Datum, H/A
- Score (aus DOEB-Sicht: DOEB:Gegner)
- Aufstellung DOEB (A/B/C)
- Aufstellung Gegner
- Alle 10 Einzelergebnisse (IIIA, I–IX)

---

## Schritt 2: LIVE-File updaten

Betrifft `LIVE/DOEBAna_W1.html`, `DOEBAna_W2.html`, `DOEBAna_V1.html`, `DOEBAna_V2.html`.

### Pflichtfelder pro Sektion:

| Sek | Inhalt | Update |
|-----|--------|--------|
| **01** | big-score | `team doeb` = immer **DOEB 1/2**, Score, Gegner-Team |
| **01** | card-title | DG + Runde + Datum + H/A |
| **01** | meta links | "Sieg/Niederlage/Remis · X Punkte" |
| **01** | meta mitte | "Heim/Auswärts · Rang X" |
| **01** | stat-chips | Mannschaftspunkte, DOEB Gesamtpunkte, DOEB Rang |
| **01** | analysis | Kurze Spielbeschreibung |
| **02** | section-label | "DG2 RX vs GEGNER" updaten |
| **02** | Spieler-Subtexte | "DG2 RX · Einzel Y/Z · Doppel ..." |
| **02** | Spieler-Details | Einzelergebnisse gegen Gegner-Spieler |
| **02** | Fazit-Text | Auf aktuelles Spiel anpassen |
| **03** | section-label | "Der Gegner · GEGNER" updaten |
| **03** | stat-chips | Rang, Punkte, S-U-N, Sp-V des Gegners |
| **03** | tbody | Gegner-Spieler mit S/N-Bilanz gegen DOEB |
| **03** | Analyse-Text | Stärken/Schwächen des Gegners |
| **04** | section-label | "Kreuzmatrix DG2 RX" updaten |
| **04** | card-title | "DOEB X vs GEGNER · Endstand Y:Z" |
| **04** | Aufstellungszeile | A/B/C und Gegner X/Y/Z |
| **04** | games-grid | Alle 10 Spielzellen (IIIA + I–IX) |
| **05** | Fazit-Text | "Fazit DG2 RX:" aktualisieren |
| **06** | card-title | "Vorschau: DOEB vs NÄCHSTER" |
| **06** | Oberer Block | Datum, H/A, nächster Gegner |
| **06** | stat-chips | Rang/Punkte des nächsten Gegners |
| **07** | card-title | "Stand DD.MM.YYYY" |
| **07** | stat-chips | DOEB Rang, Punkte, Gespielt, Offen |
| **08** | Spieler-Einzel | +Einsätze, +Siege, +Niederlagen pro Spieler |
| **09** | Doppel-Tabelle | +Einsätze, +Siege/Niederlagen pro Paar |
| **10** | card-title | "X offene Spiele" (–1) |
| **10** | Ergebnis-Zeile | Prognose → "Y:Z ✓/✗", tr class hl entfernen |
| **11** | card-title | "X offene Spiele" (–1) |
| **11** | Zeile entfernen | Gespielte Runde aus Tabelle löschen |
| **11** | Nächste Zeile | class="hl" auf nächstes Spiel setzen |

### ⚠ Kritische Fehlerquellen:

1. **big-score**: `team doeb` muss IMMER "DOEB 1" oder "DOEB 2" enthalten — NIE den Gegner-Namen
2. **Score-Richtung**: Score immer aus DOEB-Sicht (DOEB:Gegner), auch bei Auswärtsspielen
3. **section-label**: Ist ein eigenes Element — NICHT der card-title. Beide updaten!
4. **Spieler-Subtexte**: Stehen direkt in den player-card divs, nicht in der Tabelle
5. **Header "DOEB TT-Übersicht"**: bleibt in ALLEN LIVE-Files (W1–V2), `archiv.html` und `REAna.html` IMMER als Link codiert — auch bei komplett neu erzeugten Files nicht als reinen `<span>` zurücksetzen:
   ```html
   <span class="title"><a href="https://hubertmicheluzzi.github.io/doeb-termine/"
   style="color:inherit;text-decoration:none;">DOEB TT-Übersicht</a></span>
   ```
   (Der Link ändert sich nicht mehr — einmal gesetzt, einfach bei jedem Update stehen lassen.)

---

## Schritt 3: AR-File erstellen

Neues AR-File in `AR/2026/DG1/Rx/` bzw. `AR/2026/DG2/Rx/` je Mannschaft und Runde.

> Archiv-Reset mit der Umbenennung SU9Ana→DOEBAna: die alten Jahrgänge 2023–2025 wurden gelöscht, das Archiv beginnt bei **2026** neu — passend zum neuen Vereinsnamen.

Basis: **vorheriges AR-File** kopieren, dann updaten:

| Sek | Update |
|-----|--------|
| `<title>` | "DG2 · RX · TT.MM.JJJJ" |
| Header-Bar | "Stand nach Runde X" |
| **01** | Kompletter Spielbericht (Score, Datum, Aufstellung, Kreuzmatrix) |
| **02** | Spielerleistung (Quote, S/N, Details) |
| **03** | Gegner-Spieler mit Bilanz gegen DOEB in diesem Spiel |
| **04** | Kreuzmatrix dieses Spiels |
| **05** | Gesamtanalyse |
| **06** | Nächstes Spiel zum damaligen Zeitpunkt |
| **07** | Ligatabelle aus Tabellendaten für diesen DG+Runde |
| **08** | Kumulierte Einzelstatistiken bis diese Runde |
| **09** | Kumulierte Doppelstatistiken bis diese Runde |
| **10** | Alle Ergebnisse bis diese Runde (+neues am Ende) |
| **11** | Ausstehende Spiele (–1 gespieltes, Ergebnis in Klammern) |

**Archiv-Logik:**
- Pro Runde ein eigener Ordner (`DG1/R1`, `DG1/R2` ...)
- Noch nicht gespielte Runden → Platzhalter "NOCH NICHT GESPIELT"
- Spielfrei → entsprechender Hinweis im HTML
- Nur die Mannschafts-HTMLs, die in dieser Runde gespielt haben
- `index.html` und `REAna.html` werden **nicht** archiviert

---

## Schritt 4: archiv.html updaten

```
<span class="btn wttv pending">GEGNER</span>
→
<a class="btn wttv" href="https://hubertmicheluzzi.github.io/doeb-tt/AR/2026/DG1/Rx/DOEBAna_Wx.html" target="_blank">GEGNER</a>
```
VÖB analog mit `class="btn voeb"`.

AR-Buttons immer in BEIDEN Files aktualisieren (`archiv.html` UND `index.html`), unabhängig voneinander.

---

## Schritt 5: Lokal übernehmen & veröffentlichen

Kein manuelles `git add`/`commit`/`push` mehr — stattdessen:

1. Zip-Download von Claude entpacken, geänderte Dateien nach `~/HM_ARCHIV-2026/HM-KI-PROJEKTE-2026/HM-DOEB-TT/` kopieren (am richtigen Pfad, siehe Ordnerstruktur oben)
2. Terminal:
   ```
   python3 ~/HM_ARCHIV-2026/HM-KI-PROJEKTE-2026/HM-DOEB-TT/doeb_push.py
   ```
3. GitHub Pages: ~40 Sekunden bis live

---

## Sektion 07 — Tabellendaten

Tabellendaten liegen in einer lokalen JSON-Datei (ehemals `su9_tabellen_v2.json` — Pfad/Dateiname lokal prüfen, falls noch nicht auf `doeb_tabellen_v2.json` o. ä. umbenannt).
Key-Schema: `data['W1']['DG2_R5']` → Liste mit allen 10 Teams.
Wenn Runde fehlt (0 Teams): Fallback auf vorherige Runde.
VÖB-Teams: `�` Encoding-Artefakt zwischen Buchstabe und Zahl → beim Parsen entfernen.

---

## Technisches (unverändert gegenüber SU9Ana)

- Dark Mode, IBM Plex Fonts
- iframe-basierte Tab-Navigation
- Daten von `oettv.xttv.at` (WTTV) und `voeb.xttv.at` (VÖB)
- Historische Daten via `sjid=XX` Parameter

---

## Verhältnis zu `doeb-termine`

`doeb-termine` (separates Repo, `https://hubertmicheluzzi.github.io/doeb-termine/`) ist ein **eigenständiges** Projekt — die automatische Terminübersicht für PC/Handy, verlinkt über den Header "DOEB TT-Übersicht". Es holt sich seine Daten **unabhängig** direkt von den XTTV-"Vereinstermine"-Seiten (zweimal täglich per GitHub Action, kein API-Key nötig) und hängt **nicht** von einem `DOEBANA_update`-Lauf ab. Der einzige Berührungspunkt ist der Header-Link (siehe Kritische Fehlerquelle 5 oben) — der muss bei jedem `DOEBANA_update` erhalten bleiben, aber `doeb-termine` selbst muss dafür nicht angestoßen werden.

---

*Ersetzt: `SU9ANA_Update_Protokoll.md` (su9-tt-Repo, erstellt 14.03.2026) — dieses Repo/diese Datei gilt nicht mehr.*
*Erstellt: 21.10.2026*
