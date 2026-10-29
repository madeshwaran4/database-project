import type { Metadata } from "next";
import Navbar from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "SecureVote - Duplicate-Vote Prevention System",
  description: "Next-generation election integrity platform with biometric deduplication and cryptographic anonymity.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">{children}</main>
        <footer className="glass-panel border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>SecureVote Election Integrity System &bull; AES-256-GCM Minutiae Encryption</span>
            <span>Zero-Link Voter / Vote Anonymity Protocol</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
