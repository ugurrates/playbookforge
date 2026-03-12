"use client";
import { STEP_TYPE_COLORS } from "@/lib/types";
import type { WorkflowStep } from "@/lib/types";
import { Play, Square, Zap, GitBranch, GitFork, BookOpen } from "lucide-react";

interface Props {
  workflow: Record<string, WorkflowStep>;
  workflowStart: string;
}

const STEP_ICONS: Record<string, React.ElementType> = {
  start: Play,
  end: Square,
  action: Zap,
  "if-condition": GitBranch,
  parallel: GitFork,
  "playbook-action": BookOpen,
};

export function StepList({ workflow, workflowStart }: Props) {
  // Simple linear walk
  const ordered: Array<[string, WorkflowStep]> = [];
  const visited = new Set<string>();
  let current: string | undefined = workflowStart;

  while (current && !visited.has(current)) {
    visited.add(current);
    const step: WorkflowStep | undefined = workflow[current];
    if (!step) break;
    ordered.push([current, step]);
    const next: string | undefined = step.on_completion || step.on_true || (step.next_steps?.[0]) || undefined;
    current = next;
  }

  return (
    <div className="space-y-1">
      {ordered.map(([id, step]) => {
        const Icon = STEP_ICONS[step.type] || Zap;
        const color = STEP_TYPE_COLORS[step.type] || "bg-[#2a3e2a]";
        return (
          <div key={id} className="flex items-center gap-3 p-2 rounded hover:bg-[#111a11]/50">
            <div className={`w-7 h-7 ${color} rounded flex items-center justify-center`}>
              <Icon className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-[#d4d4c8] truncate">{step.name || id}</p>
              {step.description && (
                <p className="text-[11px] text-[#7a7a6a] truncate">{step.description}</p>
              )}
            </div>
            <span className="text-[10px] text-[#7a7a6a] font-mono shrink-0">{step.type}</span>
          </div>
        );
      })}
    </div>
  );
}
