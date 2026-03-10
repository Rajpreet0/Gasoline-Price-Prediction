import { useEffect, useState } from "react";
import { Location, Station } from "../types";

export function useStations(location: Location | null) {
    const [stations, setStations] = useState<Station[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!location) return;

        setLoading(true);
        setError(null);

        fetch(`/api/stations?lat=${location.latitude}&lng=${location.longitude}`)
            .then((res) => res.json())
            .then((data) => {
                if (data.error) throw new Error(data.error);
                setStations(data);
            })
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));
    }, [location]);

    return { stations, error, loading };
}
