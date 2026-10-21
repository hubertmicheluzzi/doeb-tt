#!/usr/bin/env python3
"""
doeb_fetch.py — XTTV API Datenabruf für DOEBAna
Holt Spielergebnisse und Tabellenstände für alle 4 DOEB-Mannschaften,
speichert sie als JSON-Cache lokal.

Aufruf: python3 doeb_fetch.py [--force]
  --force  Cache ignorieren, alles neu laden

API-Format (verifiziert 12.10.2026):
  https://{host}.xttv.at/xml/v1/{Methode}.php?apikey={KEY}&{params}
Methoden: getLeagueResults, getLeagueTeams, getGameDetails
XML getLeagueResults: <game_id>, <round_nr>, <date>, <time>,
  <team_home_id>, <team_home_short_name>, <team_away_id>, <team_away_short_name>,
  <matches_won_home>, <matches_won_away>, <played>, <confirmed>
  + <player> (wiederholt): <id>, <team_id>, <first_name>, <last_name>,
    <matches_won>, <matches_lost>
"""

import urllib.request
import ssl
import xml.etree.ElementTree as ET
import json
import os
import sys
import datetime

# macOS Python 3.x: SSL-Kontext mit certifi oder System-Fallback
_SSL_CTX = ssl.create_default_context()
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX.check_hostname = False
    _SSL_CTX.verify_mode = ssl.CERT_NONE

# ── Konfiguration ────────────────────────────────────────────────────────────

API_KEY = "f68965680155a865"

TEAMS = {
    "W1": {"tid": "55340", "liga": "WTTV 3. Kl. B",   "lid": "8957",   "host": "oettv"},
    "W2": {"tid": "55341", "liga": "WTTV Gr. VIb",    "lid": "8970",   "host": "oettv"},
    "V1": {"tid": "3106",  "liga": "VÖB 1. Kl. B",    "lid": "4220124","host": "voeb"},
    "V2": {"tid": "3107",  "liga": "VÖB 4. Kl.",       "lid": "4220127","host": "voeb"},
}

HOSTS = {
    "oettv": "https://oettv.xttv.at/xml/v1",
    "voeb":  "https://voeb.xttv.at/xml/v1",
}

CACHE_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "xttv_data.json")
CACHE_MAX_AGE_HOURS = 2

# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def api_url(host, method, params):
    base = HOSTS[host]
    param_str = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base}/{method}.php?apikey={API_KEY}&{param_str}"

def fetch_xml(url):
    print(f"  GET {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DOEBAna/1.0"})
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as resp:
            data = resp.read()
        return ET.fromstring(data)
    except Exception as e:
        print(f"  FEHLER: {e}")
        return None

def cache_fresh():
    if not os.path.exists(CACHE_FILE):
        return False
    age = datetime.datetime.now().timestamp() - os.path.getmtime(CACHE_FILE)
    return age < CACHE_MAX_AGE_HOURS * 3600

def load_cache():
    with open(CACHE_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_cache(data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Cache gespeichert: {CACHE_FILE}")

# ── API-Methoden ─────────────────────────────────────────────────────────────

def get_league_results(team_key):
    """
    getLeagueResults: Spiele eines Teams in einer Liga.
    Ergebnis aus matches_won_home / matches_won_away.
    Spielerstatistiken direkt im <game>-Element als <player>-Kinder.
    """
    t = TEAMS[team_key]
    url = api_url(t["host"], "getLeagueResults", {
        "leagueId": t["lid"],
        "teamId":   t["tid"],
    })
    root = fetch_xml(url)
    if root is None:
        return []

    games = []
    for g in root.findall("game"):
        heim_id  = g.findtext("team_home_id", "")
        gast_id  = g.findtext("team_away_id", "")
        heim     = g.findtext("team_home_short_name", "")
        gast     = g.findtext("team_away_short_name", "")
        mwh      = g.findtext("matches_won_home", "")
        mwa      = g.findtext("matches_won_away", "")
        gespielt = g.findtext("played", "0") == "1"

        # Ergebnis nur wenn gespielt
        if gespielt and mwh != "" and mwa != "":
            ergebnis = f"{mwh}:{mwa}"
        else:
            ergebnis = ""

        # Spieler dieses Teams aus dem game-Element
        spieler = []
        for p in g.findall("player"):
            if p.findtext("team_id", "") == t["tid"]:
                spieler.append({
                    "id":          p.findtext("id", ""),
                    "vorname":     p.findtext("first_name", ""),
                    "nachname":    p.findtext("last_name", ""),
                    "siege":       p.findtext("matches_won", ""),
                    "niederlagen": p.findtext("matches_lost", ""),
                })

        games.append({
            "game_id":  g.findtext("game_id", ""),
            "runde":    g.findtext("round_nr", ""),
            "datum":    g.findtext("date", ""),
            "uhrzeit":  g.findtext("time", ""),
            "heim":     heim,
            "heim_id":  heim_id,
            "gast":     gast,
            "gast_id":  gast_id,
            "ergebnis": ergebnis,   # immer im Format Heim:Gast
            "gespielt": gespielt,
            "spieler":  spieler,
        })
    return games

def get_game_details(game_id, host):
    """
    getGameDetails: Einzelspiel-Ergebnisse (Einzel/Doppel).
    Nur aufrufen wenn getLeagueResults keine Einzeldetails liefert.
    """
    url = api_url(host, "getGameDetails", {"gameId": game_id})
    root = fetch_xml(url)
    if root is None:
        return []

    details = []
    for m in root.iter("match"):
        details.append({
            "pos":          m.findtext("pos", ""),
            "heim_spieler": m.findtext("home_player", "") or m.findtext("homeplayer", ""),
            "gast_spieler": m.findtext("guest_player", "") or m.findtext("guestplayer", ""),
            "saetze_heim":  m.findtext("home_score", "") or m.findtext("homescore", ""),
            "saetze_gast":  m.findtext("guest_score", "") or m.findtext("guestscore", ""),
            "sieger":       m.findtext("winner", ""),
        })
    return details

def get_league_table(team_key):
    """
    getTeamStandings: Ligatabelle mit Platz und Punkten.
    XML-Felder (verifiziert): <standing_row> mit <rank>, <team_id>,
      <team_short_name>, <team_code>, <games_played>, <games_won>,
      <games_drawn>, <games_lost>, <matches_won>, <matches_lost>,
      <sets_won>, <sets_lost>, <points>
    """
    t = TEAMS[team_key]
    url = api_url(t["host"], "getTeamStandings", {"leagueId": t["lid"]})
    root = fetch_xml(url)
    if root is None:
        return []

    table = []
    for row in root.findall(".//standing_row"):
        table.append({
            "platz":        row.findtext("rank", ""),
            "team":         row.findtext("team_short_name", ""),
            "team_id":      row.findtext("team_id", ""),
            "team_code":    row.findtext("team_code", ""),
            "sp":           row.findtext("games_played", ""),
            "s":            row.findtext("games_won", ""),
            "u":            row.findtext("games_drawn", ""),
            "n":            row.findtext("games_lost", ""),
            "spiele_s":     row.findtext("matches_won", ""),
            "spiele_n":     row.findtext("matches_lost", ""),
            "saetze_s":     row.findtext("sets_won", ""),
            "saetze_n":     row.findtext("sets_lost", ""),
            "punkte":       row.findtext("points", ""),
        })
    return table

# ── Hauptprogramm ─────────────────────────────────────────────────────────────

def fetch_all():
    data = {
        "stand": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
        "teams": {}
    }

    for team_key in TEAMS:
        t = TEAMS[team_key]
        print(f"\n── {team_key} ({t['liga']}) ──")

        games = get_league_results(team_key)
        print(f"  {len(games)} Spiele gefunden")

        table = get_league_table(team_key)
        print(f"  {len(table)} Teams in Tabelle")

        data["teams"][team_key] = {
            "tid":     t["tid"],
            "spiele":  games,
            "tabelle": table,
        }

    return data

def main():
    force = "--force" in sys.argv

    if not force and cache_fresh():
        print(f"Cache frisch (< {CACHE_MAX_AGE_HOURS}h) — verwende Cache.")
        print("Mit --force neu laden.")
        data = load_cache()
    else:
        print("Lade Daten von XTTV API ...")
        data = fetch_all()
        save_cache(data)

    # Zusammenfassung
    print(f"\n── Zusammenfassung (Stand: {data['stand']}) ──")
    for team_key, td in data["teams"].items():
        tid = td.get("tid", TEAMS[team_key]["tid"])
        gespielt = [g for g in td["spiele"] if g.get("gespielt")]
        print(f"  {team_key}: {len(gespielt)} gespielte Runden")
        for g in gespielt:
            doeb_heim = g.get("heim_id", "") == tid
            if doeb_heim:
                score  = g["ergebnis"]
                gegner = g["gast"]
                ort    = "H"
            else:
                parts  = g["ergebnis"].split(":")
                score  = f"{parts[1]}:{parts[0]}" if len(parts) == 2 else g["ergebnis"]
                gegner = g["heim"]
                ort    = "A"
            print(f"    R{g['runde']}: vs {gegner}  {score} ({ort})")

    return data

if __name__ == "__main__":
    main()
