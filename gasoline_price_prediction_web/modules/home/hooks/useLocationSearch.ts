import { useState, useCallback } from "react";

export type GeoResult = {
    display_name: string;
    lat: string;
    lon: string;
};

export function useLocationSearch() {
    const [results, setResults] = useState<GeoResult[]>([]);
    const [loading, setLoading] = useState(false);

    const search = useCallback(async (query: string) => {
        if (!query.trim()) { setResults([]); return; }

        setLoading(true);
        try {
            const res = await fetch(`/api/geocode?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            setResults(data);
        } finally {
            setLoading(false);
        }
    }, []);

    return { results, loading, search, setResults };
}
