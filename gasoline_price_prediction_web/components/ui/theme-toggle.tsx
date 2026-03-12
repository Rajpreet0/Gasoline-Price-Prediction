"use client";

import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";

function subscribe(cb: () => void) {
    window.addEventListener("storage", cb);
    return () => window.removeEventListener("storage", cb);
}

function useIsMounted() {
    return useSyncExternalStore(subscribe, () => true, () => false);
}

export function ThemeToggle() {
    const { resolvedTheme, setTheme } = useTheme();
    const mounted = useIsMounted();

    if (!mounted) return <div className="w-9 h-9" />;

    const isDark = resolvedTheme === "dark";

    return (
        <button
            onClick={() => setTheme(isDark ? "light" : "dark")}
            aria-label="Theme wechseln"
            className="relative w-9 h-9 rounded-full flex items-center justify-center transition-colors hover:bg-accent"
        >
            {/* Sun */}
            <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="absolute h-5 w-5 transition-all duration-500"
                style={{
                    opacity: isDark ? 0 : 1,
                    transform: isDark ? "rotate(-90deg) scale(0.5)" : "rotate(0deg) scale(1)",
                }}
            >
                <circle cx="12" cy="12" r="4" />
                <line x1="12" y1="2" x2="12" y2="4" />
                <line x1="12" y1="20" x2="12" y2="22" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="2" y1="12" x2="4" y2="12" />
                <line x1="20" y1="12" x2="22" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>

            {/* Moon */}
            <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="absolute h-5 w-5 transition-all duration-500"
                style={{
                    opacity: isDark ? 1 : 0,
                    transform: isDark ? "rotate(0deg) scale(1)" : "rotate(90deg) scale(0.5)",
                }}
            >
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
        </button>
    );
}