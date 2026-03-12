"use client";

import { useState, useEffect } from "react";
import { X, Download, Loader2, CheckCircle2, AlertTriangle, Copy } from "lucide-react";
import { listPlatforms, convertPlaybook, convertAll } from "@/lib/api";
import type { Platform, ConvertResponse } from "@/lib/api";
import { PLATFORM_LOGOS } from "@/lib/types";

interface ExportModalProps {
  playbook: Record<string, unknown>;
  onClose: () => void;
}

export function ExportModal({ playbook, onClose }: ExportModalProps) {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [results, setResults] = useState<Record<string, ConvertResponse & { error?: string }>>({});
  const [loading, setLoading] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    listPlatforms().then((d) => setPlatforms(d.platforms)).catch(() => {});
  }, []);

  const handleExport = async (platformId: string) => {
    setLoading(platformId);
    try {
      const result = await convertPlaybook(playbook, platformId);
      setResults((prev) => ({ ...prev, [platformId]: result }));
    } catch (err) {
      setResults((prev) => ({
        ...prev,
        [platformId]: { success: false, error: String(err) } as ConvertResponse & { error: string },
      }));
    }
    setLoading(null);
  };

  const handleExportAll = async () => {
    setLoading("all");
    try {
      const allResults = await convertAll(playbook);
      if (allResults.results) {
        setResults(allResults.results);
      }
    } catch {
      // ignore
    }
    setLoading(null);
  };

  const handleDownload = (platformId: string) => {
    const r = results[platformId];
    if (!r?.content) return;
    const blob = new Blob([r.content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = r.filename || `playbook.${platformId}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCopy = (platformId: string) => {
    const r = results[platformId];
    if (!r?.content) return;
    navigator.clipboard.writeText(r.content);
    setCopied(platformId);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-[#111a11] border border-[#2a3e2a] rounded w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#2a3e2a]">
          <h2 className="text-lg font-semibold text-white">Export Playbook</h2>
          <button onClick={onClose} className="text-[#7a7a6a] hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Export All Button */}
          <button
            onClick={handleExportAll}
            disabled={loading !== null}
            className="w-full mb-4 px-4 py-3 btn-primary disabled:opacity-50 text-sm flex items-center justify-center gap-2"
          >
            {loading === "all" ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            Export to All Platforms
          </button>

          {/* Platform Grid */}
          <div className="grid grid-cols-2 gap-3">
            {platforms.map((p) => {
              const logo = PLATFORM_LOGOS[p.platform_id];
              const result = results[p.platform_id];
              const isLoading = loading === p.platform_id;

              return (
                <div key={p.platform_id} className="bg-[#0f1a0f] border border-[#2a3e2a] rounded p-3">
                  <div className="flex items-center gap-2 mb-2">
                    {logo && (
                      <span className={`w-7 h-7 rounded text-[10px] font-bold flex items-center justify-center text-white ${logo.color}`}>
                        {logo.abbr}
                      </span>
                    )}
                    <div>
                      <div className="text-sm font-medium text-white">{p.platform_name}</div>
                      <div className="text-[10px] text-[#7a7a6a]">{p.file_extension}</div>
                    </div>
                  </div>

                  {result?.success ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-1 text-xs text-green-400">
                        <CheckCircle2 className="w-3 h-3" /> Converted
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleDownload(p.platform_id)}
                          className="flex-1 px-2 py-1 bg-[#111a11] border border-[#2a3e2a] hover:border-amber-500/50 hover:bg-[#1a2e1a] rounded text-xs text-white flex items-center justify-center gap-1"
                        >
                          <Download className="w-3 h-3" /> Download
                        </button>
                        <button
                          onClick={() => handleCopy(p.platform_id)}
                          className="flex-1 px-2 py-1 bg-[#111a11] border border-[#2a3e2a] hover:border-amber-500/50 hover:bg-[#1a2e1a] rounded text-xs text-white flex items-center justify-center gap-1"
                        >
                          <Copy className="w-3 h-3" />
                          {copied === p.platform_id ? "Copied!" : "Copy"}
                        </button>
                      </div>
                    </div>
                  ) : result?.error ? (
                    <div className="flex items-center gap-1 text-xs text-red-400">
                      <AlertTriangle className="w-3 h-3" /> Failed
                    </div>
                  ) : (
                    <button
                      onClick={() => handleExport(p.platform_id)}
                      disabled={isLoading}
                      className="w-full px-3 py-1.5 btn-primary disabled:opacity-50 text-xs flex items-center justify-center gap-1"
                    >
                      {isLoading ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        "Export"
                      )}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
