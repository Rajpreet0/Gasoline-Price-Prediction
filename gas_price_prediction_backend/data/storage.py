"""
storage.py – SQLite-Speicherung der gesammelten Snapshots.

Schema:
  snapshots   – ein Eintrag pro collect_snapshot()-Aufruf (JSON-Blob + Metadaten)
  prices      – normalisierte Tankstellenpreise (für ML-Training)
"""

import json
import sqlite3

from pathlib import Path

from config import DB_PATH


def _connect() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Fügt fehlende Spalten zu bestehenden Tabellen hinzu (idempotent)."""
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(prices)").fetchall()
    }
    migrations = [
        ("e5change",     "ALTER TABLE prices ADD COLUMN e5change     INTEGER"),
        ("e10change",    "ALTER TABLE prices ADD COLUMN e10change    INTEGER"),
        ("dieselchange", "ALTER TABLE prices ADD COLUMN dieselchange INTEGER"),
        ("source",       "ALTER TABLE prices ADD COLUMN source       TEXT DEFAULT 'live'"),
    ]
    for col, sql in migrations:
        if col not in existing:
            conn.execute(sql)

    # Neue Indizes anlegen falls fehlend (IF NOT EXISTS macht das sicher)
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_prices_source
            ON prices(source);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_unique
            ON prices(collected_at, station_id);
    """)


def init_db() -> None:
    """Erstellt alle Tabellen falls nicht vorhanden."""
    with _connect() as conn:
        # Migration zuerst, damit ALTER TABLE vor den Index-Statements läuft
        _migrate(conn)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                collected_at TEXT    NOT NULL,
                stadt        TEXT,
                bundesland   TEXT,
                latitude     REAL,
                longitude    REAL,
                co2_preis    REAL,
                eur_usd      REAL,
                brent        REAL,
                wti          REAL,
                temperatur   REAL,
                niederschlag REAL,
                windgeschwindigkeit REAL,
                wettercode   INTEGER,
                pegel_aktuell REAL,
                raw_json     TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS prices (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id  INTEGER REFERENCES snapshots(id),  -- NULL bei historischen Importen
                collected_at TEXT    NOT NULL,
                station_id   TEXT    NOT NULL,
                station_name TEXT,
                lat          REAL,
                lng          REAL,
                dist_km      REAL,
                is_open      INTEGER,
                e5           REAL,
                e10          REAL,
                diesel       REAL,
                e5change     INTEGER,  -- 0=keine Änderung, 1=Änderung, 2=Entfernt, 3=Neu
                e10change    INTEGER,
                dieselchange INTEGER,
                source       TEXT DEFAULT 'live'  -- 'live' oder 'historical'
            );

            CREATE INDEX IF NOT EXISTS idx_prices_collected_at
                ON prices(collected_at);
            CREATE INDEX IF NOT EXISTS idx_prices_station_id
                ON prices(station_id);
            CREATE INDEX IF NOT EXISTS idx_prices_source
                ON prices(source);

            -- Deduplizierung: gleicher Zeitstempel + Station nur einmal
            CREATE UNIQUE INDEX IF NOT EXISTS idx_prices_unique
                ON prices(collected_at, station_id);
        """)


def save_snapshot(snapshot: dict) -> int:
    """
    Speichert einen RawSnapshot aus collector.collect_snapshot().
    Gibt die neue snapshot-ID zurück.
    """
    standort   = snapshot.get("standort", {})
    marktdaten = snapshot.get("marktdaten", {})
    wetter     = snapshot.get("wetter", {})
    pegel      = snapshot.get("pegel", {})

    # Pegelstand: letzter Messwert
    messungen = pegel.get("messungen", [])
    pegel_aktuell = messungen[-1]["value"] if messungen else None

    # Marktpreise
    eur_usd = marktdaten.get("eur_usd", {}) or {}
    brent   = marktdaten.get("brent",   {}) or {}
    wti     = marktdaten.get("wti",     {}) or {}

    with _connect() as conn:
        cur = conn.execute("""
            INSERT INTO snapshots (
                collected_at, stadt, bundesland, latitude, longitude,
                co2_preis, eur_usd, brent, wti,
                temperatur, niederschlag, windgeschwindigkeit, wettercode,
                pegel_aktuell, raw_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            snapshot.get("collected_at"),
            standort.get("stadt"),
            standort.get("bundesland"),
            standort.get("latitude"),
            standort.get("longitude"),
            snapshot.get("co2_preis"),
            eur_usd.get("wert"),
            brent.get("wert"),
            wti.get("wert"),
            wetter.get("temperatur"),
            wetter.get("niederschlag"),
            wetter.get("windgeschwindigkeit"),
            wetter.get("wettercode"),
            pegel_aktuell,
            json.dumps(snapshot, ensure_ascii=False, default=str),
        ))
        snapshot_id = cur.lastrowid

        # Tankstellenpreise normalisiert speichern
        stationen = snapshot.get("tankstellen", [])
        if stationen:
            conn.executemany("""
                INSERT OR IGNORE INTO prices (
                    snapshot_id, collected_at, station_id, station_name,
                    lat, lng, dist_km, is_open, e5, e10, diesel, source
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,'live')
            """, [
                (
                    snapshot_id,
                    snapshot.get("collected_at"),
                    s.get("id"),
                    s.get("name"),
                    s.get("lat"),
                    s.get("lng"),
                    s.get("dist"),
                    int(bool(s.get("isOpen"))),
                    s.get("e5"),
                    s.get("e10"),
                    s.get("diesel"),
                )
                for s in stationen
            ])

    return snapshot_id


def load_snapshots(limit: int = 100) -> list[dict]:
    """Letzte `limit` Snapshots als Liste von Dicts (ohne raw_json)."""
    with _connect() as conn:
        rows = conn.execute("""
            SELECT id, collected_at, stadt, bundesland,
                   co2_preis, eur_usd, brent, wti,
                   temperatur, niederschlag, pegel_aktuell
            FROM snapshots
            ORDER BY collected_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def load_prices(station_id: str | None = None, limit: int = 500) -> list[dict]:
    """Preishistorie — optional gefiltert nach station_id."""
    with _connect() as conn:
        if station_id:
            rows = conn.execute("""
                SELECT * FROM prices
                WHERE station_id = ?
                ORDER BY collected_at DESC
                LIMIT ?
            """, (station_id, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM prices
                ORDER BY collected_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    print(f"Datenbank initialisiert: {DB_PATH}")
