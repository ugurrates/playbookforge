"use client";
import { PLATFORM_LOGOS } from "@/lib/types";

interface PlatformCardProps {
  platformId: string;
  platformName: string;
  fileExtension: string;
  selected?: boolean;
  onClick?: () => void;
}

export function PlatformCard({ platformId, platformName, fileExtension, selected, onClick }: PlatformCardProps) {
  const logo = PLATFORM_LOGOS[platformId] || { color: "bg-[#1a2e1a]", abbr: platformId.slice(0, 2).toUpperCase() };

  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-3 p-3 rounded border transition-all text-left w-full ${
        selected
          ? "border-amber-500 bg-amber-500/10"
          : "border-[#2a3e2a] bg-[#111a11] hover:border-[#2a3e2a]"
      }`}
    >
      <div className={`w-10 h-10 ${logo.color} rounded flex items-center justify-center text-white font-bold text-sm shrink-0`}>
        {logo.abbr}
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium text-[#d4d4c8] truncate">{platformName}</p>
        <p className="text-xs text-[#7a7a6a]">{fileExtension}</p>
      </div>
      {selected && (
        <div className="ml-auto w-2 h-2 rounded-full bg-amber-400 shrink-0" />
      )}
    </button>
  );
}
