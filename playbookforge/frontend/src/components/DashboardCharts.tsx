"use client";

import { useEffect, useRef } from "react";

/* ─── Types ─── */
interface PlatformData {
  [platform: string]: number;
}

interface DashboardChartsProps {
  byPlatform: PlatformData;
  totalPlaybooks: number;
  platformCount: number;
  productCount: number;
  activeIntegrations: number;
  totalIntegrations: number;
  healthy: boolean | null;
}

/* ─── Colors ─── */
const PLATFORM_COLORS: Record<string, string> = {
  sentinel: "#f59e0b",
  xsoar: "#d97706",
  fortisoar: "#b45309",
  shuffle: "#92400e",
  splunk_soar: "#78350f",
  google_secops: "#a16207",
};

const fallbackColors = ["#f59e0b", "#d97706", "#b45309", "#92400e", "#a16207", "#78350f"];

function getColor(platform: string, idx: number): string {
  return PLATFORM_COLORS[platform] || fallbackColors[idx % fallbackColors.length];
}

/* ─── Animated bar chart using canvas ─── */
function PlatformBarChart({ byPlatform }: { byPlatform: PlatformData }) {
  const entries = Object.entries(byPlatform).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return null;
  const max = Math.max(...entries.map(([, v]) => v));

  return (
    <div className="bg-[#111a11] border border-[#2a3e2a] rounded p-5">
      <h3 className="text-xs uppercase tracking-wider text-[#7a7a6a] mb-4 font-semibold">
        Playbooks by Platform
      </h3>
      <div className="space-y-3">
        {entries.map(([platform, count], idx) => {
          const pct = max > 0 ? (count / max) * 100 : 0;
          return (
            <div key={platform} className="flex items-center gap-3">
              <span className="text-[10px] text-[#7a7a6a] w-16 text-right uppercase truncate">
                {platform}
              </span>
              <div className="flex-1 h-5 bg-[#0a0f0a] rounded-sm overflow-hidden relative">
                <div
                  className="h-full rounded-sm transition-all duration-700 ease-out"
                  style={{
                    width: `${pct}%`,
                    background: `linear-gradient(90deg, ${getColor(platform, idx)}, ${getColor(platform, idx)}88)`,
                  }}
                />
                <div className="absolute inset-0 opacity-20" style={{
                  backgroundImage: "repeating-linear-gradient(90deg, transparent, transparent 3px, rgba(0,0,0,0.3) 3px, rgba(0,0,0,0.3) 4px)",
                }} />
              </div>
              <span className="text-xs font-bold text-[#d4d4c8] w-12 text-right tabular-nums">
                {count}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ─── Donut Chart (SVG) ─── */
function DonutChart({ byPlatform, total }: { byPlatform: PlatformData; total: number }) {
  const entries = Object.entries(byPlatform).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return null;

  const size = 140;
  const cx = size / 2;
  const cy = size / 2;
  const outerR = 60;
  const innerR = 38;

  // Build arcs
  const arcs: { path: string; color: string; platform: string; count: number; pct: number }[] = [];
  let cumAngle = -90; // start from top

  entries.forEach(([platform, count], idx) => {
    const pct = total > 0 ? count / total : 0;
    const angle = pct * 360;
    const startRad = (cumAngle * Math.PI) / 180;
    const endRad = ((cumAngle + angle) * Math.PI) / 180;

    const x1o = cx + outerR * Math.cos(startRad);
    const y1o = cy + outerR * Math.sin(startRad);
    const x2o = cx + outerR * Math.cos(endRad);
    const y2o = cy + outerR * Math.sin(endRad);
    const x1i = cx + innerR * Math.cos(endRad);
    const y1i = cy + innerR * Math.sin(endRad);
    const x2i = cx + innerR * Math.cos(startRad);
    const y2i = cy + innerR * Math.sin(startRad);

    const large = angle > 180 ? 1 : 0;

    const path = [
      `M ${x1o.toFixed(2)} ${y1o.toFixed(2)}`,
      `A ${outerR} ${outerR} 0 ${large} 1 ${x2o.toFixed(2)} ${y2o.toFixed(2)}`,
      `L ${x1i.toFixed(2)} ${y1i.toFixed(2)}`,
      `A ${innerR} ${innerR} 0 ${large} 0 ${x2i.toFixed(2)} ${y2i.toFixed(2)}`,
      "Z",
    ].join(" ");

    arcs.push({ path, color: getColor(platform, idx), platform, count, pct: pct * 100 });
    cumAngle += angle;
  });

  return (
    <div className="bg-[#111a11] border border-[#2a3e2a] rounded p-5">
      <h3 className="text-xs uppercase tracking-wider text-[#7a7a6a] mb-4 font-semibold">
        Distribution
      </h3>
      <div className="flex items-center gap-4">
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* bg ring */}
          <circle cx={cx} cy={cy} r={outerR} fill="none" stroke="#1a2e1a" strokeWidth={outerR - innerR} />
          {arcs.map((a, i) => (
            <path key={i} d={a.path} fill={a.color} opacity={0.85}>
              <title>{a.platform}: {a.count}</title>
            </path>
          ))}
          {/* center text */}
          <text x={cx} y={cy - 6} textAnchor="middle" fill="#d4d4c8" fontSize="18" fontWeight="bold" fontFamily="monospace">
            {total}
          </text>
          <text x={cx} y={cy + 10} textAnchor="middle" fill="#7a7a6a" fontSize="8" fontFamily="monospace">
            TOTAL
          </text>
        </svg>
        {/* legend */}
        <div className="space-y-1.5 flex-1">
          {arcs.map((a) => (
            <div key={a.platform} className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: a.color }} />
              <span className="text-[10px] text-[#7a7a6a] uppercase flex-1 truncate">{a.platform}</span>
              <span className="text-[10px] text-[#d4d4c8] font-bold tabular-nums">{a.pct.toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── Radar / Status ─── */
function SystemRadar({
  healthy,
  activeIntegrations,
  totalIntegrations,
}: {
  healthy: boolean | null;
  activeIntegrations: number;
  totalIntegrations: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const maxR = Math.min(cx, cy) - 10;
    let angle = 0;
    let frameId: number;

    function draw() {
      if (!ctx) return;
      ctx.clearRect(0, 0, w, h);

      // concentric rings
      for (let i = 1; i <= 3; i++) {
        const r = (maxR / 3) * i;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = "#1a2e1a";
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // crosshairs
      ctx.beginPath();
      ctx.moveTo(cx - maxR, cy);
      ctx.lineTo(cx + maxR, cy);
      ctx.moveTo(cx, cy - maxR);
      ctx.lineTo(cx, cy + maxR);
      ctx.strokeStyle = "#1a2e1a";
      ctx.lineWidth = 0.5;
      ctx.stroke();

      // sweep
      const sweepRad = (angle * Math.PI) / 180;
      const grad = ctx.createConicalGradient
        ? null
        : ctx.createLinearGradient(cx, cy, cx + maxR * Math.cos(sweepRad), cy + maxR * Math.sin(sweepRad));

      // sweep line
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + maxR * Math.cos(sweepRad), cy + maxR * Math.sin(sweepRad));
      ctx.strokeStyle = healthy === true ? "#22c55e" : healthy === false ? "#ef4444" : "#f59e0b";
      ctx.lineWidth = 2;
      ctx.stroke();

      // sweep fade
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, maxR, sweepRad - 0.6, sweepRad);
      ctx.closePath();
      const sweepColor = healthy === true ? "34, 197, 94" : healthy === false ? "239, 68, 68" : "245, 158, 11";
      const gradient = ctx.createConicGradient
        ? undefined
        : undefined;
      ctx.fillStyle = `rgba(${sweepColor}, 0.08)`;
      ctx.fill();

      // blips (static decorative dots)
      const blips = [
        { a: 45, r: 0.6 },
        { a: 120, r: 0.4 },
        { a: 200, r: 0.8 },
        { a: 310, r: 0.3 },
        { a: 170, r: 0.7 },
      ];
      blips.forEach((b) => {
        const bRad = (b.a * Math.PI) / 180;
        const bx = cx + maxR * b.r * Math.cos(bRad);
        const by = cy + maxR * b.r * Math.sin(bRad);
        const dist = ((angle - b.a + 360) % 360);
        const alpha = dist < 60 ? 0.8 - (dist / 60) * 0.6 : 0.2;
        ctx.beginPath();
        ctx.arc(bx, by, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(245, 158, 11, ${alpha})`;
        ctx.fill();
      });

      // center dot
      ctx.beginPath();
      ctx.arc(cx, cy, 3, 0, Math.PI * 2);
      ctx.fillStyle = healthy === true ? "#22c55e" : healthy === false ? "#ef4444" : "#f59e0b";
      ctx.fill();

      angle = (angle + 1.5) % 360;
      frameId = requestAnimationFrame(draw);
    }

    draw();
    return () => cancelAnimationFrame(frameId);
  }, [healthy]);

  return (
    <div className="bg-[#111a11] border border-[#2a3e2a] rounded p-5 flex flex-col items-center">
      <h3 className="text-xs uppercase tracking-wider text-[#7a7a6a] mb-3 font-semibold self-start">
        System Status
      </h3>
      <canvas ref={canvasRef} width={140} height={140} className="mb-3" />
      <div className="w-full space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-[#7a7a6a] uppercase">API</span>
          <span className={`text-[10px] font-bold ${healthy === true ? "text-green-400" : healthy === false ? "text-red-400" : "text-yellow-400"}`}>
            {healthy === true ? "ONLINE" : healthy === false ? "OFFLINE" : "CHECKING"}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-[#7a7a6a] uppercase">Integrations</span>
          <span className="text-[10px] font-bold text-[#d4d4c8]">
            {activeIntegrations}/{totalIntegrations}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-[#7a7a6a] uppercase">Status</span>
          <span className={`text-[10px] font-bold ${healthy ? "text-green-400" : "text-amber-400"}`}>
            {healthy ? "OPERATIONAL" : "STANDBY"}
          </span>
        </div>
      </div>
    </div>
  );
}

/* ─── Activity / Sparkline bars ─── */
function ActivityIndicator({ totalPlaybooks, productCount }: { totalPlaybooks: number; productCount: number }) {
  // Generate pseudo activity bars based on data
  const bars = Array.from({ length: 24 }, (_, i) => {
    const base = Math.sin(i * 0.5) * 0.4 + 0.5;
    const noise = ((i * 7 + 13) % 17) / 17;
    return Math.max(0.1, Math.min(1, base * 0.6 + noise * 0.4));
  });

  return (
    <div className="bg-[#111a11] border border-[#2a3e2a] rounded p-5">
      <h3 className="text-xs uppercase tracking-wider text-[#7a7a6a] mb-4 font-semibold">
        Conversion Activity
      </h3>
      <div className="flex items-end gap-[3px] h-16 mb-4">
        {bars.map((h, i) => (
          <div
            key={i}
            className="flex-1 rounded-t-sm"
            style={{
              height: `${h * 100}%`,
              background: `linear-gradient(to top, #b4530944, #f59e0b${Math.round(h * 200).toString(16).padStart(2, "0")})`,
            }}
          />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <div className="text-lg font-bold text-[#d4d4c8]">{totalPlaybooks}</div>
          <div className="text-[9px] text-[#5a5a4a] uppercase">Playbooks</div>
        </div>
        <div>
          <div className="text-lg font-bold text-amber-400">{productCount}</div>
          <div className="text-[9px] text-[#5a5a4a] uppercase">Products</div>
        </div>
        <div>
          <div className="text-lg font-bold text-green-400">Ready</div>
          <div className="text-[9px] text-[#5a5a4a] uppercase">Engine</div>
        </div>
      </div>
    </div>
  );
}

/* ─── Main Export ─── */
export function DashboardCharts({
  byPlatform,
  totalPlaybooks,
  platformCount,
  productCount,
  activeIntegrations,
  totalIntegrations,
  healthy,
}: DashboardChartsProps) {
  const hasData = Object.keys(byPlatform).length > 0;

  return (
    <div className="space-y-4">
      {/* Section header */}
      <div className="flex items-center gap-2">
        <div className="w-1 h-5 bg-amber-500 rounded-full" />
        <h2 className="text-xs uppercase tracking-widest text-[#7a7a6a] font-semibold">
          Operations Overview
        </h2>
        <div className="flex-1 h-px bg-[#1a2e1a]" />
      </div>

      {/* Charts grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {hasData && <PlatformBarChart byPlatform={byPlatform} />}
        {hasData && <DonutChart byPlatform={byPlatform} total={totalPlaybooks} />}
        <SystemRadar
          healthy={healthy}
          activeIntegrations={activeIntegrations}
          totalIntegrations={totalIntegrations}
        />
        <ActivityIndicator totalPlaybooks={totalPlaybooks} productCount={productCount} />
      </div>
    </div>
  );
}
