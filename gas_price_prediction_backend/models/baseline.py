"""
Baseline XGBoost model: 1-day forecast for E5, E10, Diesel.

Usage:
  python -m models.baseline          # train + evaluate
  python -m models.baseline --predict # predict tomorrow
"""
import argparse
import sqlite3
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yfinance as yf
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

DB_PATH = Path(__file__).parent.parent / "data" / "gasoline_daily.db"
MODEL_DIR = Path(__file__).parent / "saved"
TARGETS = ["e5_mean", "e10_mean", "diesel_mean"]
TEST_DAYS = 90


# ── Data loading ──────────────────────────────────────────────────────────────

def load_prices() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM daily_prices ORDER BY date", conn, parse_dates=["date"])
    conn.close()
    df = df.set_index("date")
    return df


def load_brent_eurusd(start: str, end: str) -> pd.DataFrame:
    """Download Brent and EUR/USD from Yahoo Finance."""
    raw_brent  = yf.download("BZ=F",     start=start, end=end, progress=False, auto_adjust=True)
    raw_eurusd = yf.download("EURUSD=X", start=start, end=end, progress=False, auto_adjust=True)

    # yfinance may return MultiIndex columns — flatten to Series
    def to_series(df):
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close.index = pd.to_datetime(close.index).tz_localize(None)
        return close

    brent  = to_series(raw_brent)
    eurusd = to_series(raw_eurusd)

    mkt = pd.DataFrame({"brent": brent, "eurusd": eurusd})
    # Forward-fill weekends/holidays
    full_idx = pd.date_range(mkt.index.min(), mkt.index.max(), freq="D")
    mkt = mkt.reindex(full_idx).ffill()
    return mkt


# ── Feature engineering ───────────────────────────────────────────────────────

def build_features(df: pd.DataFrame, mkt: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Join market data
    df = df.join(mkt, how="left")
    df[["brent", "eurusd"]] = df[["brent", "eurusd"]].ffill()

    # Calendar features
    df["dow"] = df.index.dayofweek          # 0=Mon, 6=Sun
    df["month"] = df.index.month
    df["is_weekend"] = (df["dow"] >= 5).astype(int)

    # Lag features (yesterday, 2d ago, 7d ago)
    for fuel in TARGETS:
        for lag in [1, 2, 7]:
            df[f"{fuel}_lag{lag}"] = df[fuel].shift(lag)
        # 7-day rolling mean
        df[f"{fuel}_roll7"] = df[fuel].shift(1).rolling(7).mean()
        # 1-day change
        df[f"{fuel}_delta1"] = df[fuel].shift(1) - df[fuel].shift(2)

    # Brent lag + rolling
    df["brent_lag1"] = df["brent"].shift(1)
    df["brent_roll7"] = df["brent"].shift(1).rolling(7).mean()
    df["brent_delta1"] = df["brent"].shift(1) - df["brent"].shift(2)
    df["eurusd_lag1"] = df["eurusd"].shift(1)

    df = df.dropna()
    return df


def get_feature_cols() -> list[str]:
    cols = ["dow", "month", "is_weekend",
            "brent_lag1", "brent_roll7", "brent_delta1",
            "eurusd_lag1"]
    for fuel in TARGETS:
        cols += [
            f"{fuel}_lag1", f"{fuel}_lag2", f"{fuel}_lag7",
            f"{fuel}_roll7", f"{fuel}_delta1",
        ]
    return cols


# ── Train / evaluate ──────────────────────────────────────────────────────────

def train_and_evaluate(df: pd.DataFrame):
    feature_cols = get_feature_cols()

    split = len(df) - TEST_DAYS
    train = df.iloc[:split]
    test  = df.iloc[split:]

    print(f"Train: {train.index[0].date()} – {train.index[-1].date()} ({len(train)} days)")
    print(f"Test:  {test.index[0].date()}  – {test.index[-1].date()}  ({len(test)} days)")
    print()

    MODEL_DIR.mkdir(exist_ok=True)
    models = {}

    for target in TARGETS:
        X_train = train[feature_cols]
        y_train = train[target]
        X_test  = test[feature_cols]
        y_test  = test[target]

        model = XGBRegressor(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
        )
        model.fit(X_train, y_train,
                  eval_set=[(X_test, y_test)],
                  verbose=False)

        preds = model.predict(X_test)
        mae  = mean_absolute_error(y_test, preds)
        rmse = root_mean_squared_error(y_test, preds)

        print(f"{target:12s}  MAE={mae*100:.2f} ct  RMSE={rmse*100:.2f} ct")

        joblib.dump(model, MODEL_DIR / f"{target}.joblib")
        models[target] = model

    return models


# ── Predict tomorrow ──────────────────────────────────────────────────────────

def predict_tomorrow(df: pd.DataFrame):
    feature_cols = get_feature_cols()
    last_row = df.iloc[[-1]][feature_cols]

    print(f"\nVorhersage für morgen ({df.index[-1].date() + pd.Timedelta(days=1)}):\n")
    for target in TARGETS:
        model_path = MODEL_DIR / f"{target}.joblib"
        if not model_path.exists():
            print(f"  {target}: Kein Modell gefunden, bitte zuerst trainieren.")
            continue
        model = joblib.load(model_path)
        pred = model.predict(last_row)[0]
        current = df[target].iloc[-1]
        diff = pred - current
        arrow = "+" if diff > 0 else "-"
        print(f"  {target:12s}: {pred:.4f} EUR/L  ({arrow}{abs(diff)*100:.2f} ct vs heute {current:.4f})")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predict", action="store_true", help="Predict tomorrow using saved models")
    args = parser.parse_args()

    print("Lade Preisdaten...")
    prices = load_prices()

    print("Lade Marktdaten (Brent, EUR/USD)...")
    start = str(prices.index.min().date())
    end   = str((prices.index.max() + pd.Timedelta(days=1)).date())
    mkt = load_brent_eurusd(start, end)

    print("Feature Engineering...")
    df = build_features(prices, mkt)
    print(f"Datensatz: {len(df)} Tage, {len(get_feature_cols())} Features\n")

    if args.predict:
        predict_tomorrow(df)
    else:
        train_and_evaluate(df)
        predict_tomorrow(df)


if __name__ == "__main__":
    main()
