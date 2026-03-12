"use client";

import { useState, useEffect } from "react";
import { ArrowLeft, BookOpen, Wrench, CheckCircle, Copy, ExternalLink, Loader2 } from "lucide-react";
import { getBestPractice, getIntegrationGuide, type BestPracticeDetail, type IntegrationGuideDetail } from "@/lib/api";
import { RESOURCE_CATEGORY_COLORS, RESOURCE_CATEGORY_LABELS, DIFFICULTY_COLORS } from "@/lib/types";

interface ResourceDetailProps {
  id: string;
  type: "best-practice" | "integration-guide";
  onBack: () => void;
}

export default function ResourceDetail({ id, type, onBack }: ResourceDetailProps) {
  const [data, setData] = useState<BestPracticeDetail | IntegrationGuideDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    const fetcher = type === "best-practice" ? getBestPractice(id) : getIntegrationGuide(id);
    fetcher
      .then((res) => setData(res))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [id, type]);

  const copyCode = (code: string, idx: number) => {
    navigator.clipboard.writeText(code);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  if (loading) {
    return (
      <div className="text-center py-20 text-[#7a7a6a]">
        <Loader2 className="w-6 h-6 mx-auto animate-spin mb-2" />
        Loading resource...
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-20 text-[#7a7a6a]">
        Resource not found.
        <button onClick={onBack} className="block mx-auto mt-4 text-amber-400 text-sm">Go back</button>
      </div>
    );
  }

  const catColor = RESOURCE_CATEGORY_COLORS[data.category] || "bg-[#1a2e1a]";
  const catLabel = RESOURCE_CATEGORY_LABELS[data.category] || data.category;
  const diffColor = DIFFICULTY_COLORS[data.difficulty] || "bg-[#1a2e1a]";
  const Icon = type === "best-practice" ? BookOpen : Wrench;
  const isBP = type === "best-practice";
  const bpData = isBP ? (data as BestPracticeDetail) : null;
  const guideData = !isBP ? (data as IntegrationGuideDetail) : null;

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="flex items-center gap-2 text-sm text-[#7a7a6a] hover:text-[#d4d4c8] transition">
        <ArrowLeft className="w-4 h-4" /> Back to Resources
      </button>

      {/* Header */}
      <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5">
        <div className="flex items-start gap-4">
          <div className={`w-12 h-12 ${catColor} rounded flex items-center justify-center text-white shrink-0`}>
            <Icon className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-semibold">{data.title}</h2>
            <p className="text-sm text-[#7a7a6a] mt-1">{data.description}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              <span className={`px-2 py-0.5 text-xs rounded ${catColor} text-white/90`}>{catLabel}</span>
              <span className={`px-2 py-0.5 text-xs rounded ${diffColor} text-white/90 capitalize`}>{data.difficulty}</span>
              <span className="px-2 py-0.5 text-xs bg-[#1a2e1a] text-[#d4d4c8] rounded">
                {data.steps.length} steps
              </span>
            </div>
            {data.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {data.tags.map((tag) => (
                  <span key={tag} className="px-1.5 py-0.5 text-[10px] bg-[#111a11] text-[#7a7a6a] rounded">{tag}</span>
                ))}
              </div>
            )}
            {bpData?.mitre_techniques && bpData.mitre_techniques.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {bpData.mitre_techniques.map((t) => (
                  <a
                    key={t}
                    href={`https://attack.mitre.org/techniques/${t.replace(".", "/")}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-1.5 py-0.5 text-[10px] bg-red-500/10 text-red-400 rounded hover:bg-red-500/20 transition inline-flex items-center gap-1"
                  >
                    {t} <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Prerequisites (guides only) */}
      {guideData?.prerequisites && guideData.prerequisites.length > 0 && (
        <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5">
          <h3 className="text-sm font-medium text-[#d4d4c8] mb-3">Prerequisites</h3>
          <ul className="space-y-1.5">
            {guideData.prerequisites.map((prereq, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[#7a7a6a]">
                <CheckCircle className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
                {prereq}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Steps */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-[#d4d4c8]">Step-by-Step Guide</h3>
        {data.steps.map((step, i) => (
          <div key={i} className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5">
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 bg-amber-600 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0">
                {step.order}
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-[#d4d4c8]">{step.title}</h4>
                <p className="text-xs text-[#7a7a6a] mt-1">{step.description}</p>
                {step.code_example && (
                  <div className="mt-3 relative">
                    <button
                      onClick={() => copyCode(step.code_example, i)}
                      className="absolute top-2 right-2 p-1 rounded bg-[#1a2e1a] hover:bg-[#1a2e1a] transition"
                      title="Copy"
                    >
                      {copiedIdx === i ? (
                        <CheckCircle className="w-3 h-3 text-green-400" />
                      ) : (
                        <Copy className="w-3 h-3 text-[#7a7a6a]" />
                      )}
                    </button>
                    <pre className="bg-[#0a0f0a] border border-[#1a2e1a] rounded p-3 text-xs text-[#d4d4c8] overflow-x-auto font-mono">
                      {step.code_example}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Related Products (best practices) */}
      {bpData?.related_product_ids && bpData.related_product_ids.length > 0 && (
        <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5">
          <h3 className="text-sm font-medium text-[#d4d4c8] mb-3">Related Products</h3>
          <div className="flex flex-wrap gap-2">
            {bpData.related_product_ids.map((pid) => (
              <span key={pid} className="px-2 py-1 text-xs bg-[#111a11] text-[#7a7a6a] rounded border border-[#2a3e2a]">
                {pid}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
