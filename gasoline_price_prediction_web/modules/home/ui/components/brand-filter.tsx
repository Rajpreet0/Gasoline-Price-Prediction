"use client";

import Image from "next/image";
import { Badge } from "@/components/ui/badge";
import { Station } from "../../types";
import { ListFilter } from "lucide-react";


const KNOWN_BRANDS: {label: string; domain?: string; logoUrl?: string }[] = [
    { label: "Aral", logoUrl: "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Aral_Logo.svg/32px-Aral_Logo.svg.png" },
    { label: "Shell", domain: "shell.de" },
    { label: "BFT", domain: "bft.de"},
    { label: "Avia", domain: "avia.de"},
    { label: "Star", domain: "star.de"},
    { label: "ESSO",  domain: "esso.de" },
    { label: "BP",    domain: "bp.com" },
    { label: "Total", domain: "totalenergies.de" },
    { label: "Jet",   domain: "jet.de" },
]

function BrandLogo({ domain, logoUrl, label }: { domain?: string; logoUrl?: string; label: string }) {
    if (!logoUrl && !domain) return null;
    const src = logoUrl ?? `https://www.google.com/s2/favicons?domain=${domain}&sz=32`;
    return (
        <Image
            src={src}
            alt={label}
            width={16}
            height={16}
            className="rounded-sm"
            onError={(e) => { e.currentTarget.style.display = "none"; }}
        />
    );
}

type Props = {
    stations: Station[];
    selected: string[];
    onChange: (brands: string[]) => void;
}

export function BrandFilter({ stations, selected, onChange }: Props) {
    
    const available = KNOWN_BRANDS.filter(brand => 
        stations.some(s => s.name.toLowerCase().includes(brand.label.toLowerCase()))
    );

    if (available.length === 0) return null;  

    function toggle(label: string) {
        onChange(
            selected.includes(label) ? selected.filter(b => b !== label) : [...selected, label]
        )
    }

    return (
        <div className="flex flex-wrap gap-2 items-center">
            <span className="text-sm text-muted-foreground flex items-center"><ListFilter size={15}/></span>
            {available.map(brand => (
                <Badge
                    key={brand.label}
                    variant={selected.includes(brand.label) ? "default" : "outline"}
                    className="cursor-pointer select-none gap-1"
                    onClick={() => toggle(brand.label)}
                >
                    <BrandLogo domain={brand.domain} label={brand.label}/>
                    {brand.label}
                </Badge>
            ))}
            {selected.length > 0 && (
                <button
                    className="text-xs text-muted-foreground underline"
                    onClick={() => onChange([])}
                >
                    Alle anzeigen
                </button>
            )}
        </div>
    )
}