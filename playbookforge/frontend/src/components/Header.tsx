"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ArrowLeftRight,
  LayoutDashboard,
  FileText,
  Workflow,
  Bot,
  BookOpen,
  FolderOpen,
  Database,
} from "lucide-react";
import { TacticalShield } from "@/components/TacticalIcons";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/convert", label: "Convert", icon: ArrowLeftRight },
  { href: "/playbooks", label: "Playbooks", icon: FileText },
  { href: "/designer", label: "Designer", icon: Workflow },
  { href: "/ai", label: "AI Assistant", icon: Bot },
  { href: "/repos", label: "Repos", icon: Database },
  { href: "/resources", label: "Resources", icon: BookOpen },
  { href: "/documents", label: "Documents", icon: FolderOpen },
];

export function Header() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-50 border-b border-[#1a2e1a] bg-[#080d08]/95 backdrop-blur-md font-mono">
      {/* Top row: brand + right actions */}
      <div className="flex items-center h-14 px-6 gap-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <TacticalShield size={28} />
          <span className="font-bold text-sm tracking-wider uppercase text-[#d4d4c8]">
            PlaybookForge
          </span>
        </Link>

        <div className="flex-1" />

        {/* Right side */}
        <a
          href="https://github.com/uguratas/playbookforge"
          target="_blank"
          rel="noopener noreferrer"
          className="text-[10px] uppercase tracking-wider text-[#7a7a6a] hover:text-amber-500 transition font-semibold"
        >
          GitHub
        </a>
        <span className="text-[10px] px-2.5 py-1 rounded-sm bg-amber-500/15 text-amber-500 font-bold uppercase tracking-wider border border-amber-500/30">
          v1.0.0
        </span>
      </div>

      {/* Navigation row */}
      <nav className="flex items-center gap-1 px-6 pb-2 overflow-x-auto scrollbar-hide">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-sm text-[11px] font-medium uppercase tracking-wider transition-all whitespace-nowrap ${
                active
                  ? "bg-amber-500/15 text-amber-500 border border-amber-500/30"
                  : "text-[#7a7a6a] hover:text-[#d4d4c8] hover:bg-[#111a11] border border-transparent"
              }`}
            >
              <item.icon className={`w-3.5 h-3.5 ${active ? "text-amber-500" : ""}`} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
