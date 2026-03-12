import type { Metadata } from "next";
import { Arimo } from "next/font/google";
import { ThemeProvider } from "next-themes";
import "./globals.css";

const arimo = Arimo({
  subsets: ["latin"]
});

export const metadata: Metadata = {
  title: "Gas Price Prediction",
  description: "Benzinpreise und Preisprognosen in deiner Nähe",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "GasPreis",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${arimo.className} antialiased`}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
