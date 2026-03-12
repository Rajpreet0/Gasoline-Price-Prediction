"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useLocation } from "../../hooks/useLocation";
import { useStations } from "../../hooks/useStations";
import { LocationSearch } from "../components/location-search";
import { SavingsCalculator } from "../components/savings-calculator";
import { Location } from "../../types";
import { Spinner } from "@/components/ui/spinner";
import { BrandFilter } from "../components/brand-filter";
import { ThemeToggle } from "@/components/ui/theme-toggle";

const StationsMap = dynamic(
    () => import("../components/stations-map").then((m) => m.StationsMap),
    { ssr: false, loading: () => <div className="flex items-center justify-center h-125"><Spinner /></div> }
);

const HomeView = () => {
    const { location: browserLocation, error: locationError, loading: locationLoading } = useLocation();
    const [manualLocation, setManualLocation] = useState<Location | null>(null);
    const [brandFilter, setBrandFilter] = useState<string[]>([]);

    const activeLocation = manualLocation ?? browserLocation;

    const { stations, error: stationsError, loading: stationsLoading, lastUpdated } = useStations(activeLocation);

    const filteredStations = brandFilter.length === 0 ? stations : stations.filter(s => brandFilter.some(b => s.name.toLowerCase().includes(b.toLowerCase())))

    const mapLocation = activeLocation
        ? { lat: activeLocation.latitude, lng: activeLocation.longitude }
        : null;

    function handleAddressSelect(lat: number, lng: number) {
        setManualLocation({ latitude: lat, longitude: lng });
    }

    return (
        <div className="p-8 space-y-4">
            <div className="flex items-center justify-between">
                <h1 className="text-4xl font-semibold">Tankpreise in deiner Nähe</h1>
                <ThemeToggle />
            </div>

            <div className="flex items-center gap-3">
                <LocationSearch onSelect={handleAddressSelect} />
                {manualLocation && (
                    <button
                        className="text-sm text-muted-foreground underline whitespace-nowrap"
                        onClick={() => setManualLocation(null)}
                    >
                        Zurück zu meinem Standort
                    </button>
                )}
            </div>

            {locationLoading && !manualLocation && (
                <p className="text-muted-foreground">Standort wird ermittelt...</p>
            )}
            {locationError && !manualLocation && (
                <p className="text-red-500">{locationError}</p>
            )}
            {stationsLoading && <p className="text-muted-foreground">Tankstellen werden geladen...</p>}
            {stationsError && <p className="text-red-500">{stationsError}</p>}

            {stations.length > 0 && (
                <BrandFilter
                    stations={stations}
                    selected={brandFilter}
                    onChange={setBrandFilter}
                />
            )}

            {mapLocation && (
                <>
                    <StationsMap location={mapLocation} stations={filteredStations} />
                    {lastUpdated && (
                        <p className="text-xs text-muted-foreground text-right">
                            Letztes Update: {lastUpdated.toLocaleTimeString("de-DE")}
                        </p>
                    )}
                </>
            )}

            {filteredStations.length > 0 && (
                <SavingsCalculator stations={filteredStations} />
            )}
        </div>
    );
};

export default HomeView;
