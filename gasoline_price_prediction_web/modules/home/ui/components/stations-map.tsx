"use client";

import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Station } from "../../types";
import { MapPinPen } from "lucide-react";

// Leaflet default icon fix für Next.js
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const makeIcon = (color: string) => new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-${color}.png`,
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
});

const cheapestIcon = makeIcon("gold");
const openIcon = makeIcon("green");
const closedIcon = makeIcon("red");
const userIcon = makeIcon("blue");

type MapLocation = { lat: number; lng: number };
type Props = { location: MapLocation; stations: Station[] };

function findCheapest(stations: Station[], fuel: "e5" | "e10" | "diesel"): string | null {
    const open = stations.filter((s) => s.isOpen && s[fuel] !== null);
    if (!open.length) return null;
    return open.reduce((a, b) => (a[fuel]! < b[fuel]! ? a : b)).id;
}

function Legend() {
    return (
        <div className="absolute bottom-8 right-2 z-1000 bg-white rounded-lg shadow-md p-3 text-sm space-y-1.5">
            <p className="font-semibold text-xs uppercase text-gray-500 mb-2">Legende</p>
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
        <div className="relative">
            <MapContainer
                center={[location.lat, location.lng]}
                zoom={13}
                style={{ width: "100%", height: 500, borderRadius: "0.5rem" }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <Circle
                    center={[location.lat, location.lng]}
                    radius={5000}
                    pathOptions={{ color: "#3b82f6", fillColor: "#3b82f6", fillOpacity: 0.05 }}
                />

                <Marker position={[location.lat, location.lng]} icon={userIcon}>
                    <Popup>Dein Standort</Popup>
                </Marker>

                {stations.map((station) => {
                    const cheap = isCheapest(station.id);
                    const icon = cheap ? cheapestIcon : station.isOpen ? openIcon : closedIcon;

                    return (
                        <Marker key={station.id} position={[station.lat, station.lng]} icon={icon}>
                            <Popup>
                                <div className="space-y-1 text-sm min-w-45">
                                    <p className="font-semibold">{station.name}</p>
                                    {cheap && (
                                        <p className="text-yellow-600 font-medium text-xs">⭐ Günstigste in der Nähe</p>
                                    )}
                                    <p className="text-gray-500 text-xs">{station.street}, {station.place}</p>
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
                                    <p className="text-gray-400 text-xs">{station.dist.toFixed(1)} km entfernt</p>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>
            <Legend />
        </div>
    );
}
