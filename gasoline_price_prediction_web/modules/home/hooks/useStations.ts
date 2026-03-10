import { useEffect, useReducer } from "react";
import { Location, Station } from "../types";

type State = { stations: Station[]; error: string | null; loading: boolean };
type Action =
    | { type: "fetched"; data: Station[] }
    | { type: "error"; message: string }
    | { type: "reset" };

function reducer(_state: State, action: Action): State {
    switch (action.type) {
        case "reset":    return { stations: [], error: null, loading: true };
        case "fetched":  return { stations: action.data, error: null, loading: false };
        case "error":    return { stations: [], error: action.message, loading: false };
    }
}

const initial: State = { stations: [], error: null, loading: false };

export function useStations(location: Location | null) {
    const [state, dispatch] = useReducer(reducer, initial);

    useEffect(() => {
        if (!location) return;

        let cancelled = false;
        dispatch({ type: "reset" });

        fetch(`/api/stations?lat=${location.latitude}&lng=${location.longitude}`)
            .then((res) => res.json())
            .then((data) => {
                if (cancelled) return;
                if (data.error) throw new Error(data.error);
                dispatch({ type: "fetched", data });
            })
            .catch((err) => { if (!cancelled) dispatch({ type: "error", message: err.message }); });

        return () => { cancelled = true; };
    }, [location]);

    return state;
}
