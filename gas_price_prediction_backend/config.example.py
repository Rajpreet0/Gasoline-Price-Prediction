from pathlib import Path

# ---------------------------------------------------------------------------
# Tankerkoenig  —  https://creativecommons.tankerkoenig.de
# ---------------------------------------------------------------------------
TANKERKOENIG_API_KEY = "YOUR_API_KEY_HERE"
TANKERKOENIG_BASE_URL = "https://creativecommons.tankerkoenig.de/json"

# Default location (Frankfurt-Ost)
DEFAULT_LAT = 50.084241
DEFAULT_LNG = 8.940342
DEFAULT_RADIUS_KM = 5.0

# ---------------------------------------------------------------------------
# Pegelonline
# ---------------------------------------------------------------------------
PEGEL_KAUB_UUID = "1d26e504-7f9e-480a-b52c-5932be6549ab"
PEGEL_HISTORISCH_MW = 210
PEGEL_KRITISCH = 80
PEGEL_NIEDRIG = 130
PEGEL_NORMAL = 200

# ---------------------------------------------------------------------------
# CO2 / nEHS
# ---------------------------------------------------------------------------
CO2_PRO_LITER = {
    "benzin": 2.37,
    "diesel": 2.65,
}

# ---------------------------------------------------------------------------
# Market data (yfinance tickers)
# ---------------------------------------------------------------------------
TICKER_CONFIG = {
    "eur_usd": ("EURUSD=X", "EUR/USD",  "USD"),
    "brent":   ("BZ=F",     "Brent Öl", "USD/bbl"),
    "wti":     ("CL=F",     "WTI Öl",  "USD/bbl"),
}

# ---------------------------------------------------------------------------
# Collection interval
# ---------------------------------------------------------------------------
COLLECTION_INTERVAL_SEC = 3600

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
DB_PATH = str(Path(__file__).parent / "data" / "gasoline.db")
