"use client";

import { useState, useEffect, useCallback } from "react";
import {
  GitBranch, RefreshCw, CheckCircle, XCircle, Clock, Loader2,
  AlertTriangle, Database, ToggleLeft, ToggleRight, ExternalLink,
  Download, Shield,
} from "lucide-react";
import {
  listRepos, getRepoSyncStatus, syncAllRepos, syncRepo, toggleRepo,
  type RepoInfo, type RepoSyncStatus,
} from "@/lib/api";

const PLATFORM_LABELS: Record<string, string> = {
  xsoar: "Cortex XSOAR",
  sentinel: "Microsoft Sentinel",
  fortisoar: "FortiSOAR",
  shuffle: "Shuffle",
  multi: "Multi-Platform",
};

const PLATFORM_COLORS: Record<string, string> = {
  xsoar: "bg-blue-600",
  sentinel: "bg-cyan-600",
  fortisoar: "bg-red-600",
  shuffle: "bg-orange-500",
  multi: "bg-amber-600",
};

const STATUS_CONFIG: Record<string, { icon: typeof CheckCircle; color: string; label: string }> = {
  synced: { icon: CheckCircle, color: "text-green-400", label: "Synced" },
  syncing: { icon: Loader2, color: "text-yellow-400", label: "Syncing..." },
  error: { icon: XCircle, color: "text-red-400", label: "Error" },
  pending: { icon: Clock, color: "text-[#7a7a6a]", label: "Pending" },
};

export default function ReposPage() {
  const [repos, setRepos] = useState<RepoInfo[]>([]);
  const [syncStatus, setSyncStatus] = useState<RepoSyncStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [filter, setFilter] = useState<string>("");

  const fetchData = useCallback(async () => {
    try {
      const [repoRes, statusRes] = await Promise.all([
        listRepos(),
        getRepoSyncStatus(),
      ]);
      setRepos(repoRes.repos);
      setSyncStatus(statusRes);
      setError("");
    } catch (err) {
      console.error("Failed to fetch repos:", err);
      setError("Could not connect to backend. Make sure the API server is running.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh while syncing
  useEffect(() => {
    if (!syncStatus?.is_syncing) return;
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [syncStatus?.is_syncing, fetchData]);

  const handleSyncAll = async () => {
    setSyncing(true);
    try {
      await syncAllRepos();
      // Start polling
      setTimeout(fetchData, 1000);
    } catch (err) {
      console.error("Sync failed:", err);
    } finally {
      setSyncing(false);
    }
  };

  const handleSyncOne = async (repoId: string) => {
    try {
      await syncRepo(repoId);
      setTimeout(fetchData, 1000);
    } catch (err) {
      console.error("Sync failed:", err);
    }
  };

  const handleToggle = async (repoId: string, enabled: boolean) => {
    try {
      await toggleRepo(repoId, enabled);
      setRepos((prev) =>
        prev.map((r) => (r.id === repoId ? { ...r, enabled } : r))
      );
    } catch (err) {
      console.error("Toggle failed:", err);
    }
  };

  const filtered = filter
    ? repos.filter((r) => r.platform === filter)
    : repos;

  const platforms = [...new Set(repos.map((r) => r.platform))];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Database className="w-6 h-6 text-amber-400" />
          Community Playbook Repos
        </h1>
        <button
          onClick={handleSyncAll}
          disabled={syncing || syncStatus?.is_syncing}
          className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white text-sm rounded hover:bg-amber-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`w-4 h-4 ${syncStatus?.is_syncing ? "animate-spin" : ""}`} />
          {syncStatus?.is_syncing ? "Syncing..." : "Sync All Repos"}
        </button>
      </div>

      {/* Stats Bar */}
      {syncStatus && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="bg-[#0f1a0f] border border-[#2a3e2a] rounded p-3 text-center">
            <p className="text-2xl font-bold text-[#d4d4c8]">{syncStatus.total_repos}</p>
            <p className="text-xs text-[#7a7a6a]">Total Repos</p>
          </div>
          <div className="bg-[#0f1a0f] border border-[#2a3e2a] rounded p-3 text-center">
            <p className="text-2xl font-bold text-green-400">{syncStatus.synced}</p>
            <p className="text-xs text-[#7a7a6a]">Synced</p>
          </div>
          <div className="bg-[#0f1a0f] border border-[#2a3e2a] rounded p-3 text-center">
            <p className="text-2xl font-bold text-yellow-400">{syncStatus.syncing}</p>
            <p className="text-xs text-[#7a7a6a]">Syncing</p>
          </div>
          <div className="bg-[#0f1a0f] border border-[#2a3e2a] rounded p-3 text-center">
            <p className="text-2xl font-bold text-red-400">{syncStatus.errors}</p>
            <p className="text-xs text-[#7a7a6a]">Errors</p>
          </div>
          <div className="bg-[#0f1a0f] border border-[#2a3e2a] rounded p-3 text-center">
            <p className="text-2xl font-bold text-amber-400">{syncStatus.total_playbooks_imported}</p>
            <p className="text-xs text-[#7a7a6a]">Imported</p>
          </div>
        </div>
      )}

      {/* Platform Filter */}
      <div className="flex flex-wrap gap-1.5">
        <button
          onClick={() => setFilter("")}
          className={`px-3 py-1.5 text-xs rounded-full transition ${
            !filter ? "bg-amber-600 text-white" : "bg-[#111a11] text-[#7a7a6a] hover:bg-[#1a2e1a]"
          }`}
        >
          All ({repos.length})
        </button>
        {platforms.map((p) => (
          <button
            key={p}
            onClick={() => setFilter(p)}
            className={`px-3 py-1.5 text-xs rounded-full transition ${
              filter === p ? "bg-amber-600 text-white" : "bg-[#111a11] text-[#7a7a6a] hover:bg-[#1a2e1a]"
            }`}
          >
            {PLATFORM_LABELS[p] || p} ({repos.filter((r) => r.platform === p).length})
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-16 text-[#7a7a6a]">
          <Loader2 className="w-6 h-6 mx-auto animate-spin mb-2" />
          Loading repos...
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <p className="text-sm text-red-300 flex-1">{error}</p>
          <button onClick={fetchData} className="px-3 py-1.5 text-xs bg-red-600/20 text-red-300 rounded hover:bg-red-600/30 transition">
            Retry
          </button>
        </div>
      )}

      {/* Repo Cards */}
      {!loading && !error && (
        <div className="space-y-3">
          {filtered.map((repo) => {
            const statusConf = STATUS_CONFIG[repo.status] || STATUS_CONFIG.pending;
            const StatusIcon = statusConf.icon;
            return (
              <div
                key={repo.id}
                className={`bg-[#0f1a0f] border rounded p-4 transition ${
                  repo.enabled ? "border-[#2a3e2a]" : "border-[#1a2e1a] opacity-60"
                }`}
              >
                <div className="flex items-start gap-4">
                  {/* Platform Badge */}
                  <div className={`w-10 h-10 ${PLATFORM_COLORS[repo.platform] || "bg-[#1a2e1a]"} rounded flex items-center justify-center shrink-0`}>
                    <Shield className="w-5 h-5 text-white" />
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-[#d4d4c8] truncate">{repo.name}</h3>
                      <span className={`inline-flex items-center gap-1 text-xs ${statusConf.color}`}>
                        <StatusIcon className={`w-3 h-3 ${repo.status === "syncing" ? "animate-spin" : ""}`} />
                        {statusConf.label}
                      </span>
                    </div>
                    <p className="text-xs text-[#7a7a6a] mb-2 line-clamp-1">{repo.description}</p>
                    <div className="flex items-center gap-3 text-xs text-[#7a7a6a]">
                      <span className={`px-1.5 py-0.5 rounded ${PLATFORM_COLORS[repo.platform] || "bg-[#1a2e1a]"} text-white text-[10px]`}>
                        {PLATFORM_LABELS[repo.platform] || repo.platform}
                      </span>
                      <span className="flex items-center gap-1">
                        <GitBranch className="w-3 h-3" />
                        {repo.branch}
                      </span>
                      {repo.playbooks_imported > 0 && (
                        <span className="flex items-center gap-1 text-green-400">
                          <Download className="w-3 h-3" />
                          {repo.playbooks_imported} imported
                        </span>
                      )}
                      {repo.playbooks_failed > 0 && (
                        <span className="text-red-400">
                          {repo.playbooks_failed} failed
                        </span>
                      )}
                      {repo.last_sync && (
                        <span>
                          Last: {new Date(repo.last_sync).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    {repo.error_message && (
                      <p className="text-xs text-red-400 mt-1 truncate">{repo.error_message}</p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <a
                      href={repo.url.replace(".git", "")}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 text-[#7a7a6a] hover:text-[#b0b0a0] transition"
                      title="Open on GitHub"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                    <button
                      onClick={() => handleSyncOne(repo.id)}
                      disabled={repo.status === "syncing"}
                      className="p-2 text-[#7a7a6a] hover:text-amber-400 transition disabled:opacity-50"
                      title="Sync this repo"
                    >
                      <RefreshCw className={`w-4 h-4 ${repo.status === "syncing" ? "animate-spin" : ""}`} />
                    </button>
                    <button
                      onClick={() => handleToggle(repo.id, !repo.enabled)}
                      className="p-2 text-[#7a7a6a] hover:text-[#b0b0a0] transition"
                      title={repo.enabled ? "Disable" : "Enable"}
                    >
                      {repo.enabled ? (
                        <ToggleRight className="w-5 h-5 text-green-400" />
                      ) : (
                        <ToggleLeft className="w-5 h-5 text-[#2a3e2a]" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Info */}
      <div className="text-xs text-[#2a3e2a] text-center pt-4">
        Repos are cloned as shallow copies. Set PLAYBOOKFORGE_AUTO_SYNC=true to sync on startup.
      </div>
    </div>
  );
}
