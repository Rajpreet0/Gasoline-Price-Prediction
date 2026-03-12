"use client";

import { useEffect, useRef } from "react";
import { Map, MapMarker, MarkerContent, MarkerPopup, useMap } from "@/components/ui/map";
import { Station } from "../../types";

function FlyToLocation({ lng, lat }: { lng: number; lat: number }) {
    const { map, isLoaded } = useMap();
    const isFirst = useRef(true);

    useEffect(() => {
        if (!map || !isLoaded) return;
        if (isFirst.current) {
            isFirst.current = false;
            return;
        }
        map.flyTo({ center: [lng, lat], zoom: 13, duration: 1200 });
    }, [map, isLoaded, lng, lat]);

    return null;
}

function RadiusCircle({ lng, lat, radiusKm }: { lng: number; lat: number; radiusKm: number }) {
    const { map, isLoaded } = useMap();

    useEffect(() => {
        if (!map || !isLoaded) return;

        // Erzeuge einen Kreis-Polygon via GeoJSON (64 Punkte)
        const points = 64;
        const coords: [number, number][] = [];
        const earthRadius = 6371;
        const latR = (lat * Math.PI) / 180;
        for (let i = 0; i <= points; i++) {
            const angle = (i * 2 * Math.PI) / points;
            const dLat = (radiusKm / earthRadius) * (180 / Math.PI);
            const dLng = dLat / Math.cos(latR);
            coords.push([lng + dLng * Math.sin(angle), lat + dLat * Math.cos(angle)]);
        }

        const sourceId = "radius-circle";
        const fillId = "radius-circle-fill";
        const outlineId = "radius-circle-outline";

        if (map.getSource(sourceId)) {
            map.removeLayer(fillId);
            map.removeLayer(outlineId);
            map.removeSource(sourceId);
        }

        map.addSource(sourceId, {
            type: "geojson",
            data: { type: "Feature", geometry: { type: "Polygon", coordinates: [coords] }, properties: {} },
        });
        map.addLayer({ id: fillId, type: "fill", source: sourceId, paint: { "fill-color": "#3b82f6", "fill-opacity": 0.05 } });
        map.addLayer({ id: outlineId, type: "line", source: sourceId, paint: { "line-color": "#3b82f6", "line-width": 1.5, "line-opacity": 0.6 } });

        return () => {
            if (map.getLayer(fillId)) map.removeLayer(fillId);
            if (map.getLayer(outlineId)) map.removeLayer(outlineId);
            if (map.getSource(sourceId)) map.removeSource(sourceId);
        };
    }, [map, isLoaded, lng, lat, radiusKm]);

    return null;
}

type MapLocation = { lat: number; lng: number };
type Props = { location: MapLocation; stations: Station[] };

function findCheapest(stations: Station[], fuel: "e5" | "e10" | "diesel"): string | null {
    const open = stations.filter((s) => s.isOpen && s[fuel] !== null);
    if (!open.length) return null;
    return open.reduce((a, b) => (a[fuel]! < b[fuel]! ? a : b)).id;
}

function PinIcon({ color }: { color: string }) {
    return (
        <div
            className="relative flex h-7 w-7 items-center justify-center rounded-full border-2 border-white shadow-lg"
            style={{ backgroundColor: color }}
        />
    );
}

function Legend() {
    return (
        <div className="absolute bottom-8 right-2 z-10 bg-background text-foreground rounded-lg shadow-md p-3 text-sm space-y-1.5 pointer-events-none">
            <p className="font-semibold text-xs uppercase text-muted-foreground mb-2">Legende</p>
            <div className="flex items-center gap-2">
                <span className="inline-block w-3 h-3 rounded-full bg-blue-500" />
                <span>Dein Standort</span>
            </div>
            <div className="flex items-center gap-2">
                <span className="inline-block w-3 h-3 rounded-full bg-green-500" />
                <span>Geöffnet</span>
            </div>
            <div className="flex items-center gap-2">
                <span className="inline-block w-3 h-3 rounded-full bg-red-500" />
                <span>Geschlossen</span>
            </div>
            <div className="flex items-center gap-2">
                <span className="inline-block w-3 h-3 rounded-full bg-yellow-400" />
                <span>Günstigste (offen)</span>
            </div>
        </div>
    );
}

export function StationsMap({ location, stations }: Props) {
    const cheapestE5 = findCheapest(stations, "e5");
    const cheapestE10 = findCheapest(stations, "e10");
    const cheapestDiesel = findCheapest(stations, "diesel");

    const isCheapest = (id: string) =>
        id === cheapestE5 || id === cheapestE10 || id === cheapestDiesel;

    return (
        <div className="relative h-125 w-full rounded-lg overflow-hidden">
            <Map
                center={[location.lng, location.lat]}
                zoom={13}
                className="h-125 w-full"
            >
                <FlyToLocation lng={location.lng} lat={location.lat} />
                <RadiusCircle lng={location.lng} lat={location.lat} radiusKm={5} />

                {/* User location marker */}
                <MapMarker longitude={location.lng} latitude={location.lat}>
                    <MarkerContent>
                        <PinIcon color="#3b82f6" />
                    </MarkerContent>
                    <MarkerPopup closeButton>
                        <p className="font-semibold text-sm">Dein Standort</p>
                    </MarkerPopup>
                </MapMarker>

                {/* Station markers */}
                {stations.map((station) => {
                    const cheap = isCheapest(station.id);
                    const color = cheap ? "#eab308" : station.isOpen ? "#22c55e" : "#ef4444";

                    return (
                        <MapMarker key={station.id} longitude={station.lng} latitude={station.lat}>
                            <MarkerContent>
                                <PinIcon color={color} />
                            </MarkerContent>
                            <MarkerPopup closeButton>
                                <div className="space-y-1 text-sm min-w-44">
                                    <p className="font-semibold">{station.name}</p>
                                    {cheap && (
                                        <p className="text-yellow-600 font-medium text-xs">⭐ Günstigste in der Nähe</p>
                                    )}
                                    <p className="text-muted-foreground text-xs">{station.street}, {station.place}</p>
                                    <p>{station.isOpen ? "✅ Geöffnet" : "❌ Geschlossen"}</p>
                                    <div className="flex gap-3 pt-1 flex-wrap">
                                        {station.e5 && (
                                            <span className={station.id === cheapestE5 ? "text-yellow-600 font-bold" : ""}>
                                                E5: <strong>{station.e5.toFixed(3)} €</strong>
                                            </span>
                                        )}
                                        {station.e10 && (
                                            <span className={station.id === cheapestE10 ? "text-yellow-600 font-bold" : ""}>
                                                E10: <strong>{station.e10.toFixed(3)} €</strong>
                                            </span>
                                        )}
                                        {station.diesel && (
                                            <span className={station.id === cheapestDiesel ? "text-yellow-600 font-bold" : ""}>
                                                Diesel: <strong>{station.diesel.toFixed(3)} €</strong>
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-muted-foreground text-xs">{station.dist.toFixed(1)} km entfernt</p>
                                </div>
                            </MarkerPopup>
                        </MapMarker>
                    );
                })}
            </Map>
            <Legend />
        </div>
    );
}
