"use client";
import { useEffect, useState } from "react";
import {
  Shield,
  FileText,
  ExternalLink,
  Newspaper,
  Bot,
} from "lucide-react";
import {
  TacticalShield,
  IconConvert,
  IconLibrary,
  IconDesigner,
  IconAI,
  IconPlatform,
  IconIntegration,
  IconStats,
} from "@/components/TacticalIcons";
import Link from "next/link";
import {
  listPlatforms,
  healthCheck,
  libraryStats,
  listProducts,
  getIntegrationsStatus,
  getRecentThreats,
  type IntegrationInfo,
  type ThreatItem,
  type LibraryStatsResponse,
} from "@/lib/api";
import { PLATFORM_LOGOS } from "@/lib/types";
import { DashboardCharts } from "@/components/DashboardCharts";

export default function Dashboard() {
  const [platforms, setPlatforms] = useState<{ platform_id: string; platform_name: string; file_extension: string }[]>([]);
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [libStats, setLibStats] = useState<LibraryStatsResponse | null>(null);
  const [productCount, setProductCount] = useState(0);
  const [integrations, setIntegrations] = useState<IntegrationInfo[]>([]);
  const [threats, setThreats] = useState<ThreatItem[]>([]);
  const [integrationsLoading, setIntegrationsLoading] = useState(true);

  useEffect(() => {
    healthCheck().then(() => setHealthy(true)).catch(() => setHealthy(false));
    listPlatforms().then((d) => setPlatforms(d.platforms)).catch(() => {});
    libraryStats().then(setLibStats).catch(() => {});
    listProducts().then((d) => setProductCount(d.total)).catch(() => {});

    // Check integrations (with timeout since services may not be running)
    setIntegrationsLoading(true);
    getIntegrationsStatus()
      .then((res) => {
        setIntegrations(res.integrations);
        // If Blue-Team-News is connected, fetch threats
        const newsConnected = res.integrations.some((i) => i.name === "Blue-Team-News" && i.connected);
        if (newsConnected) {
          getRecentThreats(5).then((r) => setThreats(r.threats)).catch(() => {});
        }
      })
      .catch(() => {})
      .finally(() => setIntegrationsLoading(false));
  }, []);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Hero */}
      <div className="text-center py-8">
        <div className="flex items-center justify-center gap-3 mb-4">
          <TacticalShield size={48} />
          <h1 className="text-3xl font-bold">PlaybookForge</h1>
        </div>
        <p className="text-[#7a7a6a] text-lg max-w-xl mx-auto">
          Write a playbook <strong className="text-amber-400">ONCE</strong> in CACAO v2.0 — export to{" "}
          <strong className="text-amber-400">ANY</strong> SOAR platform.
        </p>
      </div>

      {/* Operations Overview Charts */}
      <DashboardCharts
        byPlatform={libStats?.by_platform ?? {}}
        totalPlaybooks={libStats?.total ?? 0}
        platformCount={platforms.length}
        productCount={productCount}
        activeIntegrations={integrations.filter((i) => i.connected).length}
        totalIntegrations={integrations.length || 3}
        healthy={healthy}
      />

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-[#111a11] border border-[#2a3e2a] rounded p-4 flex items-start gap-3">
          <IconLibrary size={32} />
          <div>
            <div className="text-2xl font-bold">{libStats?.total ?? "—"}</div>
            <div className="text-xs text-[#7a7a6a]">Playbooks in Library</div>
          </div>
        </div>
        <div className="bg-[#111a11] border border-[#2a3e2a] rounded p-4 flex items-start gap-3">
          <IconPlatform size={32} />
          <div>
            <div className="text-2xl font-bold">{platforms.length}</div>
            <div className="text-xs text-[#7a7a6a]">SOAR Platforms</div>
          </div>
        </div>
        <div className="bg-[#111a11] border border-[#2a3e2a] rounded p-4 flex items-start gap-3">
          <IconStats size={32} />
          <div>
            <div className="text-2xl font-bold">{productCount}</div>
            <div className="text-xs text-[#7a7a6a]">Security Products</div>
          </div>
        </div>
        <div className="bg-[#111a11] border border-[#2a3e2a] rounded p-4 flex items-start gap-3">
          <IconIntegration size={32} />
          <div>
            <div className="text-2xl font-bold">
              {integrationsLoading ? "..." : integrations.filter((i) => i.connected).length}/{integrations.length || 3}
            </div>
            <div className="text-xs text-[#7a7a6a]">Integrations Active</div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Link
          href="/convert"
          className="bg-[#111a11] border border-[#2a3e2a] rounded p-5 hover:border-amber-500 transition group"
        >
          <div className="mb-3 group-hover:scale-110 transition-transform"><IconConvert size={48} /></div>
          <h3 className="font-semibold mb-1">Convert</h3>
          <p className="text-sm text-[#7a7a6a]">Import & export playbooks between SOAR platforms.</p>
        </Link>
        <Link
          href="/playbooks"
          className="bg-[#111a11] border border-[#2a3e2a] rounded p-5 hover:border-amber-500 transition group"
        >
          <div className="mb-3 group-hover:scale-110 transition-transform"><IconLibrary size={48} /></div>
          <h3 className="font-semibold mb-1">Library</h3>
          <p className="text-sm text-[#7a7a6a]">{libStats?.total ?? 0} playbooks ready to use and customize.</p>
        </Link>
        <Link
          href="/designer"
          className="bg-[#111a11] border border-[#2a3e2a] rounded p-5 hover:border-amber-500 transition group"
        >
          <div className="mb-3 group-hover:scale-110 transition-transform"><IconDesigner size={48} /></div>
          <h3 className="font-semibold mb-1">Designer</h3>
          <p className="text-sm text-[#7a7a6a]">Build CACAO playbooks visually with step editor.</p>
        </Link>
        <Link
          href="/ai"
          className="bg-[#111a11] border border-[#2a3e2a] rounded p-5 hover:border-amber-500 transition group"
        >
          <div className="mb-3 group-hover:scale-110 transition-transform"><IconAI size={48} /></div>
          <h3 className="font-semibold mb-1">AI Generator</h3>
          <p className="text-sm text-[#7a7a6a]">Select products, describe scenario, get executable playbook.</p>
        </Link>
      </div>

      {/* Platform Status */}
      <div>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <IconPlatform size={24} />
          Supported Platforms ({platforms.length})
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {platforms.map((p) => {
            const logo = PLATFORM_LOGOS[p.platform_id] || { color: "bg-[#1a2e1a]", abbr: "??" };
            return (
              <div key={p.platform_id} className="bg-[#111a11] border border-[#2a3e2a] rounded p-3 text-center">
                <div className={`w-10 h-10 ${logo.color} rounded flex items-center justify-center text-white font-bold text-sm mx-auto mb-2`}>
                  {logo.abbr}
                </div>
                <p className="text-xs font-medium text-[#d4d4c8] truncate">{p.platform_name}</p>
                <p className="text-[10px] text-[#5a5a4a]">{p.file_extension}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Integrations */}
      <div>
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <IconIntegration size={24} />
          Blue Team Integrations
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {(integrations.length > 0 ? integrations : [
            { name: "Blue-Team-News", description: "Threat intelligence feed", url: "", connected: false, version: null, error: "Not checked" },
            { name: "Blue-Team-Assistant", description: "SOC analyst toolkit", url: "", connected: false, version: null, error: "Not checked" },
            { name: "MCP-For-SOC", description: "MCP server for Claude", url: "", connected: false, version: null, error: "Not checked" },
          ]).map((integration) => (
            <div
              key={integration.name}
              className="bg-[#111a11] border border-[#2a3e2a] rounded p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      integration.connected ? "bg-green-400" : "bg-[#1a2e1a]"
                    }`}
                  />
                  <h3 className="text-sm font-medium text-[#d4d4c8]">{integration.name}</h3>
                </div>
                {integration.version && (
                  <span className="text-[10px] text-[#5a5a4a]">v{integration.version}</span>
                )}
              </div>
              <p className="text-xs text-[#7a7a6a] mb-2">{integration.description}</p>
              <div className="text-[10px] text-[#5a5a4a]">
                {integration.connected ? (
                  <span className="text-green-400">Connected</span>
                ) : (
                  <span className="text-[#5a5a4a]">{integration.error || "Not running"}</span>
                )}
              </div>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-[#5a5a4a] mt-2">
          <a href="https://github.com/ugurrates" target="_blank" rel="noopener noreferrer" className="hover:text-[#7a7a6a] transition inline-flex items-center gap-1">
            <ExternalLink className="w-3 h-3" /> github.com/ugurrates — Blue Team Projects
          </a>
        </p>
      </div>

      {/* Recent Threats (only if Blue-Team-News is connected) */}
      {threats.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Newspaper className="w-5 h-5 text-red-400" />
            Recent Threats
            <span className="text-xs text-[#5a5a4a] font-normal ml-1">from Blue-Team-News</span>
          </h2>
          <div className="space-y-2">
            {threats.map((threat) => (
              <div key={threat.id} className="bg-[#111a11] border border-[#2a3e2a] rounded p-3 flex items-start gap-3">
                <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                  threat.severity === "critical" ? "bg-red-500" :
                  threat.severity === "high" ? "bg-orange-500" :
                  threat.severity === "medium" ? "bg-yellow-500" : "bg-blue-500"
                }`} />
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-[#d4d4c8] truncate">{threat.title}</h3>
                  {threat.description && (
                    <p className="text-xs text-[#7a7a6a] mt-0.5 line-clamp-1">{threat.description}</p>
                  )}
                  <div className="flex flex-wrap items-center gap-2 mt-1.5">
                    {threat.cve_ids.map((cve) => (
                      <Link
                        key={cve}
                        href={`/ai?prompt=${encodeURIComponent(`Create a response playbook for ${cve}`)}`}
                        className="px-1.5 py-0.5 text-[9px] bg-red-500/10 text-red-400 rounded hover:bg-red-500/20 transition"
                      >
                        {cve}
                      </Link>
                    ))}
                    {threat.tags.slice(0, 3).map((tag) => (
                      <span key={tag} className="px-1 py-0.5 text-[9px] bg-[#1a2e1a] text-[#5a5a4a] rounded">{tag}</span>
                    ))}
                    <span className="text-[9px] text-[#5a5a4a]">{threat.published}</span>
                  </div>
                </div>
                <Link
                  href={`/ai?prompt=${encodeURIComponent(`Create a playbook to respond to: ${threat.title}`)}`}
                  className="px-2 py-1 bg-amber-600/20 text-amber-400 rounded text-[10px] hover:bg-amber-600/30 transition shrink-0"
                >
                  <Bot className="w-3 h-3 inline mr-1" />
                  Generate
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Library Stats by Platform */}
      {libStats && Object.keys(libStats.by_platform).length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-[#7a7a6a]" />
            Library by Source Platform
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {Object.entries(libStats.by_platform).map(([platform, count]) => {
              const logo = PLATFORM_LOGOS[platform] || { color: "bg-[#1a2e1a]", abbr: platform.slice(0, 2).toUpperCase() };
              return (
                <Link
                  key={platform}
                  href={`/playbooks?platform=${platform}`}
                  className="bg-[#111a11] border border-[#2a3e2a] rounded p-3 text-center hover:border-amber-500 transition"
                >
                  <div className={`w-8 h-8 ${logo.color} rounded flex items-center justify-center text-white font-bold text-xs mx-auto mb-1`}>
                    {logo.abbr}
                  </div>
                  <p className="text-xs font-medium text-[#d4d4c8]">{platform}</p>
                  <p className="text-[10px] text-[#5a5a4a]">{count} playbooks</p>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* API Status */}
      <div className="flex items-center gap-2 text-sm">
        <div className={`w-2 h-2 rounded-full ${healthy === true ? "bg-green-400" : healthy === false ? "bg-red-400" : "bg-yellow-400 animate-pulse"}`} />
        <span className="text-[#7a7a6a]">
          API: {healthy === true ? "Connected" : healthy === false ? "Disconnected" : "Checking..."}
        </span>
        <span className="text-[#5a5a4a] text-xs ml-2">PlaybookForge v1.0.0</span>
      </div>
    </div>
  );
}
