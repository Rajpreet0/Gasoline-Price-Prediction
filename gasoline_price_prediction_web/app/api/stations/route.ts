import { NextRequest, NextResponse } from "next/server";

const BASE_URL = "https://creativecommons.tankerkoenig.de/json";

// In-Memory Cache: key = "lat,lng" (gerundet auf ~1km), value = { stations, expiresAt }
const cache = new Map<string, { stations: unknown; expiresAt: number }>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 Minuten

// Rate Limiting: key = IP, value = { count, windowStart }
const rateLimitMap = new Map<string, { count: number; windowStart: number }>();
const RATE_LIMIT = 10;       // max Requests
const RATE_WINDOW_MS = 60 * 1000; // pro Minute

function isRateLimited(ip: string): boolean {
    const now = Date.now();
    const entry = rateLimitMap.get(ip);

    if (!entry || now - entry.windowStart > RATE_WINDOW_MS) {
        rateLimitMap.set(ip, { count: 1, windowStart: now });
        return false;
    }

    if (entry.count >= RATE_LIMIT) return true;

    entry.count++;
    return false;
}

function cacheKey(lat: number, lng: number): string {
    // Runden auf 2 Dezimalstellen ≈ ~1km Grid
    return `${lat.toFixed(2)},${lng.toFixed(2)}`;
}

export async function GET(req: NextRequest) {
    // Rate Limiting
    const ip = req.headers.get("x-forwarded-for") ?? "unknown";
    if (isRateLimited(ip)) {
        return NextResponse.json({ error: "Zu viele Anfragen. Bitte warte eine Minute." }, { status: 429 });
    }

    const { searchParams } = new URL(req.url);
    const latStr = searchParams.get("lat");
    const lngStr = searchParams.get("lng");

    if (!latStr || !lngStr) {
        return NextResponse.json({ error: "lat und lng sind erforderlich" }, { status: 400 });
    }

    // Input Validation
    const lat = parseFloat(latStr);
    const lng = parseFloat(lngStr);

    if (isNaN(lat) || isNaN(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180) {
        return NextResponse.json({ error: "Ungültige Koordinaten" }, { status: 400 });
    }

    // Cache prüfen
    const key = cacheKey(lat, lng);
    const cached = cache.get(key);
    if (cached && Date.now() < cached.expiresAt) {
        return NextResponse.json(cached.stations, { headers: { "X-Cache": "HIT" } });
    }

    const apiKey = process.env.TANKERKOENIG_API_KEY;
    if (!apiKey) {
        return NextResponse.json({ error: "API Key nicht konfiguriert" }, { status: 500 });
    }

    const url = new URL(`${BASE_URL}/list.php`);
    url.searchParams.set("lat", lat.toString());
    url.searchParams.set("lng", lng.toString());
    url.searchParams.set("rad", "5");
    url.searchParams.set("type", "all");
    url.searchParams.set("sort", "dist");
    url.searchParams.set("apikey", apiKey);

    const response = await fetch(url.toString());
    const data = await response.json();

    if (!data.ok) {
        return NextResponse.json({ error: data.message }, { status: 500 });
    }

    // In Cache speichern
    cache.set(key, { stations: data.stations, expiresAt: Date.now() + CACHE_TTL_MS });

    return NextResponse.json(data.stations, { headers: { "X-Cache": "MISS" } });
}
