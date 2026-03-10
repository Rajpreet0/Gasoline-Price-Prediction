"use client";

import { useState, useRef } from "react";
import {Search} from "lucide-react"
import { Input } from "@/components/ui/input";
import { useLocationSearch, GeoResult } from "../../hooks/useLocationSearch";
import { Spinner } from "@/components/ui/spinner";

type Props = {
    onSelect: (lat: number, lng: number, label: string) => void;
};

export function LocationSearch({ onSelect }: Props) {
    const [query, setQuery] = useState("");
    const [open, setOpen] = useState(false);
    const { results, loading, search, setResults } = useLocationSearch();
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    function handleChange(value: string) {
        setQuery(value);
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => {
            search(value);
            setOpen(true);
        }, 400);
    }

    function handleSelect(result: GeoResult) {
        setQuery(result.display_name);
        setResults([]);
        setOpen(false);
        onSelect(parseFloat(result.lat), parseFloat(result.lon), result.display_name);
    }

    return (
        <div className="relative w-full max-w-md">
            <div className="bg-white rounded-md border flex items-center p-1">
                <Search size={20} className="ml-2"/>
                <Input
                    placeholder="Adresse suchen..."
                    value={query}
                    className="border-0"
                    onChange={(e) => handleChange(e.target.value)}
                    onFocus={() => results.length > 0 && setOpen(true)}
                />
                {loading && (
                    <Spinner className="mr-2"/>
                )}
            </div>
            {open && results.length > 0 && (
                <ul className="absolute z-9999 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto text-sm">
                    {results.map((r, i) => (
                        <li
                            key={i}
                            className="px-3 py-2 hover:bg-gray-100 cursor-pointer truncate"
                            onClick={() => handleSelect(r)}
                        >
                            {r.display_name}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
