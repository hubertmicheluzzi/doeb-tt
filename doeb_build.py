#!/usr/bin/env python3
"""
doeb_build.py — HTML-Generator für DOEBAna
Liest den JSON-Cache (doeb_fetch.py) und generiert:
  - LIVE/DOEBAna_W1.html  (+ W2, V1, V2)
  - AR/2026/DG[x]/R[n]/DOEBAna_*.html  (Snapshots je Runde)
  - archiv.html  (Übersicht aller Snapshots)

Aufruf: python3 doeb_build.py [--live-only] [--ar-only]
"""

import json
import os
import datetime
import sys

# ── Konfiguration ──────────────────────────────────────────────────────────

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "cache", "xttv_data.json")
LIVE_DIR   = os.path.join(BASE_DIR, "LIVE")
AR_BASE    = os.path.join(BASE_DIR, "AR", "2026")

TEAM_META = {
    "W1": {"label": "W1·3.Kl.B",  "liga": "3. Klasse B",  "cls": "w1", "farbe": "#1565c0"},
    "W2": {"label": "W2·Gr.VIb",  "liga": "Gruppe VIb",   "cls": "w2", "farbe": "#1976d2"},
    "V1": {"label": "V1·1.Kl.B",  "liga": "1. Klasse B",  "cls": "v1", "farbe": "#e65100"},
    "V2": {"label": "V2·4.Kl.",    "liga": "4. Klasse",    "cls": "v2", "farbe": "#f57c00"},
}

# ── Hilfsfunktionen ─────────────────────────────────────────────────────────

def load_cache():
    with open(CACHE_FILE, encoding="utf-8") as f:
        return json.load(f)

def badge(ergebnis, doeb_heim):
    """Errechnet Sieg/Unentschieden/Niederlage aus Ergebnis-String."""
    if not ergebnis:
        return "", ""
    try:
        teile = ergebnis.split(":")
        h, g = int(teile[0]), int(teile[1])
        if doeb_heim:
            doeb, gegner = h, g
        else:
            doeb, gegner = g, h
        if doeb > gegner:
            return "S", "badge-s"
        elif doeb == gegner:
            return "U", "badge-u"
        else:
            return "N", "badge-n"
    except:
        return "", ""

def doeb_ergebnis(ergebnis, doeb_heim):
    """Gibt Ergebnis aus DOEB-Perspektive zurück (DOEB:Gegner)."""
    if not ergebnis:
        return ""
    try:
        h, g = ergebnis.split(":")
        if doeb_heim:
            return f"{h}:{g}"
        else:
            return f"{g}:{h}"
    except:
        return ergebnis

def ist_doeb_heim(spiel, team_key):
    """Prüft ob DOEB Heimmannschaft ist."""
    heim = spiel.get("heim", "").upper()
    return "DOEB" in heim or "DÖB" in heim

def format_datum(datum_str):
    """Formatiert Datum für Anzeige."""
    # XTTV liefert z.B. "2026-09-25" oder "Fr. 25.09.2026"
    try:
        d = datetime.datetime.strptime(datum_str, "%Y-%m-%d")
        return d.strftime("%d.%m.")
    except:
        # Fallback: so anzeigen wie es kommt, ohne Wochentag
        for prefix in ["Mo. ", "Di. ", "Mi. ", "Do. ", "Fr. ", "Sa. ", "So. "]:
            if datum_str.startswith(prefix):
                datum_str = datum_str[4:]
        return datum_str

# ── CSS / HTML-Bausteine ────────────────────────────────────────────────────

CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: #0d1117;
  color: #c9d1d9;
  font-size: 14px;
  line-height: 1.5;
  padding-top: 62px;
}
:root {
  --wttv-1: #1565c0; --wttv-2: #1976d2;
  --voeb-1: #e65100; --voeb-2: #f57c00;
  --archiv: #546e7a; --regeln: #c62828;
  --border: #30363d; --bg-card: #161b22;
  --text-muted: #8b949e; --text-dim: #6e7681;
}
#bar1 {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  background: #161b22; border-bottom: 1px solid var(--border);
  padding: 5px 10px; display: flex; flex-direction: column;
  align-items: flex-start; gap: 4px;
}
.title { font-weight: 700; font-size: 13px; color: #c9d1d9; white-space: nowrap; }
.sep { color: var(--text-dim); }
.team-btn {
  display: inline-block; padding: 3px 5px; border-radius: 4px;
  font-size: 11px; font-weight: 600; text-decoration: none;
  border: 1px solid transparent; color: #c9d1d9; white-space: nowrap;
}
.btn-w1 { border-color: var(--wttv-1); color: #90caf9; }
.btn-w1:hover, .btn-w1.active { background: var(--wttv-1); color: #fff; border-top: 2px solid #90caf9; }
.btn-w2 { border-color: var(--wttv-2); color: #90caf9; }
.btn-w2:hover, .btn-w2.active { background: var(--wttv-2); color: #fff; border-top: 2px solid #90caf9; }
.btn-v1 { border-color: var(--voeb-1); color: #ffcc80; }
.btn-v1:hover, .btn-v1.active { background: var(--voeb-1); color: #fff; border-top: 2px solid #ffcc80; }
.btn-v2 { border-color: var(--voeb-2); color: #ffcc80; }
.btn-v2:hover, .btn-v2.active { background: var(--voeb-2); color: #fff; border-top: 2px solid #ffcc80; }
.btn-arc { border-color: var(--archiv); color: #90a4ae; }
.btn-arc:hover, .btn-arc.active { background: var(--archiv); color: #fff; border-top: 2px solid #cfd8dc; }
.btn-reg { border-color: var(--regeln); color: #ef9a9a; }
.btn-reg:hover, .btn-reg.active { background: var(--regeln); color: #fff; border-top: 2px solid #ef9a9a; }
#bar2 {
  position: fixed; top: 62px; left: 0; right: 0; z-index: 99;
  background: #161b22; border-bottom: 2px solid var(--border);
  padding: 4px 10px; display: flex; align-items: center;
  gap: 2px; flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none;
}
.sec-btn {
  display: inline-block; padding: 2px 3px; border-radius: 2px;
  font-size: 10px; font-weight: 600; text-decoration: none;
  border: 1px solid var(--border); color: var(--text-muted);
  white-space: nowrap; cursor: pointer;
}
.sec-btn.active { background: var(--border); color: #c9d1d9; }
.container { max-width: 900px; margin: 0 auto; padding: 16px 12px 40px; }
.section { margin-bottom: 28px; scroll-margin-top: 80px; }
.sec-title {
  font-size: 12px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .05em; color: var(--text-muted);
  margin-bottom: 10px; padding-bottom: 5px;
  border-bottom: 1px solid var(--border);
}
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th {
  background: #1a2030; color: var(--text-muted);
  padding: 5px 7px; text-align: left; font-weight: 600;
  border-bottom: 1px solid var(--border);
}
td { padding: 6px 7px; border-bottom: 1px solid #1e2530; vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #1a2030; }
.badge {
  display: inline-block; padding: 1px 5px; border-radius: 3px;
  font-size: 10px; font-weight: 700;
}
.badge-s { background: #0d3320; color: #3fb950; }
.badge-u { background: #2d2300; color: #d29922; }
.badge-n { background: #3d0f0f; color: #f85149; }
.dim { color: var(--text-dim); }
.muted { color: var(--text-muted); }
.bold { font-weight: 700; }
.doeb-row td { background: #1a2535; }
.doeb-row:hover td { background: #1e2d40; }
"""

def bar1_html(active_team, stand, prefix=""):
    """Erzeugt Leiste 1. prefix = relativer Pfad zum Root (z.B. '../../' für AR-Dateien)."""
    teams = [
        ("W1", "btn-w1", f"{prefix}LIVE/DOEBAna_W1.html"),
        ("W2", "btn-w2", f"{prefix}LIVE/DOEBAna_W2.html"),
        ("V1", "btn-v1", f"{prefix}LIVE/DOEBAna_V1.html"),
        ("V2", "btn-v2", f"{prefix}LIVE/DOEBAna_V2.html"),
    ]
    btns = ""
    for key, cls, href in teams:
        label = TEAM_META[key]["label"]
        act = " active" if key == active_team else ""
        btns += f'<a href="{href}" class="team-btn {cls}{act}">{label}</a>\n    '
    arc_act = " active" if active_team == "ARC" else ""
    reg_act = " active" if active_team == "REG" else ""
    return f"""<div id="bar1">
  <div style="display:flex;align-items:center;gap:6px;">
    <span class="title">DOEB TT-Übersicht</span>
    <span class="sep">·</span>
    <span style="font-size:11px;color:var(--text-dim)">Stand: {stand}</span>
  </div>
  <div style="display:flex;gap:4px;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;width:fit-content;">
    {btns}<a href="{prefix}archiv.html" class="team-btn btn-arc{arc_act}">Archiv</a>
    <a href="{prefix}REAna.html" class="team-btn btn-reg{reg_act}">Regeln</a>
  </div>
</div>"""

SEKTIONEN = [
    ("s01", "ERG",  "01 · Aktuelles Ergebnis"),
    ("s02", "LEIS", "02 · Spielerleistung"),
    ("s03", "VERL", "03 · Saisonverlauf"),
    ("s04", "STAT", "04 · Spielerstatistik"),
    ("s05", "TAB",  "05 · Tabelle"),
    ("s06", "DEMN", "06 · Nächste Partie"),
    ("s07", "MTX",  "07 · Ergebnismatrix"),
    ("s08", "ANA",  "08 · Einzelanalyse"),
    ("s09", "GEG",  "09 · Gegnerprofile"),
    ("s10", "KEN",  "10 · Saisonkennzahlen"),
    ("s11", "ARC",  "11 · Archiv"),
]

def bar2_html(bar2_color="var(--border)"):
    btns = ""
    for sid, kuerzel, _ in SEKTIONEN:
        btns += f'<a class="sec-btn" href="#{sid}">{kuerzel}</a>\n  '
    return f"""<div id="bar2" style="border-bottom-color:{bar2_color};">
  {btns}</div>"""

# ── Sektionen ───────────────────────────────────────────────────────────────

def sec_01(spiele, team_key):
    """Aktuelles Ergebnis (letzte gespielte Runde)."""
    gespielt = [s for s in spiele if s.get("ergebnis")]
    if not gespielt:
        return '<p class="dim">Noch keine Ergebnisse.</p>'

    letzte = gespielt[-1]
    doeb_h = ist_doeb_heim(letzte, team_key)
    erg = doeb_ergebnis(letzte["ergebnis"], doeb_h)
    typ, bcls = badge(letzte["ergebnis"], doeb_h)
    gegner = letzte["gast"] if doeb_h else letzte["heim"]
    ha = "Heimspiel" if doeb_h else "Auswärtsspiel"
    datum = format_datum(letzte.get("datum", ""))

    return f"""<div style="font-size:32px;font-weight:700;text-align:center;letter-spacing:.05em;margin:8px 0">
  {erg} <span class="badge {bcls}" style="font-size:16px;vertical-align:middle">{typ}</span>
</div>
<p style="text-align:center;color:var(--text-muted);font-size:13px">
  R{letzte['runde']} · {datum} · {ha} vs. {gegner}
</p>"""

def sec_03(spiele, team_key):
    """Saisonverlauf — Tabelle aller Runden."""
    gespielt = [s for s in spiele if s.get("ergebnis")]
    if not gespielt:
        return '<p class="dim">Noch keine Spiele.</p>'

    punkte_ges = 0
    rows = ""
    for s in gespielt:
        doeb_h = ist_doeb_heim(s, team_key)
        erg = doeb_ergebnis(s["ergebnis"], doeb_h)
        typ, bcls = badge(s["ergebnis"], doeb_h)
        if typ == "S": punkte_ges += 2
        elif typ == "U": punkte_ges += 1
        gegner = s["gast"] if doeb_h else s["heim"]
        ha = "H" if doeb_h else "A"
        datum = format_datum(s.get("datum", ""))
        rows += f"""<tr>
  <td class="muted">R{s['runde']}</td>
  <td class="dim">{datum}</td>
  <td>{ha}</td>
  <td>{gegner}</td>
  <td style="text-align:center"><span class="badge {bcls}">{erg}</span></td>
  <td style="text-align:center">{punkte_ges}</td>
</tr>\n"""

    return f"""<table>
<thead><tr>
  <th>Runde</th><th>Datum</th><th>H/A</th><th>Gegner</th>
  <th style="text-align:center">Erg.</th><th style="text-align:center">Pkt</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>"""

def sec_05(tabelle, team_key):
    """Ligatabelle."""
    if not tabelle:
        return '<p class="dim">Tabelle nicht verfügbar.</p>'

    rows = ""
    for t in tabelle:
        ist_doeb = "DOEB" in t.get("team","").upper() or "DÖB" in t.get("team","").upper()
        cls = ' class="doeb-row bold"' if ist_doeb else ""
        rows += f"""<tr{cls}>
  <td style="text-align:center">{t['platz']}</td>
  <td>{t['team']}</td>
  <td style="text-align:center">{t['sp']}</td>
  <td style="text-align:center">{t['s']}</td>
  <td style="text-align:center">{t['u']}</td>
  <td style="text-align:center">{t['n']}</td>
  <td style="text-align:center">{t['punkte']}</td>
</tr>\n"""

    return f"""<table>
<thead><tr>
  <th style="text-align:center">#</th><th>Team</th>
  <th style="text-align:center">Sp</th><th style="text-align:center">S</th>
  <th style="text-align:center">U</th><th style="text-align:center">N</th>
  <th style="text-align:center">Pkt</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>"""

def sec_08(letzte_runde, team_key):
    """Einzelpunkte-Analyse der letzten Runde."""
    details = letzte_runde.get("details", []) if letzte_runde else []
    if not details:
        return '<p class="dim">Keine Einzeldaten verfügbar.</p>'

    doeb_h = ist_doeb_heim(letzte_runde, team_key)
    rows = ""
    for d in details:
        hp = d["heim_spieler"].split()[0] if d["heim_spieler"] else "?"
        gp = d["gast_spieler"].split()[0] if d["gast_spieler"] else "?"
        sieger = d.get("sieger","")
        h_bold = ' class="bold"' if sieger == "H" else ""
        g_bold = ' class="bold"' if sieger == "G" else ""
        doeb_s = d["saetze_heim"] if doeb_h else d["saetze_gast"]
        geg_s  = d["saetze_gast"] if doeb_h else d["saetze_heim"]
        doeb_p = hp if doeb_h else gp
        geg_p  = gp if doeb_h else hp
        doeb_w = (doeb_h and sieger=="H") or (not doeb_h and sieger=="G")
        rows += f"""<tr>
  <td class="muted">{d['pos']}</td>
  <td{' class="bold"' if doeb_w else ''}>{doeb_p}</td>
  <td class="dim">{doeb_s}:{geg_s}</td>
  <td{' class="bold"' if not doeb_w else ''}>{geg_p}</td>
</tr>\n"""

    return f"""<table>
<thead><tr>
  <th>#</th><th>DOEB</th><th style="text-align:center">Sätze</th><th>Gegner</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>"""

def sec_10(spiele, team_key):
    """Saisonkennzahlen."""
    gespielt = [s for s in spiele if s.get("ergebnis")]
    sp = len(gespielt)
    s = u = n = pkt = 0
    for spiel in gespielt:
        doeb_h = ist_doeb_heim(spiel, team_key)
        typ, _ = badge(spiel["ergebnis"], doeb_h)
        if typ == "S": s += 1; pkt += 2
        elif typ == "U": u += 1; pkt += 1
        elif typ == "N": n += 1

    return f"""<table>
<thead><tr><th>Sp</th><th>S</th><th>U</th><th>N</th><th>Punkte</th></tr></thead>
<tbody><tr>
  <td style="text-align:center">{sp}</td>
  <td style="text-align:center">{s}</td>
  <td style="text-align:center">{u}</td>
  <td style="text-align:center">{n}</td>
  <td style="text-align:center">{pkt}</td>
</tr></tbody>
</table>"""

def placeholder(text="In Entwicklung"):
    return f'<p class="dim">{text}</p>'

# ── HTML-Seite generieren ───────────────────────────────────────────────────

def make_page(team_key, team_data, stand, prefix="", runde_info=None):
    """
    Generiert vollständige HTML-Seite für ein Team.
    runde_info: None = LIVE, sonst dict mit dg/runde für AR-Titel
    """
    meta = TEAM_META[team_key]
    spiele  = team_data["spiele"]
    tabelle = team_data["tabelle"]

    gespielt = [s for s in spiele if s.get("ergebnis")]
    letzte = gespielt[-1] if gespielt else None

    # Titel
    if runde_info:
        titel = f"DOEB TT · {team_key} · {meta['liga']} · DG{runde_info['dg']} · R{runde_info['runde']} · {stand}"
    else:
        titel = f"DOEBAna · {team_key} · {meta['liga']} · {stand}"

    # bar2-Farbe = Teamfarbe
    bar2_color = meta["farbe"]

    # Sektionen zusammenbauen
    secs = {sid: "" for sid, _, _ in SEKTIONEN}
    secs["s01"] = sec_01(spiele, team_key)
    secs["s02"] = placeholder("Spielerleistung — folgt")
    secs["s03"] = sec_03(spiele, team_key)
    secs["s04"] = placeholder("Spielerstatistik — folgt")
    secs["s05"] = sec_05(tabelle, team_key)
    secs["s06"] = placeholder("Nächste Partie — folgt")
    secs["s07"] = placeholder("Ergebnismatrix — folgt")
    secs["s08"] = sec_08(letzte, team_key)
    secs["s09"] = placeholder("Gegnerprofile — folgt")
    secs["s10"] = sec_10(spiele, team_key)
    secs["s11"] = placeholder("Archiv-Links — folgt")

    sek_html = ""
    for sid, kuerzel, label in SEKTIONEN:
        sek_html += f'<div id="{sid}" class="section">\n'
        sek_html += f'<div class="sec-title">{label}</div>\n'
        sek_html += secs[sid] + "\n"
        sek_html += "</div>\n\n"

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{titel}</title>
<style>{CSS}</style>
</head>
<body>

{bar1_html(team_key, stand, prefix)}

{bar2_html(bar2_color)}

<div class="container">
{sek_html}
</div>

<script>
// Aktiven sec-btn beim Scrollen aktualisieren
const sections = document.querySelectorAll('.section');
const btns = document.querySelectorAll('.sec-btn');
const obs = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (e.isIntersecting) {{
      btns.forEach(b => b.classList.remove('active'));
      const b = document.querySelector(`.sec-btn[href="#${{e.target.id}}"]`);
      if (b) b.classList.add('active');
    }}
  }});
}}, {{rootMargin: '-40% 0px -55% 0px'}});
sections.forEach(s => obs.observe(s));
</script>

</body>
</html>
"""

# ── Datei schreiben ──────────────────────────────────────────────────────────

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ {os.path.relpath(path, BASE_DIR)}")

# ── Hauptprogramm ────────────────────────────────────────────────────────────

def build_live(data):
    """Generiert LIVE-Dateien für alle 4 Teams."""
    stand = data["stand"].split(" ")[0]  # nur Datum
    print("\n── LIVE ──")
    for team_key, team_data in data["teams"].items():
        html = make_page(team_key, team_data, stand, prefix="../")
        path = os.path.join(LIVE_DIR, f"DOEBAna_{team_key}.html")
        write_file(path, html)

def build_ar(data):
    """Generiert AR-Snapshots für alle gespielten Runden."""
    stand = data["stand"].split(" ")[0]
    print("\n── AR-Snapshots ──")

    for team_key, team_data in data["teams"].items():
        spiele = team_data["spiele"]
        gespielt = [s for s in spiele if s.get("ergebnis")]

        for i, spiel in enumerate(gespielt):
            dg = spiel.get("dg", "1") or "1"
            runde = spiel.get("runde", str(i+1)) or str(i+1)

            # AR-Daten = nur Spiele bis zu dieser Runde
            ar_spiele = gespielt[:i+1]
            ar_data = {
                "spiele": ar_spiele + [s for s in spiele if not s.get("ergebnis")],
                "tabelle": team_data["tabelle"],  # Tabelle nach dieser Runde (Annäherung)
            }

            runde_info = {"dg": dg, "runde": runde}
            datum = format_datum(spiel.get("datum",""))
            html = make_page(team_key, ar_data, datum, prefix="../../../../", runde_info=runde_info)
            path = os.path.join(AR_BASE, f"DG{dg}", f"R{runde}", f"DOEBAna_{team_key}.html")
            write_file(path, html)

def main():
    if not os.path.exists(CACHE_FILE):
        print("FEHLER: Kein Cache gefunden. Zuerst doeb_fetch.py ausführen.")
        sys.exit(1)

    data = load_cache()
    live_only = "--live-only" in sys.argv
    ar_only   = "--ar-only"   in sys.argv

    if not ar_only:
        build_live(data)
    if not live_only:
        build_ar(data)

    print("\nFertig.")

if __name__ == "__main__":
    main()
