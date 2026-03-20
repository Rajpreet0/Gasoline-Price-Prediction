"""
features.py – Wandelt einen RawSnapshot in einen flachen ML-Feature-Vektor um.

Aufruf:
    from data.features import build_features
    features = build_features(snapshot)   # -> dict[str, float | int | str]
"""

import statistics
from datetime import datetime, timezone

from config import (
    PEGEL_HISTORISCH_MW,
    PEGEL_KRITISCH,
    PEGEL_NIEDRIG,
    PEGEL_NORMAL,
    CO2_PRO_LITER,
    REGIONAL_WEIGHTS,
)


# ---------------------------------------------------------------------------
# Pegel
# ---------------------------------------------------------------------------

def _klassifiziere_pegel(wert: float) -> str:
    if wert <= PEGEL_KRITISCH:
        return "KRITISCH"
    elif wert <= PEGEL_NIEDRIG:
        return "NIEDRIG"
    elif wert <= PEGEL_NORMAL:
        return "EINGESCHRAENKT"
    return "NORMAL"


def _pegel_features(pegel_raw: dict) -> dict:
    messungen  = pegel_raw.get("messungen", [])
    vorhersage = pegel_raw.get("vorhersage", [])

    if not messungen:
        return {"pegel_aktuell_cm": None}

    werte = [m["value"] for m in messungen]
    aktuell = werte[-1]

    features = {
        "pegel_aktuell_cm":       aktuell,
        "pegel_min_cm":           min(werte),
        "pegel_max_cm":           max(werte),
        "pegel_mittel_cm":        round(statistics.mean(werte), 2),
        "pegel_std_cm":           round(statistics.stdev(werte), 2) if len(werte) > 1 else 0.0,
        "pegel_trend_3d_cm":      round(aktuell - werte[0], 2),
        "pegel_trend_1d_cm":      round(aktuell - werte[-9], 2) if len(werte) >= 9 else 0.0,
        "pegel_volatilitaet_cm":  round(max(werte) - min(werte), 2),
        "pegel_normalisiert":     round(aktuell / PEGEL_HISTORISCH_MW, 4),
        "pegel_abweichung_mw_cm": round(aktuell - PEGEL_HISTORISCH_MW, 2),
        "pegel_status":           _klassifiziere_pegel(aktuell),
        "ist_kritisch":           int(aktuell <= PEGEL_KRITISCH),
        "ist_niedrig":            int(aktuell <= PEGEL_NIEDRIG),
    }

    if vorhersage:
        vhs = [m["value"] for m in vorhersage]
        features.update({
            "pegel_vhs_morgen_cm": vhs[0],
            "pegel_vhs_min_cm":    min(vhs),
            "pegel_vhs_max_cm":    max(vhs),
            "pegel_vhs_trend_cm":  round(vhs[-1] - vhs[0], 2),
            "pegel_vhs_kritisch":  int(any(v <= PEGEL_KRITISCH for v in vhs)),
            "pegel_vhs_niedrig":   int(any(v <= PEGEL_NIEDRIG for v in vhs)),
        })

    return features


# ---------------------------------------------------------------------------
# Tankstellenpreise
# ---------------------------------------------------------------------------

def _preis_features(tankstellen: list[dict]) -> dict:
    if not tankstellen:
        return {}

    offene = [s for s in tankstellen if s.get("isOpen")]

    def _stats(key: str, quelle: list[dict]) -> dict:
        werte = [s[key] for s in quelle if s.get(key)]
        if not werte:
            return {}
        return {
            f"{key}_min":    round(min(werte), 3),
            f"{key}_max":    round(max(werte), 3),
            f"{key}_mittel": round(statistics.mean(werte), 3),
            f"{key}_median": round(statistics.median(werte), 3),
        }

    features = {"anzahl_stationen": len(tankstellen), "anzahl_offen": len(offene)}
    for sorte in ("e5", "e10", "diesel"):
        features.update(_stats(sorte, offene))

    return features


# ---------------------------------------------------------------------------
# CO2-Aufschlag
# ---------------------------------------------------------------------------

def _co2_features(co2_preis: float | None) -> dict:
    if co2_preis is None:
        return {"co2_preis_eur_t": None}
    return {
        "co2_preis_eur_t":         round(co2_preis, 2),
        "co2_aufschlag_benzin_ct": round((co2_preis * CO2_PRO_LITER["benzin"]) / 10, 4),
        "co2_aufschlag_diesel_ct": round((co2_preis * CO2_PRO_LITER["diesel"]) / 10, 4),
    }


# ---------------------------------------------------------------------------
# Marktdaten
# ---------------------------------------------------------------------------

def _markt_features(marktdaten: dict) -> dict:
    features = {}
    for key in ("eur_usd", "brent", "wti"):
        eintrag = marktdaten.get(key) or {}
        features[key] = eintrag.get("wert")
    return features


# ---------------------------------------------------------------------------
# Wetter
# ---------------------------------------------------------------------------

def _wetter_features(wetter: dict) -> dict:
    return {
        "temperatur":           wetter.get("temperatur"),
        "gefuehlte_temperatur": wetter.get("gefuehlte_temperatur"),
        "niederschlag":         wetter.get("niederschlag"),
        "windgeschwindigkeit":  wetter.get("windgeschwindigkeit"),
        "wettercode":           wetter.get("wettercode"),
    }


# ---------------------------------------------------------------------------
# Kalender-Features (Feiertage / Ferien / Wochentag)
# ---------------------------------------------------------------------------

def _kalender_features(
    feiertage: dict,
    ferien: list[dict],
    bundesland: str,
    collected_at: str,
) -> dict:
    try:
        now = datetime.fromisoformat(collected_at)
    except Exception:
        now = datetime.now(timezone.utc)

    heute = now.date()
    heute_str = heute.isoformat()

    ist_feiertag = int(any(
        info.get("datum") == heute_str
        for info in feiertage.values()
    ))

    ist_ferien = 0
    for eintrag in ferien:
        if eintrag.get("stateCode", "").upper() != bundesland.upper():
            continue
        try:
            start = datetime.fromisoformat(eintrag["start"].replace("Z", "+00:00")).date()
            end   = datetime.fromisoformat(eintrag["end"].replace("Z", "+00:00")).date()
            if start <= heute <= end:
                ist_ferien = 1
                break
        except Exception:
            continue

    return {
        "wochentag":   now.weekday(),       # 0=Mo … 6=So
        "ist_wochenende": int(now.weekday() >= 5),
        "monat":       now.month,
        "jahreszeit":  (now.month % 12) // 3 + 1,   # 1=Winter … 4=Herbst
        "ist_feiertag": ist_feiertag,
        "ist_ferien":   ist_ferien,
    }


# ---------------------------------------------------------------------------
# Regionales Gewicht Pegelstand
# ---------------------------------------------------------------------------

def _regional_weight(bundesland: str) -> float:
    nord   = {"HH", "HB", "SH", "MV", "NI"}
    sued   = {"BY", "BW", "RP", "SL", "SN", "TH", "ST"}
    if bundesland in nord:
        return REGIONAL_WEIGHTS["nord"]
    elif bundesland in sued:
        return REGIONAL_WEIGHTS["sued"]
    return REGIONAL_WEIGHTS["mitte"]


# ---------------------------------------------------------------------------
# Haupt-Funktion
# ---------------------------------------------------------------------------

def build_features(snapshot: dict) -> dict:
    """
    Gibt einen flachen Feature-Vektor zurück, der direkt als
    Trainings- oder Inferenzzeile verwendet werden kann.
    """
    standort   = snapshot.get("standort", {})
    bundesland = standort.get("bundesland", "HE")

    features: dict = {"collected_at": snapshot.get("collected_at")}

    features.update(_pegel_features(snapshot.get("pegel", {})))
    features.update(_preis_features(snapshot.get("tankstellen", [])))
    features.update(_co2_features(snapshot.get("co2_preis")))
    features.update(_markt_features(snapshot.get("marktdaten", {})))
    features.update(_wetter_features(snapshot.get("wetter", {})))
    features.update(_kalender_features(
        snapshot.get("feiertage", {}),
        snapshot.get("ferien", []),
        bundesland,
        snapshot.get("collected_at", ""),
    ))
    features["pegel_regional_weight"] = _regional_weight(bundesland)

    return features


if __name__ == "__main__":
    import json
    import asyncio
    from data.collector import collect_snapshot

    snapshot = asyncio.run(collect_snapshot())
    feats = build_features(snapshot)
    print(json.dumps(feats, indent=2, ensure_ascii=False, default=str))
