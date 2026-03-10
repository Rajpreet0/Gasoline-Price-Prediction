import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
    const query = new URL(req.url).searchParams.get("q");

    if (!query) {
        return NextResponse.json({ error: "q ist erforderlich" }, { status: 400 });
    }

    const url = new URL("https://nominatim.openstreetmap.org/search");
    url.searchParams.set("q", query);
    url.searchParams.set("format", "json");
    url.searchParams.set("limit", "5");
    url.searchParams.set("countrycodes", "de");

    const response = await fetch(url.toString(), {
        headers: { "User-Agent": "GasolinePricePrediction/1.0" },
    });

    const data = await response.json();
    return NextResponse.json(data);
}
