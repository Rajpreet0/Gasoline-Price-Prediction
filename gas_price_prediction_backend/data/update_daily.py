"""
Lädt fehlende Tage von Tankerkoenig und schreibt Tages-Aggregate in gasoline_daily.db.
Startet automatisch ab dem letzten gespeicherten Datum.

Ausführen: python -m data.update_daily
"""

import sqlite3
import httpx
import csv
import io
import os
from datetime import date, timedelta
from statistics import mean, median
from pathlib import Path

DB_PATH = str(Path(__file__).parent / "gasoline_daily.db")
GITEA_USER = "rajpreet.singh_gmx.de"
GITEA_PASS = "7859d950-977e-bd11-9170-3dc86af3d070"
BASE_URL   = "https://data.tankerkoenig.de/tankerkoenig-organization/tankerkoenig-data/raw/branch/master/prices"
START_DATE = date(2022, 1, 1)


def init_db(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_prices (
            date          TEXT PRIMARY KEY,
            e5_mean       REAL,
            e5_median     REAL,
            e5_min        REAL,
            e5_max        REAL,
            e10_mean      REAL,
            e10_median    REAL,
            e10_min       REAL,
            e10_max       REAL,
            diesel_mean   REAL,
            diesel_median REAL,
            diesel_min    REAL,
            diesel_max    REAL,
            n_stations    INTEGER
        )
    """)
    conn.commit()
    return conn


def fetch_csv(d: date) -> str | None:
    url = f"{BASE_URL}/{d.year}/{d.month:02d}/{d}-prices.csv"
    try:
        r = httpx.get(url, auth=(GITEA_USER, GITEA_PASS), timeout=60)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print(f"  Fehler bei {d}: {e}")
    return None


def aggregate_csv(text: str):
    e5_vals, e10_vals, diesel_vals = [], [], []
    stations = set()

    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        try:
            sid = row.get("station_uuid") or row.get("stationuuid") or row.get("uuid", "")
            stations.add(sid)
            e5     = float(row["e5"])     if row.get("e5")     and row["e5"]     != "0" else None
            e10    = float(row["e10"])    if row.get("e10")    and row["e10"]    != "0" else None
            diesel = float(row["diesel"]) if row.get("diesel") and row["diesel"] != "0" else None
            if e5     and 0.5 < e5     < 4.0: e5_vals.append(e5)
            if e10    and 0.5 < e10    < 4.0: e10_vals.append(e10)
            if diesel and 0.5 < diesel < 4.0: diesel_vals.append(diesel)
        except (ValueError, KeyError):
            continue

    if not e5_vals:
        return None

    return {
        "e5_mean":       round(mean(e5_vals), 4),
        "e5_median":     round(median(e5_vals), 4),
        "e5_min":        round(min(e5_vals), 4),
        "e5_max":        round(max(e5_vals), 4),
        "e10_mean":      round(mean(e10_vals), 4)    if e10_vals    else None,
        "e10_median":    round(median(e10_vals), 4)  if e10_vals    else None,
        "e10_min":       round(min(e10_vals), 4)     if e10_vals    else None,
        "e10_max":       round(max(e10_vals), 4)     if e10_vals    else None,
        "diesel_mean":   round(mean(diesel_vals), 4)   if diesel_vals else None,
        "diesel_median": round(median(diesel_vals), 4) if diesel_vals else None,
        "diesel_min":    round(min(diesel_vals), 4)    if diesel_vals else None,
        "diesel_max":    round(max(diesel_vals), 4)    if diesel_vals else None,
        "n_stations":    len(stations),
    }


def main():
    conn = init_db(DB_PATH)

    # Letztes gespeichertes Datum ermitteln
    last = conn.execute("SELECT MAX(date) FROM daily_prices").fetchone()[0]
    start = date.fromisoformat(last) + timedelta(days=1) if last else START_DATE
    end   = date.today() - timedelta(days=1)

    if start > end:
        print(f"DB ist aktuell (bis {last}). Nichts zu tun.")
        return

    days = []
    d = start
    while d <= end:
        days.append(d)
        d += timedelta(days=1)

    print(f"DB aktuell bis: {last}")
    print(f"Lade {len(days)} fehlende Tage ({start} bis {end})...")

    inserted = skipped = errors = 0

    for i, d in enumerate(days):
        pct = (i + 1) / len(days) * 100
        text = fetch_csv(d)

        if text is None:
            skipped += 1
            print(f"[{i+1:4d}/{len(days)}] {d} keine Daten")
            continue

        agg = aggregate_csv(text)
        if agg is None:
            errors += 1
            print(f"[{i+1:4d}/{len(days)}] {d} Aggregat fehlgeschlagen")
            continue

        conn.execute("""
            INSERT OR IGNORE INTO daily_prices VALUES
            (:date,:e5_mean,:e5_median,:e5_min,:e5_max,
             :e10_mean,:e10_median,:e10_min,:e10_max,
             :diesel_mean,:diesel_median,:diesel_min,:diesel_max,
             :n_stations)
        """, {"date": str(d), **agg})
        conn.commit()
        inserted += 1

        print(f"[{i+1:4d}/{len(days)}] {d} e5={agg['e5_mean']} diesel={agg['diesel_mean']} n={agg['n_stations']} ({pct:.1f}%)")

    print(f"\nFertig! Inserted: {inserted}, Skipped: {skipped}, Errors: {errors}")

    count, mn, mx = conn.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM daily_prices").fetchone()
    print(f"DB: {count} Zeilen, {mn} bis {mx}")


if __name__ == "__main__":
    main()
