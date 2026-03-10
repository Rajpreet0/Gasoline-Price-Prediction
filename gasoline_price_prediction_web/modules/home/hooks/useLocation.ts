import { useEffect, useState } from "react";
import { Location } from "../types";


export function useLocation() {
    const [location, setLocation]   =   useState<Location | null>(null);
    const [error, setError]         =   useState<string | null>(null);
    const [loading, setLoading]     =   useState(false);

    useEffect(() => {
        if (!navigator.geolocation) {
            setError("Geolocation wird von deinem Browser nicht unterstützt.");
            setLoading(false);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                setLocation({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                });
                setLoading(false);
            }, (err) => {
                setError("Standort konnte nicht ermittelt werden: " + err.message);
                setLoading(false);
            }
        );
    }, []);

    return { location, error, loading}
}