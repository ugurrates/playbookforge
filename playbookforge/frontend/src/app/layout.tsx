import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/Header";

export const metadata: Metadata = {
  title: "PlaybookForge — Universal SOAR Playbook Converter",
  description: "Write a playbook ONCE in CACAO v2.0, export to ANY SOAR platform.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0a0f0a] text-[#d4d4c8] flex flex-col font-mono">
        <Header />
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </body>
    </html>
  );
}
