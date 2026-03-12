"use client";

import { BookOpen, Wrench, ChevronRight } from "lucide-react";
import { RESOURCE_CATEGORY_COLORS, RESOURCE_CATEGORY_LABELS, DIFFICULTY_COLORS } from "@/lib/types";

interface ResourceCardProps {
  id: string;
  title: string;
  description: string;
  category: string;
  difficulty: string;
  step_count: number;
  tags: string[];
  type: "best-practice" | "integration-guide";
  onClick: () => void;
}

export default function ResourceCard({
  title,
  description,
  category,
  difficulty,
  step_count,
  tags,
  type,
  onClick,
}: ResourceCardProps) {
  const Icon = type === "best-practice" ? BookOpen : Wrench;
  const catColor = RESOURCE_CATEGORY_COLORS[category] || "bg-[#1a2e1a]";
  const catLabel = RESOURCE_CATEGORY_LABELS[category] || category;
  const diffColor = DIFFICULTY_COLORS[difficulty] || "bg-[#1a2e1a]";

  return (
    <button
      onClick={onClick}
      className="bg-[#111a11] border border-[#2a3e2a] rounded p-4 text-left hover:border-amber-500 transition group w-full"
    >
      <div className="flex items-start gap-3">
        <div className={`w-9 h-9 ${catColor} rounded flex items-center justify-center text-white shrink-0`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-medium text-[#d4d4c8] group-hover:text-amber-300 transition line-clamp-1">
            {title}
          </h3>
          <p className="text-xs text-[#7a7a6a] mt-0.5 line-clamp-2">{description}</p>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className={`px-1.5 py-0.5 text-[9px] rounded ${catColor} text-white/80`}>
              {catLabel}
            </span>
            <span className={`px-1.5 py-0.5 text-[9px] rounded ${diffColor} text-white/80 capitalize`}>
              {difficulty}
            </span>
            <span className="text-[9px] text-[#2a3e2a]">
              {step_count} steps
            </span>
          </div>
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {tags.slice(0, 3).map((tag) => (
                <span key={tag} className="px-1 py-0.5 text-[9px] bg-[#1a2e1a]/50 text-[#7a7a6a] rounded">
                  {tag}
                </span>
              ))}
              {tags.length > 3 && (
                <span className="text-[9px] text-[#2a3e2a]">+{tags.length - 3}</span>
              )}
            </div>
          )}
        </div>
        <ChevronRight className="w-4 h-4 text-[#2a3e2a] group-hover:text-amber-400 transition shrink-0 mt-1" />
      </div>
    </button>
  );
}
