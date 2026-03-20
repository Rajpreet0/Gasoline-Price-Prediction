"""
collector.py – Ruft alle Datenquellen parallel ab und gibt ein einheitliches
RawSnapshot-Dict zurück.

Quellen:
  - Tankerkoenig   (Tankstellenpreise)
  - pegelonline    (Rhein-Pegelstand Kaub)
  - EEX nEHS       (CO2-Preis)
  - feiertage-api  (Feiertage je Bundesland)
  - ferien-api     (Schulferien je Bundesland)
  - open-meteo     (Wetterdaten)
  - yfinance       (EUR/USD, Brent, WTI)
"""

import asyncio
import csv
from datetime import datetime, timezone
from io import StringIO

import httpx
import yfinance as yf

from config import (
    TANKERKOENIG_API_KEY,
    TANKERKOENIG_BASE_URL,
    PEGEL_KAUB_UUID,
    TICKER_CONFIG,
    DEFAULT_LAT,
    DEFAULT_LNG,
    DEFAULT_RADIUS_KM,
)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

async def _get_standort(client: httpx.AsyncClient) -> dict:
    """IP-basierter Standort (Stadt, Lat, Lng, Bundesland-Code)."""
    try:
        r = await client.get("https://ipapi.co/json/")
        r.raise_for_status()
        data = r.json()

        bundesland_map = {
            "Bavaria": "BY", "Berlin": "BE", "Brandenburg": "BB",
            "Bremen": "HB", "Hamburg": "HH", "Hesse": "HE",
            "Mecklenburg-Vorpommern": "MV", "Lower Saxony": "NI",
            "North Rhine-Westphalia": "NW", "Rhineland-Palatinate": "RP",
            "Saarland": "SL", "Saxony": "SN", "Saxony-Anhalt": "ST",
            "Schleswig-Holstein": "SH", "Thuringia": "TH",
            "Baden-Württemberg": "BW",
        }
        region = data.get("region", "")
        return {
            "stadt":      data.get("city", ""),
            "latitude":   data.get("latitude", DEFAULT_LAT),
            "longitude":  data.get("longitude", DEFAULT_LNG),
            "bundesland": bundesland_map.get(region, "HE"),
        }
    except Exception:
        return {"stadt": "", "latitude": DEFAULT_LAT, "longitude": DEFAULT_LNG, "bundesland": "HE"}


# ---------------------------------------------------------------------------
# Einzelne Datenquellen
# ---------------------------------------------------------------------------

async def fetch_tankstellen(
    client: httpx.AsyncClient,
    lat: float,
    lng: float,
    radius: float = DEFAULT_RADIUS_KM,
) -> list[dict]:
    try:
        r = await client.get(f"{TANKERKOENIG_BASE_URL}/list.php", params={
            "lat": lat, "lng": lng, "rad": radius,
            "type": "all", "sort": "dist",
            "apikey": TANKERKOENIG_API_KEY,
        })
        r.raise_for_status()
        data = r.json()
        return data.get("stations", []) if data.get("ok") else []
    except Exception as e:
        print(f"[collector] Tankerkoenig Fehler: {e}")
        return []


async def fetch_pegel(client: httpx.AsyncClient) -> dict:
    try:
        ist, vhs = await asyncio.gather(
            client.get(
                f"https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/"
                f"{PEGEL_KAUB_UUID}/W/measurements.json",
                params={"start": "P3D"},
            ),
            client.get(
                f"https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/"
                f"{PEGEL_KAUB_UUID}/WV/measurements.json",
                params={"start": "P0D"},
            ),
        )
        ist.raise_for_status()
        vhs.raise_for_status()
        return {"messungen": ist.json(), "vorhersage": vhs.json()}
    except Exception as e:
        print(f"[collector] Pegel Fehler: {e}")
        return {"messungen": [], "vorhersage": []}


async def fetch_co2_preis(client: httpx.AsyncClient) -> float | None:
    try:
        r = await client.get(
            "https://public.eex-group.com/eex/nehs-reporting/nEHS_Reporting.csv"
        )
        r.raise_for_status()
        zeilen = r.text.splitlines()
        reader = csv.DictReader(StringIO("\n".join(zeilen[2:])), delimiter=";")
        rows = [row for row in reader if row.get("Datum/Date")]
        if rows:
            return float(rows[0]["Verkaufspreis/Price €/tCO2"].replace(",", "."))
    except Exception as e:
        print(f"[collector] CO2 Fehler: {e}")
    return None


async def fetch_feiertage(client: httpx.AsyncClient, bundesland: str) -> dict:
    try:
        jahr = datetime.now().year
        r = await client.get(
            "https://feiertage-api.de/api/",
            params={"jahr": str(jahr), "nur_land": bundesland},
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[collector] Feiertage Fehler: {e}")
        return {}


async def fetch_ferien(client: httpx.AsyncClient) -> list[dict]:
    try:
        jahr = datetime.now().year
        r = await client.get(f"https://ferien-api.maxleistner.de/api/v1/{jahr}")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[collector] Ferien Fehler: {e}")
        return []


async def fetch_wetter(client: httpx.AsyncClient, lat: float, lng: float) -> dict:
    try:
        r = await client.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lng,
            "current": [
                "temperature_2m", "precipitation", "weathercode",
                "windspeed_10m", "apparent_temperature",
            ],
            "timezone": "Europe/Berlin",
            "forecast_days": 1,
        })
        r.raise_for_status()
        aktuell = r.json()["current"]
        return {
            "temperatur":           aktuell["temperature_2m"],
            "gefuehlte_temperatur": aktuell["apparent_temperature"],
            "niederschlag":         aktuell["precipitation"],
            "windgeschwindigkeit":  aktuell["windspeed_10m"],
            "wettercode":           aktuell["weathercode"],
            "zeitpunkt":            aktuell["time"],
        }
    except Exception as e:
        print(f"[collector] Wetter Fehler: {e}")
        return {}


def fetch_marktdaten() -> dict:
    result = {}
    for key, (ticker_symbol, name, einheit) in TICKER_CONFIG.items():
        try:
            wert = yf.Ticker(ticker_symbol).fast_info["last_price"]
            result[key] = {"name": name, "wert": wert, "einheit": einheit}
        except Exception as e:
            print(f"[collector] Marktdaten {name} Fehler: {e}")
            result[key] = None
    return result


# ---------------------------------------------------------------------------
# Haupt-Collector
# ---------------------------------------------------------------------------

async def collect_snapshot() -> dict:
    """
    Ruft alle Datenquellen parallel ab.
    Gibt ein RawSnapshot-Dict zurück mit Schlüsseln:
      collected_at, standort, tankstellen, pegel, co2_preis,
      feiertage, ferien, wetter, marktdaten
    """
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        standort = await _get_standort(client)

        (
            tankstellen,
            pegel,
            co2_preis,
            feiertage,
            ferien,
            wetter,
        ) = await asyncio.gather(
            fetch_tankstellen(client, standort["latitude"], standort["longitude"]),
            fetch_pegel(client),
            fetch_co2_preis(client),
            fetch_feiertage(client, standort["bundesland"]),
            fetch_ferien(client),
            fetch_wetter(client, standort["latitude"], standort["longitude"]),
        )

    # yfinance ist synchron → außerhalb des async-Blocks
    marktdaten = fetch_marktdaten()

    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "standort":     standort,
        "tankstellen":  tankstellen,
        "pegel":        pegel,
        "co2_preis":    co2_preis,
        "feiertage":    feiertage,
        "ferien":       ferien,
        "wetter":       wetter,
        "marktdaten":   marktdaten,
    }


if __name__ == "__main__":
    import json
    snapshot = asyncio.run(collect_snapshot())
    print(json.dumps(snapshot, indent=2, ensure_ascii=False, default=str))
