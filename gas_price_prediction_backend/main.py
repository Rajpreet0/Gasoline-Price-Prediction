"""
main.py – Entry-Point für die Datensammlung.

Verwendung:
    python main.py            # einmalig sammeln
    python main.py --loop     # dauerhaft alle COLLECTION_INTERVAL_SEC Sekunden
"""

import argparse
import asyncio

from config import COLLECTION_INTERVAL_SEC
from data.collector import collect_snapshot
from data.features import build_features
from data.storage import init_db, save_snapshot


async def run_once(verbose: bool = True) -> dict:
    print("[main] Starte Datensammlung …")
    snapshot = await collect_snapshot()

    snapshot_id = save_snapshot(snapshot)
    features    = build_features(snapshot)

    print(f"[main] Snapshot #{snapshot_id} gespeichert — {snapshot['collected_at']}")
    print(f"[main] Standort: {snapshot['standort'].get('stadt')} ({snapshot['standort'].get('bundesland')})")

    stationen = snapshot.get("tankstellen", [])
    offene = [s for s in stationen if s.get("isOpen")]
    print(f"[main] Tankstellen: {len(stationen)} gefunden, {len(offene)} offen")

    if verbose:
        print("\n--- Feature-Vektor ---")
        for k, v in features.items():
            print(f"  {k:<35} {str(v)}")

    return features


async def run_loop() -> None:
    init_db()
    print(f"[main] Scheduler gestartet — Intervall: {COLLECTION_INTERVAL_SEC}s")
    while True:
        try:
            await run_once(verbose=False)
        except Exception as e:
            print(f"[main] Fehler beim Sammeln: {e}")
        print(f"[main] Warte {COLLECTION_INTERVAL_SEC}s …\n")
        await asyncio.sleep(COLLECTION_INTERVAL_SEC)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gasoline Price Data Collector")
    parser.add_argument("--loop", action="store_true", help="Dauerhaft im Intervall sammeln")
    parser.add_argument("--no-verbose", action="store_true", help="Kein Feature-Dump")
    args = parser.parse_args()

    init_db()

    if args.loop:
        asyncio.run(run_loop())
    else:
        asyncio.run(run_once(verbose=not args.no_verbose))


if __name__ == "__main__":
    main()
