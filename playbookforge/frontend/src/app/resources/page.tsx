"use client";

import { useState, useEffect, useCallback } from "react";
import { BookOpen, Search, Shield, Wrench, Zap, Loader2, AlertTriangle } from "lucide-react";
import ResourceCard from "@/components/ResourceCard";
import ResourceDetail from "@/components/ResourceDetail";
import {
  listBestPractices,
  listIntegrationGuides,
  searchResources,
  getEdrResources,
  type BestPracticeSummary,
  type IntegrationGuideSummary,
} from "@/lib/api";
import { RESOURCE_CATEGORY_LABELS, RESOURCE_CATEGORY_COLORS } from "@/lib/types";

const CATEGORIES = [
  { value: "", label: "All" },
  { value: "edr", label: "EDR / XDR" },
  { value: "siem", label: "SIEM" },
  { value: "email", label: "Email Security" },
  { value: "identity", label: "Identity / IAM" },
  { value: "firewall", label: "Firewall" },
  { value: "threat-intel", label: "Threat Intel" },
  { value: "cloud", label: "Cloud" },
  { value: "incident-response", label: "Incident Response" },
  { value: "general", label: "General" },
];

const DIFFICULTIES = [
  { value: "", label: "All Levels" },
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

export default function ResourcesPage() {
  const [bestPractices, setBestPractices] = useState<BestPracticeSummary[]>([]);
  const [guides, setGuides] = useState<IntegrationGuideSummary[]>([]);
  const [edrData, setEdrData] = useState<{
    best_practices: BestPracticeSummary[];
    integration_guides: IntegrationGuideSummary[];
    total: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<(BestPracticeSummary | IntegrationGuideSummary)[] | null>(null);
  const [category, setCategory] = useState("");
  const [difficulty, setDifficulty] = useState("");

  // Detail view
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<"best-practice" | "integration-guide">("best-practice");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [bpRes, guideRes, edr] = await Promise.all([
        listBestPractices(category || undefined, difficulty || undefined),
        listIntegrationGuides(category || undefined),
        !category && !difficulty ? getEdrResources() : Promise.resolve(null),
      ]);
      setBestPractices(bpRes.best_practices);
      setGuides(guideRes.integration_guides);
      if (edr) setEdrData(edr);
    } catch (err) {
      console.error("Failed to fetch resources:", err);
      setBestPractices([]);
      setGuides([]);
      setError("Could not connect to backend. Make sure the API server is running on localhost:8002.");
    } finally {
      setLoading(false);
    }
  }, [category, difficulty]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await searchResources(searchQuery);
        setSearchResults(res.results);
      } catch (err) {
        console.error("Search failed:", err);
        setSearchResults([]);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleSelectResource = (id: string, type: "best-practice" | "integration-guide") => {
    setSelectedId(id);
    setSelectedType(type);
  };

  // Detail view
  if (selectedId) {
    return (
      <div className="max-w-4xl mx-auto">
        <ResourceDetail
          id={selectedId}
          type={selectedType}
          onBack={() => setSelectedId(null)}
        />
      </div>
    );
  }

  const displayItems = searchResults !== null ? searchResults : null;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-amber-400" />
          Resources & Best Practices
        </h1>
        <span className="text-sm text-[#7a7a6a]">
          {bestPractices.length + guides.length} resources
        </span>
      </div>

      {/* EDR Spotlight */}
      {!category && !searchQuery && edrData && edrData.total > 0 && (
        <div className="bg-gradient-to-r from-red-900/30 to-[#080d08] border border-red-800/30 rounded p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-red-600 rounded flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">EDR Spotlight</h2>
              <p className="text-xs text-[#7a7a6a]">{edrData.total} EDR-specific resources — detection, response, and forensics</p>
            </div>
            <button
              onClick={() => setCategory("edr")}
              className="ml-auto px-3 py-1.5 bg-red-600/20 text-red-300 text-xs rounded hover:bg-red-600/30 transition"
            >
              View All EDR
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {[...edrData.best_practices.slice(0, 2), ...edrData.integration_guides.slice(0, 2)].map((item) => (
              <button
                key={item.id}
                onClick={() => handleSelectResource(item.id, item.type as "best-practice" | "integration-guide")}
                className="flex items-center gap-3 p-3 bg-[#111a11]/60 rounded hover:bg-[#1a2e1a] transition text-left"
              >
                {item.type === "best-practice" ? (
                  <BookOpen className="w-4 h-4 text-red-400 shrink-0" />
                ) : (
                  <Wrench className="w-4 h-4 text-red-400 shrink-0" />
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium text-[#d4d4c8] truncate">{item.title}</p>
                  <p className="text-[10px] text-[#7a7a6a] capitalize">{item.type.replace("-", " ")} &middot; {item.step_count} steps</p>
                </div>
                <Zap className="w-3 h-3 text-[#2a3e2a] shrink-0" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Search & Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#7a7a6a]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search resources..."
            className="w-full pl-10 pr-4 py-2 bg-[#0f1a0f] border border-[#2a3e2a] rounded text-sm text-[#d4d4c8] focus:outline-none focus:border-amber-500"
          />
        </div>
        <select
          value={difficulty}
          onChange={(e) => { setDifficulty(e.target.value); setSearchQuery(""); }}
          className="px-3 py-2 bg-[#0f1a0f] border border-[#2a3e2a] rounded text-sm text-[#d4d4c8] focus:outline-none focus:border-amber-500"
        >
          {DIFFICULTIES.map((d) => (
            <option key={d.value} value={d.value}>{d.label}</option>
          ))}
        </select>
      </div>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-1.5">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.value}
            onClick={() => { setCategory(cat.value); setSearchQuery(""); }}
            className={`px-3 py-1.5 text-xs rounded-full transition ${
              category === cat.value
                ? "bg-amber-600 text-white"
                : "bg-[#111a11] text-[#7a7a6a] hover:bg-[#1a2e1a]"
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-16 text-[#7a7a6a]">
          <Loader2 className="w-6 h-6 mx-auto animate-spin mb-2" />
          Loading resources...
        </div>
      )}

      {/* Error Banner */}
      {!loading && error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <div className="flex-1">
            <p className="text-sm text-red-300">{error}</p>
          </div>
          <button
            onClick={fetchData}
            className="px-3 py-1.5 text-xs bg-red-600/20 text-red-300 rounded hover:bg-red-600/30 transition"
          >
            Retry
          </button>
        </div>
      )}

      {/* Search Results */}
      {!loading && displayItems !== null && (
        <div className="space-y-4">
          <h2 className="text-sm font-medium text-[#7a7a6a]">
            Search Results ({displayItems.length})
          </h2>
          {displayItems.length === 0 ? (
            <p className="text-center py-8 text-[#7a7a6a] text-sm">No results found.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {displayItems.map((item) => (
                <ResourceCard
                  key={item.id}
                  {...item}
                  type={item.type as "best-practice" | "integration-guide"}
                  onClick={() => handleSelectResource(item.id, item.type as "best-practice" | "integration-guide")}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Browse View */}
      {!loading && displayItems === null && (
        <>
          {/* Best Practices */}
          {bestPractices.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-amber-400" />
                Best Practices
                <span className="text-xs text-[#7a7a6a] font-normal">({bestPractices.length})</span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {bestPractices.map((bp) => (
                  <ResourceCard
                    key={bp.id}
                    {...bp}
                    type="best-practice"
                    onClick={() => handleSelectResource(bp.id, "best-practice")}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Integration Guides */}
          {guides.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Wrench className="w-5 h-5 text-amber-400" />
                Integration Guides
                <span className="text-xs text-[#7a7a6a] font-normal">({guides.length})</span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {guides.map((g) => (
                  <ResourceCard
                    key={g.id}
                    {...g}
                    type="integration-guide"
                    onClick={() => handleSelectResource(g.id, "integration-guide")}
                  />
                ))}
              </div>
            </div>
          )}

          {bestPractices.length === 0 && guides.length === 0 && (
            <div className="text-center py-16 text-[#7a7a6a]">
              <BookOpen className="w-12 h-12 mx-auto mb-3 text-[#2a3e2a]" />
              <p>No resources found for this filter.</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
