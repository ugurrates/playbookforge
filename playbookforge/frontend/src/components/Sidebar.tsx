"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield, ArrowLeftRight, LayoutDashboard, FileText, Workflow, Bot, BookOpen, FolderOpen, Database } from "lucide-react";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/convert", label: "Convert", icon: ArrowLeftRight },
  { href: "/playbooks", label: "Playbooks", icon: FileText },
  { href: "/designer", label: "Designer", icon: Workflow },
  { href: "/ai", label: "AI Assistant", icon: Bot },
  { href: "/repos", label: "Community Repos", icon: Database },
  { href: "/resources", label: "Resources", icon: BookOpen },
  { href: "/documents", label: "Documents", icon: FolderOpen },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden md:flex w-56 flex-col bg-[#080d08] border-r border-[#1a2e1a]">
      {/* Logo / Brand */}
      <div className="h-14 flex items-center gap-2.5 px-5 border-b border-[#1a2e1a]">
        <Shield className="w-6 h-6 text-amber-500" />
        <span className="font-bold text-sm tracking-wider uppercase text-[#d4d4c8]">
          PlaybookForge
        </span>
      </div>

      {/* Section label */}
      <div className="px-5 pt-5 pb-2">
        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-[#7a7a6a]">
          Operations
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-0.5">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-sm text-xs font-medium uppercase tracking-wider transition-all ${
                active
                  ? "bg-amber-500/15 text-amber-500 border-l-2 border-amber-500"
                  : "text-[#7a7a6a] hover:text-[#d4d4c8] hover:bg-[#111a11] border-l-2 border-transparent"
              }`}
            >
              <item.icon className={`w-4 h-4 ${active ? "text-amber-500" : ""}`} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Divider */}
      <div className="mx-4 border-t border-[#1a2e1a]" />

      {/* Footer */}
      <div className="p-4 flex flex-col items-center gap-1">
        <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-500">
          CACAO v2.0
        </span>
        <span className="text-[9px] uppercase tracking-wider text-[#7a7a6a]">
          Standard Protocol
        </span>
      </div>
    </aside>
  );
}
