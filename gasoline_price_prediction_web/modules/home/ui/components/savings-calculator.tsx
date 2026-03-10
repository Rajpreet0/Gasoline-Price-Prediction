"use client";

import { useState, useMemo } from "react";
import { Station } from "../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Info } from "lucide-react";

type FuelType = "e5" | "e10" | "diesel";

function ColHeader({ label, tip }: { label: string; tip: string }) {
    return (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger className="inline-flex items-center gap-1 cursor-default">
                    {label} <Info size={13} />
                </TooltipTrigger>
                <TooltipContent className="max-w-48 text-center">{tip}</TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
}

type Props = {
    stations: Station[];
};

type Result = {
    station: Station;
    price: number;
    drivingCost: number;
    savings: number;
    netSavings: number;
};

export function SavingsCalculator({ stations }: Props) {
    const [consumption, setConsumption] = useState<string>("8");
    const [fuel, setFuel] = useState<FuelType>("e5");
    const [amount, setAmount] = useState<string>("40");

    const results = useMemo<Result[]>(() => {
        const cons = parseFloat(consumption);
        const amt = parseFloat(amount);
        if (isNaN(cons) || isNaN(amt) || cons <= 0 || amt <= 0) return [];

        const openStations = stations.filter((s) => s.isOpen && s[fuel] !== null);
        if (openStations.length === 0) return [];

        // Nächste Tankstelle = Referenz (kleinste Distanz)
        const nearest = openStations.reduce((a, b) => a.dist < b.dist ? a : b);
        const nearestPrice = nearest[fuel] as number;

        return openStations
            .map((s) => {
                const price = s[fuel] as number;
                // Extrafahrt im Vergleich zur nächsten Tankstelle
                const extraDist = Math.max(0, s.dist - nearest.dist);
                const drivingCost = ((extraDist * 2) / 100) * cons * price;
                // Ersparnis gegenüber der nächsten Tankstelle
                const savings = (nearestPrice - price) * amt;
                const netSavings = savings - drivingCost;
                return { station: s, price, drivingCost, savings, netSavings };
            })
            .sort((a, b) => b.netSavings - a.netSavings);
    }, [stations, consumption, fuel, amount]);

    return (
        <Card>
            <CardHeader>
                <CardTitle>Lohnt sich die Fahrt?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Inputs */}
                <div className="flex flex-wrap gap-4">
                    <div className="flex flex-col gap-1">
                        <label className="text-sm text-muted-foreground">Kraftstoff</label>
                        <Select value={fuel} onValueChange={(v) => setFuel(v as FuelType)}>
                            <SelectTrigger className="w-28">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="e5">E5</SelectItem>
                                <SelectItem value="e10">E10</SelectItem>
                                <SelectItem value="diesel">Diesel</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="flex flex-col gap-1">
                        <label className="text-sm text-muted-foreground">Verbrauch (L/100km)</label>
                        <Input
                            type="number"
                            min={1}
                            max={30}
                            value={consumption}
                            onChange={(e) => setConsumption(e.target.value)}
                            className="w-28"
                        />
                    </div>
                    <div className="flex flex-col gap-1">
                        <label className="text-sm text-muted-foreground">Tankmenge (Liter)</label>
                        <Input
                            type="number"
                            min={1}
                            max={200}
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                            className="w-28"
                        />
                    </div>
                </div>

                {/* Ergebnisse */}
                {results.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Keine offenen Tankstellen mit {fuel.toUpperCase()} gefunden.</p>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-muted-foreground border-b">
                                    <th className="text-left py-2 pr-4">Tankstelle</th>
                                    <th className="text-right py-2 pr-4">
                                        <ColHeader label="Preis" tip="Preis pro Liter für den gewählten Kraftstoff" />
                                    </th>
                                    <th className="text-right py-2 pr-4">
                                        <ColHeader label="Extrafahrt" tip="Kosten für die zusätzlichen Kilometer im Vergleich zur nächsten Tankstelle (Hin- & Rückfahrt)" />
                                    </th>
                                    <th className="text-right py-2 pr-4">
                                        <ColHeader label="vs. Nächste" tip="Reine Preisersparnis gegenüber der nächsten Tankstelle, ohne Fahrkosten" />
                                    </th>
                                    <th className="text-right py-2">
                                        <ColHeader label="Netto" tip="Tatsächliche Ersparnis: Preisersparnis minus Extrafahrtkosten. Grün = lohnt sich" />
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {results.map((r) => (
                                    <tr key={r.station.id} className="border-b last:border-0">
                                        <td className="py-2 pr-4">
                                            <p className="font-medium">{r.station.name}</p>
                                            <p className="text-muted-foreground text-xs">{r.station.dist.toFixed(1)} km</p>
                                        </td>
                                        <td className="text-right py-2 pr-4">{r.price.toFixed(3)} €</td>
                                        <td className="text-right py-2 pr-4 text-red-500">-{r.drivingCost.toFixed(2)} €</td>
                                        <td className="text-right py-2 pr-4">
                                            {r.savings >= 0
                                                ? <span className="text-green-600">+{r.savings.toFixed(2)} €</span>
                                                : <span className="text-red-500">{r.savings.toFixed(2)} €</span>
                                            }
                                        </td>
                                        <td className="text-right py-2">
                                            {r.station.dist === Math.min(...results.map(x => x.station.dist))
                                                ? <Badge variant="outline">Nächste</Badge>
                                                : <Badge variant={r.netSavings > 0 ? "default" : "secondary"}>
                                                    {r.netSavings > 0 ? "+" : ""}{r.netSavings.toFixed(2)} €
                                                  </Badge>
                                            }
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
