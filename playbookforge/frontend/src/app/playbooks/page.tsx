"use client";
import { useState, useEffect, useCallback } from "react";
import { FileText, Upload, Eye, Search, Filter, ArrowLeft, Database, Tag, Layers, ArrowLeftRight, Download, Workflow, FolderOpen } from "lucide-react";
import { StepList } from "@/components/StepList";
import { PlaybookViewer } from "@/components/PlaybookViewer";
import { ExportModal } from "@/components/ExportModal";
import PdfDownloadButton from "@/components/PdfDownloadButton";
import FileUploadZone from "@/components/FileUploadZone";
import FileList from "@/components/FileList";
import { PLATFORM_LOGOS } from "@/lib/types";
import type { CacaoPlaybook } from "@/lib/types";
import { libraryList, libraryStats, libraryGet, type LibraryEntry, type LibraryStatsResponse } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function PlaybooksPage() {
  const router = useRouter();
  const [entries, setEntries] = useState<LibraryEntry[]>([]);
  const [stats, setStats] = useState<LibraryStatsResponse | null>(null);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [platformFilter, setPlatformFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const limit = 24;

  // Detail view state
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedPlaybook, setSelectedPlaybook] = useState<CacaoPlaybook | null>(null);
  const [selectedMeta, setSelectedMeta] = useState<LibraryEntry | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [view, setView] = useState<"steps" | "json" | "files">("steps");
  const [showExport, setShowExport] = useState(false);
  const [fileRefreshKey, setFileRefreshKey] = useState(0);

  const handleOpenInDesigner = () => {
    if (selectedPlaybook) {
      sessionStorage.setItem("playbookforge_designer_input", JSON.stringify(selectedPlaybook));
      router.push("/designer");
    }
  };

  const handleOpenInConvert = () => {
    if (selectedPlaybook) {
      sessionStorage.setItem("playbookforge_convert_input", JSON.stringify(selectedPlaybook, null, 2));
      router.push("/convert");
    }
  };

  const fetchPlaybooks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await libraryList({
        search: search || undefined,
        platform: platformFilter || undefined,
        tag: tagFilter || undefined,
        limit,
        offset,
      });
      setEntries(res.playbooks);
      setTotal(res.total);
    } catch {
      setEntries([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [search, platformFilter, tagFilter, offset]);

  useEffect(() => {
    fetchPlaybooks();
  }, [fetchPlaybooks]);

  useEffect(() => {
    libraryStats().then(setStats).catch(() => {});
  }, []);

  const handleSelect = async (id: string) => {
    setDetailLoading(true);
    setSelectedId(id);
    try {
      const full = await libraryGet(id);
      setSelectedMeta(full);
      if (full.cacao_playbook) {
        setSelectedPlaybook(full.cacao_playbook as unknown as CacaoPlaybook);
      }
    } catch {
      setSelectedPlaybook(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleBack = () => {
    setSelectedId(null);
    setSelectedPlaybook(null);
    setSelectedMeta(null);
    setView("steps");
  };

  // Detail view
  if (selectedId && selectedMeta) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <button onClick={handleBack} className="flex items-center gap-2 text-sm text-[#7a7a6a] hover:text-[#d4d4c8] transition">
          <ArrowLeft className="w-4 h-4" /> Back to Library
        </button>

        {detailLoading ? (
          <div className="text-center py-20 text-[#7a7a6a]">Loading playbook...</div>
        ) : (
          <div className="space-y-6">
            {/* Header */}
            <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5">
              <div className="flex items-start gap-4">
                <div className={`w-12 h-12 ${(PLATFORM_LOGOS[selectedMeta.source_platform] || { color: "bg-[#1a2e1a]" }).color} rounded flex items-center justify-center text-white font-bold text-sm shrink-0`}>
                  {(PLATFORM_LOGOS[selectedMeta.source_platform] || { abbr: "??" }).abbr}
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="text-xl font-semibold">{selectedMeta.name}</h2>
                  {selectedMeta.description && (
                    <p className="text-sm text-[#7a7a6a] mt-1">{selectedMeta.description}</p>
                  )}
                  <div className="flex flex-wrap gap-2 mt-3">
                    <span className="px-2 py-0.5 text-xs bg-amber-500/20 text-amber-300 rounded">
                      {selectedMeta.step_count} steps
                    </span>
                    <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-300 rounded">
                      {selectedMeta.action_count} actions
                    </span>
                    <span className="px-2 py-0.5 text-xs bg-[#1a2e1a] text-[#d4d4c8] rounded">
                      {selectedMeta.source_platform}
                    </span>
                    {selectedMeta.playbook_types.map((t) => (
                      <span key={t} className="px-2 py-0.5 text-xs bg-[#1a2e1a] text-[#7a7a6a] rounded">{t}</span>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {selectedMeta.tags.map((tag) => (
                      <span key={tag} className="px-1.5 py-0.5 text-[10px] bg-[#111a11] text-[#7a7a6a] rounded">{tag}</span>
                    ))}
                  </div>
                  {selectedMeta.mitre_techniques.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {selectedMeta.mitre_techniques.map((t) => (
                        <a key={t} href={`https://attack.mitre.org/techniques/${t.replace(".", "/")}/`} target="_blank" rel="noopener noreferrer"
                          className="px-1.5 py-0.5 text-[10px] bg-red-500/10 text-red-400 rounded hover:bg-red-500/20 transition">
                          {t}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setShowExport(true)}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded text-sm font-medium flex items-center gap-2 text-white"
              >
                <Download className="w-4 h-4" /> Export to...
              </button>
              <PdfDownloadButton
                libraryId={selectedId || undefined}
                playbook={selectedPlaybook as unknown as Record<string, unknown>}
                label="Download PDF"
                className="px-4 py-2 text-sm"
              />
              <button
                onClick={handleOpenInDesigner}
                className="px-4 py-2 bg-[#1a2e1a] hover:bg-[#1a2e1a] rounded text-sm font-medium flex items-center gap-2 text-white"
              >
                <Workflow className="w-4 h-4" /> Open in Designer
              </button>
              <button
                onClick={handleOpenInConvert}
                className="px-4 py-2 bg-[#1a2e1a] hover:bg-[#1a2e1a] rounded text-sm font-medium flex items-center gap-2 text-white"
              >
                <ArrowLeftRight className="w-4 h-4" /> Open in Convert
              </button>
            </div>

            {/* View toggle */}
            <div className="flex gap-2">
              <button onClick={() => setView("steps")}
                className={`px-3 py-1.5 rounded text-sm ${view === "steps" ? "bg-amber-600" : "bg-[#111a11] text-[#7a7a6a]"}`}>
                Steps
              </button>
              <button onClick={() => setView("json")}
                className={`px-3 py-1.5 rounded text-sm ${view === "json" ? "bg-amber-600" : "bg-[#111a11] text-[#7a7a6a]"}`}>
                CACAO JSON
              </button>
              <button onClick={() => setView("files")}
                className={`px-3 py-1.5 rounded text-sm flex items-center gap-1.5 ${view === "files" ? "bg-amber-600" : "bg-[#111a11] text-[#7a7a6a]"}`}>
                <FolderOpen className="w-3.5 h-3.5" /> Files
              </button>
            </div>

            {/* Content */}
            <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5">
              {view === "steps" && selectedPlaybook ? (
                <StepList workflow={selectedPlaybook.workflow} workflowStart={selectedPlaybook.workflow_start} />
              ) : view === "json" && selectedPlaybook ? (
                <PlaybookViewer content={JSON.stringify(selectedPlaybook, null, 2)} filename={`${selectedMeta.name}.json`} />
              ) : view === "files" ? (
                <div className="space-y-4">
                  <h3 className="text-sm font-medium text-[#d4d4c8]">Uploaded Documents</h3>
                  <FileUploadZone
                    playbookId={selectedId || undefined}
                    onUploaded={() => setFileRefreshKey((k) => k + 1)}
                  />
                  <FileList playbookId={selectedId || undefined} refreshKey={fileRefreshKey} />
                </div>
              ) : (
                <p className="text-[#7a7a6a] text-sm">Playbook data not available.</p>
              )}
            </div>
          </div>
        )}

        {/* Export Modal */}
        {showExport && selectedPlaybook && (
          <ExportModal
            playbook={selectedPlaybook as unknown as Record<string, unknown>}
            onClose={() => setShowExport(false)}
          />
        )}
      </div>
    );
  }

  // Library browse view
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Database className="w-6 h-6 text-amber-400" />
          Playbook Library
        </h1>
        {stats && (
          <span className="text-sm text-[#7a7a6a]">{stats.total} playbooks</span>
        )}
      </div>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {Object.entries(stats.by_platform).map(([platform, count]) => {
            const logo = PLATFORM_LOGOS[platform] || { color: "bg-[#1a2e1a]", abbr: platform.slice(0, 2).toUpperCase() };
            return (
              <button
                key={platform}
                onClick={() => { setPlatformFilter(platformFilter === platform ? "" : platform); setOffset(0); }}
                className={`p-3 rounded border text-center transition ${
                  platformFilter === platform
                    ? "border-amber-500 bg-amber-500/10"
                    : "border-[#2a3e2a] bg-[#111a11] hover:border-[#2a3e2a]"
                }`}
              >
                <div className={`w-8 h-8 ${logo.color} rounded flex items-center justify-center text-white font-bold text-xs mx-auto mb-1`}>
                  {logo.abbr}
                </div>
                <p className="text-xs font-medium text-[#d4d4c8]">{platform}</p>
                <p className="text-[10px] text-[#7a7a6a]">{count} playbooks</p>
              </button>
            );
          })}
        </div>
      )}

      {/* Search & filters */}
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#7a7a6a]" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
            placeholder="Search playbooks by name, description, or tag..."
            className="w-full pl-10 pr-4 py-2 bg-[#0f1a0f] border border-[#2a3e2a] rounded text-sm text-[#d4d4c8] focus:outline-none focus:border-amber-500"
          />
        </div>
        {(search || platformFilter || tagFilter) && (
          <button
            onClick={() => { setSearch(""); setPlatformFilter(""); setTagFilter(""); setOffset(0); }}
            className="px-3 py-2 bg-[#111a11] text-[#7a7a6a] rounded text-sm hover:text-[#d4d4c8] transition"
          >
            Clear
          </button>
        )}
      </div>

      {/* Top tags */}
      {stats && !tagFilter && (
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(stats.top_tags).slice(0, 15).map(([tag, count]) => (
            <button
              key={tag}
              onClick={() => { setTagFilter(tag); setOffset(0); }}
              className="px-2 py-1 text-xs bg-[#111a11] text-[#7a7a6a] rounded hover:bg-[#1a2e1a] hover:text-[#d4d4c8] transition"
            >
              {tag} <span className="text-[#2a3e2a]">({count})</span>
            </button>
          ))}
        </div>
      )}

      {tagFilter && (
        <div className="flex items-center gap-2">
          <Tag className="w-4 h-4 text-amber-400" />
          <span className="text-sm text-[#d4d4c8]">Tag: {tagFilter}</span>
          <button onClick={() => { setTagFilter(""); setOffset(0); }} className="text-xs text-[#7a7a6a] hover:text-[#b0b0a0]">×</button>
        </div>
      )}

      {/* Results */}
      {loading ? (
        <div className="text-center py-20 text-[#7a7a6a]">Loading...</div>
      ) : entries.length === 0 ? (
        <div className="text-center py-20 text-[#7a7a6a]">
          <FileText className="w-12 h-12 mx-auto mb-3 text-[#2a3e2a]" />
          <p>No playbooks found.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {entries.map((entry) => {
              const logo = PLATFORM_LOGOS[entry.source_platform] || { color: "bg-[#1a2e1a]", abbr: "??" };
              return (
                <button
                  key={entry.id}
                  onClick={() => handleSelect(entry.id)}
                  className="bg-[#111a11] border border-[#2a3e2a] rounded p-4 text-left hover:border-amber-500 transition group"
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-9 h-9 ${logo.color} rounded flex items-center justify-center text-white font-bold text-xs shrink-0`}>
                      {logo.abbr}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-medium text-[#d4d4c8] truncate group-hover:text-amber-300 transition">
                        {entry.name}
                      </h3>
                      <p className="text-xs text-[#7a7a6a] mt-0.5 line-clamp-2">{entry.description}</p>
                      <div className="flex items-center gap-2 mt-2 text-[10px] text-[#7a7a6a]">
                        <span className="flex items-center gap-1">
                          <Layers className="w-3 h-3" /> {entry.step_count} steps
                        </span>
                        <span>•</span>
                        <span>{entry.action_count} actions</span>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {entry.tags.slice(0, 3).map((tag) => (
                          <span key={tag} className="px-1 py-0.5 text-[9px] bg-[#1a2e1a]/50 text-[#7a7a6a] rounded">{tag}</span>
                        ))}
                        {entry.tags.length > 3 && (
                          <span className="px-1 py-0.5 text-[9px] text-[#2a3e2a]">+{entry.tags.length - 3}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Pagination */}
          {total > limit && (
            <div className="flex items-center justify-center gap-4">
              <button
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="px-3 py-1.5 bg-[#111a11] text-sm rounded disabled:opacity-30 hover:bg-[#1a2e1a] transition"
              >
                Previous
              </button>
              <span className="text-sm text-[#7a7a6a]">
                {offset + 1}–{Math.min(offset + limit, total)} of {total}
              </span>
              <button
                onClick={() => setOffset(offset + limit)}
                disabled={offset + limit >= total}
                className="px-3 py-1.5 bg-[#111a11] text-sm rounded disabled:opacity-30 hover:bg-[#1a2e1a] transition"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
