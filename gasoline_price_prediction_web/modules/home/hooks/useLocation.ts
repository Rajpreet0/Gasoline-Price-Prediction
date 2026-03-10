import { useEffect, useState } from "react";
import { Location } from "../types";

const hasGeolocation = typeof navigator !== "undefined" && !!navigator.geolocation;

export function useLocation() {
    const [location, setLocation] = useState<Location | null>(null);
    const [error, setError]       = useState<string | null>(
        hasGeolocation ? null : "Geolocation wird von deinem Browser nicht unterstützt."
    );
    const [loading, setLoading]   = useState(hasGeolocation);

    useEffect(() => {
        if (!hasGeolocation) return;

        navigator.geolocation.getCurrentPosition(
            (position) => {
                setLocation({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                });
                setLoading(false);
            },
            (err) => {
                setError("Standort konnte nicht ermittelt werden: " + err.message);
                setLoading(false);
            }
        );
    }, []);

    return { location, error, loading };
}
