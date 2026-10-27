#!/usr/bin/env python3
"""
doeb_gen_v0.02.py — DoebAna-Generator (Testseiten für W1, W2, V1, V2)

Liest NUR die öffentlichen Dateien aus doeb-termine:
  data/termine.json   (Format doeb-termine/1)
  data/tabellen.json  (Format doeb-tabellen/1)
und baut daraus eine Team-Seite. Die bestehende LIVE-Seite dient nur als
Vorlage (Kopfleiste, CSS) und als Quelle für die Analyse-Texte
(Kommentar Sektion 01, Gegnereinschätzung Sektion 06, Bemerkungen Sektion 09).

Aufruf:
  python3 tools/doeb_gen_v0.02.py --data <ordner mit termine.json/tabellen.json> --team w1
Ausgabe:
  test/DOEBAna_<TEAM>_gen_v0.02.html   (die echten LIVE-Seiten bleiben unverändert)

Regeln: unsere Spieler = Rufname, Gegner = Vorname (so wie in den Dateien),
Ergebnisse immer aus DOEB-Sicht. DoebAna schreibt nie in doeb-termine.
"""
import argparse, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NR = ['I', 'II', 'III', 'IIIA', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
BADGE = {'S': 'badge-win', 'U': 'badge-draw', 'N': 'badge-loss'}
MPC = {'S': 'win', 'U': 'draw', 'N': 'loss'}
DIM = '<td class="c" style="font-size:11px;color:var(--text-dim)">'
WTAG = ['Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.', 'So.']
MAXR = {'w1': 18, 'w2': 16, 'v1': 22, 'v2': 22}
HINWEIS = {'PT': 'Platztausch', 'verschoben': 'verschoben', 'abgesagt': 'abgesagt'}

def hinweis(h):
    return HINWEIS.get(h, h) if h else ''

def e(t):
    return html.escape(str(t if t is not None else '–'), quote=False)

def dmy(iso, kurz=False):
    y, m, d = iso.split('-')
    return f'{d}.{m}.' if kurz else f'{d}.{m}.{y}'

def wtag(iso):
    import datetime
    return WTAG[datetime.date.fromisoformat(iso).weekday()]

def res(a, b):
    return 'S' if a > b else ('U' if a == b else 'N')

def section(s, sid, new):
    i = s.index(f'<section id="{sid}"')
    j = s.index('</section>', i) + len('</section>')
    return s[:i] + new + s[j:]

def inner_text(s, sid, pattern):
    """Holt einen Text aus einer Sektion der Vorlage (für Analyse-Texte)."""
    try:
        i = s.index(f'<section id="{sid}"'); j = s.index('</section>', i)
    except ValueError:
        return None
    m = re.search(pattern, s[i:j], re.S)
    return m.group(1).strip() if m else None

def build(team, termine, tabellen, vorlage):
    b = termine['bewerbe'][team]
    tb = tabellen['bewerbe'][team]
    T = b['label']
    liga = b['liga'].replace(', ', ' ')
    pkt = {'S': 3, 'U': 1, 'N': 0} if liga.startswith('VÖB') else {'S': 2, 'U': 1, 'N': 0}
    sysnote = ('VÖB' if pkt['S'] == 3 else 'WTTV') + f': Sieg={pkt["S"]}, Unentschieden=1, Niederlage=0'
    eig = [r for r in tb['tabelle'] if r.get('eigen')][0]
    wir = eig['mannschaft']

    spiele = sorted([g for g in b['spiele'] if g.get('durchgang') == 1],
                    key=lambda g: g['runde'])
    gespielt = [g for g in spiele if g['status'] == 'past' and g.get('punkteEigen') is not None]
    kommend = [g for g in spiele if g['status'] == 'upcoming']
    letzte = max(gespielt, key=lambda g: g['datum'])
    n = letzte['runde']

    # --- Kumulierte Werte ---
    pts = 0; sp = [0, 0]; cnt = {'S': 0, 'U': 0, 'N': 0}; st = {}; dbl = [0, 0]
    ver = ''; mth = ''; mtb = ''; geg = ''
    alte_bem = {}
    vi = vorlage.find('<section id="s09"')
    if vi >= 0:
        for m in re.finditer(r'<tr><td>([^<]+)</td>.*?<td style="font-size:11px;color:var\(--text-muted\)">([^<]*)</td></tr>',
                             vorlage[vi:vorlage.index('</section>', vi)]):
            alte_bem[m.group(1).strip()] = m.group(2)
    runden_mit_spiel = {g['runde'] for g in spiele}
    for r in range(1, max(runden_mit_spiel) + 1):
        g = next((x for x in spiele if x['runde'] == r), None)
        if g is None:
            if r < n:
                ver += f'      <tr><td>R{r}</td><td>–</td><td>–</td><td style="color:var(--text-dim)">spielfrei</td><td class="c">–</td><td class="c">–</td><td class="c num">{pts}</td></tr>\n'
            continue
        if g not in gespielt:
            if r < n or g.get('hinweis'):
                hw = f' <span style="font-size:10px;color:var(--text-dim)">({e(hinweis(g.get("hinweis")))})</span>' if g.get('hinweis') else ''
                ver += (f'      <tr><td>R{r}</td><td>{dmy(g["datum"], True)}</td><td>{g["ha"]}</td><td>{e(g["gegner"])}{hw}</td>'
                        f'<td class="c">–</td><td class="c" style="color:var(--text-dim)">offen</td><td class="c num">{pts}</td></tr>\n')
            continue
        a, c2 = g['punkteEigen'], g['punkteGegner']; x = res(a, c2)
        pts += pkt[x]; cnt[x] += 1; sp[0] += a; sp[1] += c2
        kl = ' <span style="font-size:10px;color:var(--text-dim)">(kl.)</span>' if not g.get('einzel') else ''
        ub = ' <span style="font-size:9px;color:var(--text-dim)">(unbest.)</span>' if not g.get('bestaetigt') else ''
        ver += (f'      <tr><td>R{r}</td><td>{dmy(g["datum"], True)}</td><td>{g["ha"]}</td><td>{e(g["gegner"])}{kl}</td>'
                f'<td class="c"><span class="badge {BADGE[x]}">{a}:{c2}</span></td><td class="c {MPC[x]}">{x}{ub}</td><td class="c num">{pts}</td></tr>\n')
        mth += f'<th class="c">{e(g["gegner"])}</th>'
        mtb += f'<td class="c"><span class="badge {BADGE[x]}">{a}:{c2}</span></td>'
        geg += (f'      <tr><td>{e(g["gegner"])}</td><td class="c">R{r}</td><td class="c">{g["ha"]}</td>'
                f'<td class="c"><span class="badge {BADGE[x]}">{a}:{c2}</span></td>'
                f'<td style="font-size:11px;color:var(--text-muted)">{alte_bem.get(g["gegner"], "")}</td></tr>\n')
        for z in g.get('einzel') or []:
            if z['art'] == 'Doppel':
                dbl[0 if z['sieg'] else 1] += 1
                for p in z['spieler'].split(' / '):
                    st.setdefault(p, [0, 0, 0, 0]); st[p][2 if z['sieg'] else 3] += 1
            else:
                st.setdefault(z['spieler'], [0, 0, 0, 0]); st[z['spieler']][0 if z['sieg'] else 1] += 1

    s = vorlage
    rd = f'DG1 R{n} · {dmy(letzte["datum"])}'
    s = re.sub(r'<title>[^<]*</title>', f'<title>DOEBAna · {T} · TEST Generator v0.02 · {rd}</title>', s, count=1)
    s = re.sub(r'Stand: \d\d\.\d\d\.\d{4}</span></div>',
               f'Stand: {dmy(tabellen["stand"][:10])} · Generator-Test</span></div>', s, count=1)
    # Navigation aus test/ zurück nach LIVE/
    for t in ['W1', 'W2', 'V1', 'V2']:
        s = s.replace(f'<a href="DOEBAna_{t}.html"', f'<a href="../LIVE/DOEBAna_{t}.html"')

    # S01 — Kommentar aus Vorlage übernehmen, wenn er zur selben Runde gehört
    a, c2 = letzte['punkteEigen'], letzte['punkteGegner']; rr = res(a, c2)
    alt_hdr = inner_text(vorlage, 's01', r'<div class="sec-header">([^<]*)</div>') or ''
    kommentar = inner_text(vorlage, 's01', r'<p class="result-comment">(.*?)</p>') if f'R{n} ' in alt_hdr + ' ' else None
    kommentar = kommentar or '<span style="color:var(--text-dim)">(Analyse-Text folgt)</span>'
    s = section(s, 's01', f'''<section id="s01" class="section">
  <div class="sec-header">{T} · {liga} · {rd}</div>
  <div class="result-big">
    <div>
      <div class="result-meta">{"Heim" if letzte["ha"] == "H" else "Auswärts"} · {e(letzte["gegner"])}</div>
      <div style="display:flex;align-items:center;gap:10px;margin-top:4px">
        <span class="result-score">{a} : {c2}</span>
        <span class="badge {BADGE[rr]}">{rr}</span>
      </div>
      <div class="result-meta" style="margin-top:3px">{wtag(letzte["datum"])} {dmy(letzte["datum"])} · {e(letzte.get("zeit"))} · {"bestätigt" if letzte.get("bestaetigt") else "noch nicht bestätigt"}</div>
    </div>
  </div>
  <p class="result-comment">
    {kommentar}
  </p>
</section>''')

    # S02 — Spielerleistung der letzten Runde
    per = {}
    for z in letzte.get('einzel') or []:
        if z['art'] == 'Einzel':
            v = per.setdefault(z['spieler'], {'es': 0, 'en': 0, 'ds': 0, 'dn': 0, 'det': []})
            v['es' if z['sieg'] else 'en'] += 1; v['det'].append(f'{z["saetze"]} gg. {e(z["gegner"])}')
    for z in letzte.get('einzel') or []:
        if z['art'] == 'Doppel':
            for p in z['spieler'].split(' / '):
                v = per.setdefault(p, {'es': 0, 'en': 0, 'ds': 0, 'dn': 0, 'det': []})
                v['ds' if z['sieg'] else 'dn'] += 1; v['det'].append(f'(D: {z["saetze"]})')
    rows = ''
    for p, v in per.items():
        dc = (f'<td class="c {"win" if v["ds"] else "loss"}">{v["ds"]}:{v["dn"]}</td>' if v['ds'] + v['dn'] else '<td class="c">–</td>')
        rows += (f'      <tr><td>{e(p)}</td><td class="c win">{v["es"]}</td><td class="c loss">{v["en"]}</td>{dc}'
                 f'<td style="font-size:11px;color:var(--text-muted)">{" · ".join(v["det"])}</td></tr>\n')
    s = section(s, 's02', f'''<section id="s02" class="section">
  <div class="sec-header">LEIS · Spielerleistung · DG1 R{n}</div>
  <table>
    <thead><tr><th>Spieler</th><th class="c">E-S</th><th class="c">E-N</th><th class="c">D</th><th>Detail</th></tr></thead>
    <tbody>
{rows}    </tbody>
  </table>
  <div style="margin-top:6px;font-size:11px;color:var(--text-dim)">E = Einzel · D = Doppel (Siege:Niederlagen) · alle Ergebnisse aus DOEB-Sicht</div>
</section>''')

    # S03 — Saisonverlauf
    s = section(s, 's03', f'''<section id="s03" class="section">
  <div class="sec-header">VERL · Saisonverlauf</div>
  <table>
    <thead><tr><th>Rd</th><th>Datum</th><th>H/A</th><th>Gegner</th><th class="c">Erg</th><th class="c">MP</th><th class="c">P</th></tr></thead>
    <tbody>
{ver}    </tbody>
  </table>
  <div style="margin-top:6px;font-size:11px;color:var(--text-dim)">Sp {len(gespielt)} · S {cnt["S"]} · U {cnt["U"]} · N {cnt["N"]} · P {pts} · Spielpunkte {sp[0]}:{sp[1]} · {sysnote}</div>
</section>''')

    # S04 — Kumulierte Spielerstatistik (sortiert nach Gesamtsiegen)
    rows = ''
    for p, (es, en, ds, dn) in sorted(st.items(), key=lambda kv: (-(kv[1][0] + kv[1][2]), kv[0])):
        pct = f'{round(100 * es / (es + en))}%' if es + en else '–'
        dc = f'<td class="c win">{ds}</td><td class="c loss">{dn}</td>' if ds + dn else '<td class="c">–</td><td class="c">–</td>'
        rows += (f'      <tr><td>{e(p)}</td><td class="c win">{es}</td><td class="c loss">{en}</td><td class="c">{pct}</td>'
                 f'{dc}<td class="c num">{es + ds}/{es + en + ds + dn}</td></tr>\n')
    s = section(s, 's04', f'''<section id="s04" class="section">
  <div class="sec-header">STAT · Spielerstatistik kumuliert</div>
  <table>
    <thead><tr><th>Spieler</th><th class="c">E-S</th><th class="c">E-N</th><th class="c">E-%</th><th class="c">D-S</th><th class="c">D-N</th><th class="c">Ges</th></tr></thead>
    <tbody>
{rows}    </tbody>
  </table>
  <div style="margin-top:6px;font-size:11px;color:var(--text-dim)">Stand nach R{n} · Ges = Siege/Spiele (Einzel + Doppel) · aus termine.json</div>
</section>''')

    # S05 — Tabelle
    tr = ''
    for r in tb['tabelle']:
        cells = (f'<td class="c">{r["spiele"]}</td><td class="c win">{r["siege"]}</td><td class="c">{r["unentschieden"]}</td>'
                 f'<td class="c">{r["niederlagen"]}</td><td class="c">{r["einzel"]}</td>')
        if r.get('eigen'):
            tr += (f'      <tr class="highlight-row"><td class="c"><span class="pos-badge">{r["platz"]}</span></td>'
                   f'<td><strong>{e(r["mannschaft"])}</strong></td>{cells}<td class="c num"><strong>{r["punkte"]}</strong></td></tr>\n')
        else:
            top = ' top3' if r['platz'] <= 3 else ''
            tr += (f'      <tr><td class="c"><span class="pos-badge{top}">{r["platz"]}</span></td>'
                   f'<td>{e(r["mannschaft"])}</td>{cells}<td class="c num">{r["punkte"]}</td></tr>\n')
    s = section(s, 's05', f'''<section id="s05" class="section">
  <div class="sec-header">TAB · {liga} · Stand {dmy(tb["stand"])}</div>
  <table>
    <thead><tr><th class="c">#</th><th>Mannschaft</th><th class="c">Sp</th><th class="c">S</th><th class="c">U</th><th class="c">N</th><th class="c">Spiele</th><th class="c">P</th></tr></thead>
    <tbody>
{tr}    </tbody>
  </table>
  <div style="margin-top:6px;font-size:11px;color:var(--text-dim)">Quelle: tabellen.json · {sysnote}</div>
</section>''')

    # S06 — Nächste Partie (Fakten aus den Dateien, Einschätzung aus der Vorlage)
    if kommend:
        nx = min(kommend, key=lambda g: g['datum'])
        ng = [r for r in tb['tabelle'] if r['mannschaft'] == nx['gegner']]
        info = f'{wir} – {nx["gegner"]}' if nx['ha'] == 'H' else f'{nx["gegner"]} – {wir}'
        stat = (f'Rang {ng[0]["platz"]} · {ng[0]["spiele"]} Sp · {ng[0]["siege"]}S-{ng[0]["unentschieden"]}U-{ng[0]["niederlagen"]}N'
                f' · {ng[0]["einzel"]} · {ng[0]["punkte"]} Pkte') if ng else ''
        alt_info = inner_text(vorlage, 's06', r'<div class="next-match-info">([^<]*)</div>') or ''
        txt = inner_text(vorlage, 's06', r'<p[^>]*>(.*?)</p>') if nx['gegner'].replace(' ', '') in alt_info.replace(' ', '') else None
        txt = txt or '<span style="color:var(--text-dim)">(Gegnereinschätzung folgt)</span>'
        s06 = f'''<section id="s06" class="section">
  <div class="sec-header">DEMN · Nächste Partie & Gegnereinschätzung</div>
  <div class="next-match">
    <div class="next-match-title">Nächstes Spiel · R{nx["runde"]}</div>
    <div class="next-match-info">{e(info)}</div>
    <div class="next-match-sub">{wtag(nx["datum"])} {dmy(nx["datum"])} · {e(nx.get("zeit"))} · {"Heimspiel" if nx["ha"] == "H" else "Auswärtsspiel"}{" · " + e(hinweis(nx["hinweis"])) if nx.get("hinweis") else ""}</div>
  </div>
  <div style="margin-bottom:8px">
    <strong style="font-size:13px;color:#e6edf3">{e(nx["gegner"])}</strong>
    <span style="font-size:11px;color:var(--text-dim);margin-left:6px">{stat}</span>
  </div>
  <p style="font-size:13px;line-height:1.6">{txt}</p>
</section>'''
    else:
        s06 = '<section id="s06" class="section">\n  <div class="sec-header">DEMN · Nächste Partie & Gegnereinschätzung</div>\n  <p style="font-size:12px;color:var(--text-dim)">Kein weiteres Spiel im Durchgang 1.</p>\n</section>'
    s = section(s, 's06', s06)

    # S07 — Ergebnismatrix
    s = section(s, 's07', f'''<section id="s07" class="section">
  <div class="sec-header">MTX · Ergebnismatrix</div>
  <div style="overflow-x:auto">
    <table>
      <thead><tr><th>Team</th>{mth}<th class="c" style="color:var(--text-dim);font-size:10px">Σ</th></tr></thead>
      <tbody><tr><td><strong>{e(wir)}</strong></td>{mtb}<td class="c num" style="color:var(--text-dim)">{pts}P</td></tr></tbody>
    </table>
  </div>
</section>''')

    # S08 — Einzelpunkte der letzten Runde (statisch); die automatische ANA-Logik der Vorlage bleibt erhalten
    trs = ''
    for z in sorted(letzte.get('einzel') or [], key=lambda z: NR.index(z['nr']) if z['nr'] in NR else 99):
        w = z['sieg']
        trs += (f'      <tr><td{" class=\"winner\"" if w else ""}>{e(z["spieler"].replace(" / ", "/"))}</td>'
                f'<td class="c"><span class="badge {"badge-win" if w else "badge-loss"}">{z["saetze"]}</span></td>'
                f'<td{"" if w else " class=\"winner\""}>{e(z["gegner"].replace(" / ", "/"))}</td>{DIM}{"D" if z["art"] == "Doppel" else "E"}</td></tr>\n')
    hh = f'{wir} (Heim) – {letzte["gegner"]} (Gast)' if letzte['ha'] == 'H' else f'{letzte["gegner"]} (Heim) – {wir} (Gast)'
    s = section(s, 's08', f'''<section id="s08" class="section">
  <div class="sec-header" id="ana-head">ANA · Einzelpunkte-Analyse · {rd}</div>
  <div id="ana-static">
    <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px">{e(hh)} &nbsp;·&nbsp; aus DOEB-Sicht <strong>{a}:{c2}</strong> &nbsp;·&nbsp; Aufstellung: {e(letzte.get("spieler"))}</div>
    <table>
      <thead><tr><th>{e(wir)}</th><th class="c">Ergebnis</th><th>{e(letzte["gegner"])}</th><th class="c">Art</th></tr></thead>
      <tbody>
{trs}      </tbody>
    </table>
    <div style="margin-top:6px;font-size:11px;color:var(--text-dim)">Ergebnisse immer aus DOEB-Sicht (DOEB:Gegner) · E = Einzel · D = Doppel</div>
  </div>
  <div id="ana-auto" style="display:none">
    <div id="ana-sub" style="font-size:12px;color:var(--text-muted);margin-bottom:8px"></div>
    <div style="overflow-x:auto">
    <table>
      <thead><tr><th>{e(wir)}</th><th class="c">Ergebnis</th><th id="ana-gegner">Gegner</th><th class="c">Art</th></tr></thead>
      <tbody id="ana-body"></tbody>
    </table>
    </div>
  </div>
  <div id="ana-foot" style="margin-top:6px;font-size:11px;color:var(--text-dim)"></div>
</section>''')

    # S09 — Gegnerprofile
    s = section(s, 's09', f'''<section id="s09" class="section">
  <div class="sec-header">GEG · Gegnerprofile</div>
  <table>
    <thead><tr><th>Gegner</th><th class="c">R</th><th class="c">H/A</th><th class="c">Erg</th><th>Bemerkung</th></tr></thead>
    <tbody>
{geg}    </tbody>
  </table>
</section>''')

    # S10 — Kennzahlen
    es = sum(v[0] for v in st.values()); en = sum(v[1] for v in st.values())
    s = section(s, 's10', f'''<section id="s10" class="section">
  <div class="sec-header">KEN · Saisonkennzahlen</div>
  <table>
    <thead><tr><th>Kennzahl</th><th class="c">Wert</th><th>Kennzahl</th><th class="c">Wert</th></tr></thead>
    <tbody>
      <tr><td>Spiele gesamt</td><td class="c num">{len(gespielt)}</td><td>Mannschaftspunkte</td><td class="c num">{pts}</td></tr>
      <tr><td>Siege</td><td class="c win">{cnt["S"]}</td><td>Spielpunkte</td><td class="c num">{sp[0]}:{sp[1]}</td></tr>
      <tr><td>Unentschieden</td><td class="c draw">{cnt["U"]}</td><td>Einzel-Gewinnquote</td><td class="c num">{round(100 * es / (es + en)) if es + en else 0}%</td></tr>
      <tr><td>Niederlagen</td><td class="c loss">{cnt["N"]}</td><td>Doppel-Gewinnquote</td><td class="c num">{round(100 * dbl[0] / sum(dbl)) if sum(dbl) else 0}%</td></tr>
      <tr><td>Tabellenplatz</td><td class="c num">{eig["platz"]}/{len(tb["tabelle"])}</td><td>Runden gespielt</td><td class="c num">{len(gespielt)}/{MAXR.get(team, "?")}</td></tr>
    </tbody>
  </table>
  <div style="margin-top:6px;font-size:11px;color:var(--text-dim)">Einzel {es}:{en} · Doppel {dbl[0]}:{dbl[1]} · Kontrolle Tabelle: {eig["einzel"]} / {eig["punkte"]} P</div>
</section>''')

    # S11 — Archiv-Links (Pfade von test/ aus)
    links = ''.join(f'    <a href="../AR/2026/DG1/R{g["runde"]}/DOEBAna_{T}.html" class="arc-link">DG1 R{g["runde"]} · {dmy(g["datum"])}</a>\n'
                    for g in gespielt)
    i = s.index('<div class="arc-grid">'); j = s.index('</div>', i)
    s = s[:i] + '<div class="arc-grid">\n' + links + '  ' + s[j:]
    return s, dict(team=T, runde=n, punkte=pts, spielpunkte=f'{sp[0]}:{sp[1]}', tabelle=f'{eig["einzel"]} / {eig["punkte"]} P',
                   spieler={k: v for k, v in st.items()})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True, help='Ordner mit termine.json und tabellen.json')
    ap.add_argument('--team', default='w1')
    a = ap.parse_args()
    termine = json.load(open(os.path.join(a.data, 'termine.json'), encoding='utf-8'))
    tabellen = json.load(open(os.path.join(a.data, 'tabellen.json'), encoding='utf-8'))
    assert termine.get('format') == 'doeb-termine/1', termine.get('format')
    assert tabellen.get('format') == 'doeb-tabellen/1', tabellen.get('format')
    T = termine['bewerbe'][a.team]['label']
    vorlage = open(os.path.join(ROOT, 'LIVE', f'DOEBAna_{T}.html'), encoding='utf-8').read()
    s, info = build(a.team, termine, tabellen, vorlage)
    os.makedirs(os.path.join(ROOT, 'test'), exist_ok=True)
    out = os.path.join(ROOT, 'test', f'DOEBAna_{T}_gen_v0.02.html')
    open(out, 'w', encoding='utf-8').write(s)
    print('geschrieben:', os.path.relpath(out, ROOT))
    print(info)

if __name__ == '__main__':
    main()
