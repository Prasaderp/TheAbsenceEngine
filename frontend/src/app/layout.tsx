import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "The Absence Engine",
  description: "Structured absence detection for any document — find what's missing before it matters.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>{children}</body>
    </html>
  );
}
