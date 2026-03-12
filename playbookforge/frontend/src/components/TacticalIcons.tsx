/**
 * Tactical / Military-style SVG icons for PlaybookForge
 * Inspired by olive-gold cybersecurity military aesthetic
 */

interface IconProps {
  className?: string;
  size?: number;
}

// Shield with circuit lines — main brand icon
export function TacticalShield({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="shield-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Shield body */}
      <path d="M32 4L8 16v16c0 14.4 10.2 27.8 24 32 13.8-4.2 24-17.6 24-32V16L32 4z"
        fill="none" stroke="url(#shield-grad)" strokeWidth="2.5"/>
      <path d="M32 10L14 20v12c0 11.4 7.8 22 18 25.6 10.2-3.6 18-14.2 18-25.6V20L32 10z"
        fill="#d4a01715"/>
      {/* Circuit lines */}
      <line x1="32" y1="22" x2="32" y2="42" stroke="#8b7335" strokeWidth="1.5" strokeDasharray="2 2"/>
      <line x1="22" y1="32" x2="42" y2="32" stroke="#8b7335" strokeWidth="1.5" strokeDasharray="2 2"/>
      {/* Nodes */}
      <circle cx="32" cy="32" r="3" fill="#d4a017"/>
      <circle cx="32" cy="22" r="1.5" fill="#8b7335"/>
      <circle cx="32" cy="42" r="1.5" fill="#8b7335"/>
      <circle cx="22" cy="32" r="1.5" fill="#8b7335"/>
      <circle cx="42" cy="32" r="1.5" fill="#8b7335"/>
      {/* Corner dots */}
      <circle cx="26" cy="26" r="1" fill="#d4a01780"/>
      <circle cx="38" cy="26" r="1" fill="#d4a01780"/>
      <circle cx="26" cy="38" r="1" fill="#d4a01780"/>
      <circle cx="38" cy="38" r="1" fill="#d4a01780"/>
    </svg>
  );
}

// Playbook Execution — gears with play button
export function IconPlaybookExec({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="exec-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Large gear */}
      <circle cx="26" cy="28" r="12" fill="none" stroke="url(#exec-grad)" strokeWidth="2"/>
      <circle cx="26" cy="28" r="7" fill="none" stroke="#8b7335" strokeWidth="1.5"/>
      {/* Gear teeth */}
      <line x1="37" y1="28" x2="40" y2="28" stroke="#d4a017" strokeWidth="2.5" strokeLinecap="round"/>
      <line x1="33.8" y1="20.2" x2="35.9" y2="18.1" stroke="#d4a017" strokeWidth="2.5" strokeLinecap="round"/>
      <line x1="26" y1="17" x2="26" y2="14" stroke="#d4a017" strokeWidth="2.5" strokeLinecap="round"/>
      <line x1="18.2" y1="20.2" x2="16.1" y2="18.1" stroke="#d4a017" strokeWidth="2.5" strokeLinecap="round"/>
      <line x1="15" y1="28" x2="12" y2="28" stroke="#d4a017" strokeWidth="2.5" strokeLinecap="round"/>
      <line x1="18.2" y1="35.8" x2="16.1" y2="37.9" stroke="#d4a017" strokeWidth="2.5" strokeLinecap="round"/>
      <line x1="26" y1="39" x2="26" y2="42" stroke="#d4a017" strokeWidth="2.5" strokeLinecap="round"/>
      <line x1="33.8" y1="35.8" x2="35.9" y2="37.9" stroke="#d4a017" strokeWidth="2.5" strokeLinecap="round"/>
      {/* Play triangle */}
      <polygon points="23,24 23,32 30,28" fill="#d4a017"/>
      {/* Small gear */}
      <circle cx="44" cy="40" r="7" fill="none" stroke="#8b7335" strokeWidth="1.5"/>
      <circle cx="44" cy="40" r="4" fill="none" stroke="#8b733580" strokeWidth="1"/>
      <line x1="50.5" y1="40" x2="53" y2="40" stroke="#8b7335" strokeWidth="2" strokeLinecap="round"/>
      <line x1="47.25" y1="34.4" x2="48.5" y2="33.2" stroke="#8b7335" strokeWidth="2" strokeLinecap="round"/>
      <line x1="40.75" y1="34.4" x2="39.5" y2="33.2" stroke="#8b7335" strokeWidth="2" strokeLinecap="round"/>
      <line x1="37.5" y1="40" x2="35" y2="40" stroke="#8b7335" strokeWidth="2" strokeLinecap="round"/>
      <line x1="40.75" y1="45.6" x2="39.5" y2="46.8" stroke="#8b7335" strokeWidth="2" strokeLinecap="round"/>
      <line x1="47.25" y1="45.6" x2="48.5" y2="46.8" stroke="#8b7335" strokeWidth="2" strokeLinecap="round"/>
      {/* Arrow connector */}
      <path d="M38 34L40 38" stroke="#d4a01780" strokeWidth="1" strokeDasharray="2 1"/>
      {/* Terminal/console */}
      <rect x="8" y="44" width="18" height="12" rx="1.5" fill="none" stroke="#8b7335" strokeWidth="1.2"/>
      <path d="M11 48l3 2.5-3 2.5" stroke="#d4a017" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="16" y1="53" x2="22" y2="53" stroke="#8b733580" strokeWidth="1"/>
    </svg>
  );
}

// Orchestration Hub — network/monitoring command center
export function IconOrchestration({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="orch-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Central hub */}
      <circle cx="32" cy="32" r="8" fill="#d4a01720" stroke="url(#orch-grad)" strokeWidth="2"/>
      <circle cx="32" cy="32" r="3" fill="#d4a017"/>
      {/* Satellite nodes */}
      {[
        { x: 14, y: 14 }, { x: 50, y: 14 },
        { x: 14, y: 50 }, { x: 50, y: 50 },
        { x: 32, y: 8 }, { x: 32, y: 56 },
      ].map((pos, i) => (
        <g key={i}>
          <line x1="32" y1="32" x2={pos.x} y2={pos.y} stroke="#8b733560" strokeWidth="1" strokeDasharray="3 2"/>
          <rect x={pos.x - 5} y={pos.y - 4} width="10" height="8" rx="1" fill="none" stroke="#8b7335" strokeWidth="1.2"/>
          <line x1={pos.x - 3} y1={pos.y} x2={pos.x + 3} y2={pos.y} stroke="#d4a01780" strokeWidth="0.8"/>
          <circle cx={pos.x} cy={pos.y - 2} r="0.8" fill="#d4a017"/>
        </g>
      ))}
      {/* Pulse rings */}
      <circle cx="32" cy="32" r="14" fill="none" stroke="#d4a01730" strokeWidth="0.8"/>
      <circle cx="32" cy="32" r="20" fill="none" stroke="#d4a01718" strokeWidth="0.5"/>
    </svg>
  );
}

// Convert / Arrow exchange — bidirectional conversion
export function IconConvert({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="conv-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Left document */}
      <rect x="6" y="14" width="20" height="28" rx="2" fill="none" stroke="#8b7335" strokeWidth="1.5"/>
      <line x1="10" y1="20" x2="22" y2="20" stroke="#8b733580" strokeWidth="1"/>
      <line x1="10" y1="24" x2="20" y2="24" stroke="#8b733580" strokeWidth="1"/>
      <line x1="10" y1="28" x2="22" y2="28" stroke="#8b733580" strokeWidth="1"/>
      <line x1="10" y1="32" x2="18" y2="32" stroke="#8b733580" strokeWidth="1"/>
      <text x="16" y="40" textAnchor="middle" fill="#d4a017" fontSize="6" fontFamily="monospace">JSON</text>
      {/* Right document */}
      <rect x="38" y="14" width="20" height="28" rx="2" fill="none" stroke="#d4a017" strokeWidth="1.5"/>
      <line x1="42" y1="20" x2="54" y2="20" stroke="#d4a01780" strokeWidth="1"/>
      <line x1="42" y1="24" x2="52" y2="24" stroke="#d4a01780" strokeWidth="1"/>
      <line x1="42" y1="28" x2="54" y2="28" stroke="#d4a01780" strokeWidth="1"/>
      <line x1="42" y1="32" x2="50" y2="32" stroke="#d4a01780" strokeWidth="1"/>
      <text x="48" y="40" textAnchor="middle" fill="#d4a017" fontSize="6" fontFamily="monospace">YAML</text>
      {/* Arrows */}
      <path d="M28 24h8" stroke="url(#conv-grad)" strokeWidth="2" markerEnd="url(#arr)"/>
      <path d="M36 32h-8" stroke="url(#conv-grad)" strokeWidth="2" markerEnd="url(#arr)"/>
      <defs>
        <marker id="arr" markerWidth="6" markerHeight="4" refX="5" refY="2" orient="auto">
          <polygon points="0,0 6,2 0,4" fill="#d4a017"/>
        </marker>
      </defs>
      {/* Bottom badge */}
      <rect x="20" y="48" width="24" height="10" rx="2" fill="#d4a01715" stroke="#8b7335" strokeWidth="1"/>
      <text x="32" y="55" textAnchor="middle" fill="#d4a017" fontSize="5.5" fontFamily="monospace">CACAO</text>
    </svg>
  );
}

// Database/Library — stacked playbooks
export function IconLibrary({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="lib-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Database cylinders stacked */}
      <ellipse cx="32" cy="16" rx="18" ry="6" fill="none" stroke="url(#lib-grad)" strokeWidth="1.5"/>
      <ellipse cx="32" cy="16" rx="18" ry="6" fill="#d4a01710"/>
      <line x1="14" y1="16" x2="14" y2="28" stroke="#8b7335" strokeWidth="1.5"/>
      <line x1="50" y1="16" x2="50" y2="28" stroke="#8b7335" strokeWidth="1.5"/>
      <ellipse cx="32" cy="28" rx="18" ry="6" fill="none" stroke="#8b7335" strokeWidth="1.2"/>
      <line x1="14" y1="28" x2="14" y2="40" stroke="#8b7335" strokeWidth="1.5"/>
      <line x1="50" y1="28" x2="50" y2="40" stroke="#8b7335" strokeWidth="1.5"/>
      <ellipse cx="32" cy="40" rx="18" ry="6" fill="none" stroke="#8b7335" strokeWidth="1.2"/>
      <line x1="14" y1="40" x2="14" y2="50" stroke="#8b7335" strokeWidth="1.5"/>
      <line x1="50" y1="40" x2="50" y2="50" stroke="#8b7335" strokeWidth="1.5"/>
      <ellipse cx="32" cy="50" rx="18" ry="6" fill="none" stroke="url(#lib-grad)" strokeWidth="1.5"/>
      {/* Data lines */}
      <line x1="22" y1="22" x2="42" y2="22" stroke="#d4a01740" strokeWidth="0.8"/>
      <line x1="24" y1="34" x2="40" y2="34" stroke="#d4a01740" strokeWidth="0.8"/>
      <line x1="22" y1="46" x2="42" y2="46" stroke="#d4a01740" strokeWidth="0.8"/>
      {/* Dot accents */}
      <circle cx="20" cy="22" r="1" fill="#d4a017"/>
      <circle cx="20" cy="34" r="1" fill="#d4a017"/>
      <circle cx="20" cy="46" r="1" fill="#d4a017"/>
    </svg>
  );
}

// Designer — flow/workflow nodes connected
export function IconDesigner({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="des-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Nodes */}
      <rect x="8" y="8" width="16" height="12" rx="2" fill="#d4a01715" stroke="url(#des-grad)" strokeWidth="1.5"/>
      <text x="16" y="16" textAnchor="middle" fill="#d4a017" fontSize="5" fontFamily="monospace">START</text>

      <rect x="38" y="8" width="18" height="12" rx="2" fill="none" stroke="#8b7335" strokeWidth="1.2"/>
      <line x1="42" y1="13" x2="52" y2="13" stroke="#8b733580" strokeWidth="0.8"/>
      <line x1="42" y1="16" x2="48" y2="16" stroke="#8b733580" strokeWidth="0.8"/>

      {/* Diamond (condition) */}
      <polygon points="32,28 42,36 32,44 22,36" fill="none" stroke="#d4a017" strokeWidth="1.5"/>
      <text x="32" y="38" textAnchor="middle" fill="#d4a01780" fontSize="4.5" fontFamily="monospace">IF</text>

      {/* Bottom nodes */}
      <rect x="6" y="50" width="16" height="10" rx="2" fill="none" stroke="#8b7335" strokeWidth="1.2"/>
      <circle cx="14" cy="55" r="2" fill="#d4a01740"/>

      <rect x="42" y="50" width="16" height="10" rx="2" fill="none" stroke="#8b7335" strokeWidth="1.2"/>
      <circle cx="50" cy="55" r="2" fill="#d4a01740"/>

      {/* Connections */}
      <path d="M24 14h14" stroke="#8b733580" strokeWidth="1"/>
      <path d="M16 20v8l16 8" stroke="#8b7335" strokeWidth="1" fill="none"/>
      <path d="M47 20v8l-5 8" stroke="#8b733560" strokeWidth="1" fill="none"/>
      <path d="M26 40l-12 10" stroke="#8b7335" strokeWidth="1"/>
      <path d="M38 40l12 10" stroke="#8b7335" strokeWidth="1"/>
      {/* Arrowheads */}
      <circle cx="14" cy="50" r="1.5" fill="#d4a017"/>
      <circle cx="50" cy="50" r="1.5" fill="#d4a017"/>
    </svg>
  );
}

// AI Bot — robot/brain with circuit
export function IconAI({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="ai-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Head */}
      <rect x="16" y="12" width="32" height="28" rx="4" fill="none" stroke="url(#ai-grad)" strokeWidth="2"/>
      <rect x="16" y="12" width="32" height="28" rx="4" fill="#d4a01710"/>
      {/* Eyes */}
      <circle cx="26" cy="26" r="4" fill="none" stroke="#d4a017" strokeWidth="1.5"/>
      <circle cx="26" cy="26" r="1.5" fill="#d4a017"/>
      <circle cx="38" cy="26" r="4" fill="none" stroke="#d4a017" strokeWidth="1.5"/>
      <circle cx="38" cy="26" r="1.5" fill="#d4a017"/>
      {/* Mouth / speaker grill */}
      <line x1="26" y1="34" x2="38" y2="34" stroke="#8b7335" strokeWidth="1"/>
      <line x1="27" y1="36" x2="37" y2="36" stroke="#8b733580" strokeWidth="0.8"/>
      {/* Antenna */}
      <line x1="32" y1="12" x2="32" y2="6" stroke="#8b7335" strokeWidth="1.5"/>
      <circle cx="32" cy="5" r="2" fill="#d4a017"/>
      {/* Signal waves */}
      <path d="M36 4c2-2 4-1 4 1" stroke="#d4a01780" strokeWidth="0.8" fill="none"/>
      <path d="M38 2c3-2 6-1 6 2" stroke="#d4a01750" strokeWidth="0.6" fill="none"/>
      {/* Body / base */}
      <rect x="20" y="42" width="24" height="8" rx="2" fill="none" stroke="#8b7335" strokeWidth="1.2"/>
      <line x1="28" y1="44" x2="28" y2="48" stroke="#8b733580" strokeWidth="0.8"/>
      <line x1="32" y1="44" x2="32" y2="48" stroke="#8b733580" strokeWidth="0.8"/>
      <line x1="36" y1="44" x2="36" y2="48" stroke="#8b733580" strokeWidth="0.8"/>
      {/* Arms / connectors */}
      <line x1="16" y1="24" x2="10" y2="24" stroke="#8b7335" strokeWidth="1.2"/>
      <circle cx="9" cy="24" r="2" fill="none" stroke="#8b7335" strokeWidth="1"/>
      <line x1="48" y1="24" x2="54" y2="24" stroke="#8b7335" strokeWidth="1.2"/>
      <circle cx="55" cy="24" r="2" fill="none" stroke="#8b7335" strokeWidth="1"/>
      {/* Circuit traces on forehead */}
      <path d="M22 18h4l2-2h8l2 2h4" stroke="#d4a01740" strokeWidth="0.7"/>
    </svg>
  );
}

// Server/Platform — rack with status LEDs
export function IconPlatform({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="plat-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Server rack */}
      <rect x="12" y="8" width="40" height="48" rx="3" fill="none" stroke="url(#plat-grad)" strokeWidth="2"/>
      {/* Server units */}
      {[14, 26, 38].map((y, i) => (
        <g key={i}>
          <rect x="16" y={y} width="32" height="10" rx="1.5" fill="#d4a01708" stroke="#8b7335" strokeWidth="1"/>
          <circle cx="21" cy={y + 5} r="1.5" fill={i === 0 ? "#22c55e" : i === 1 ? "#d4a017" : "#22c55e"}/>
          <line x1="26" y1={y + 3} x2="38" y2={y + 3} stroke="#8b733560" strokeWidth="0.8"/>
          <line x1="26" y1={y + 5} x2="34" y2={y + 5} stroke="#8b733540" strokeWidth="0.8"/>
          <line x1="26" y1={y + 7} x2="36" y2={y + 7} stroke="#8b733540" strokeWidth="0.8"/>
          <rect x="40" y={y + 2} width="5" height="6" rx="0.5" fill="none" stroke="#8b733580" strokeWidth="0.6"/>
        </g>
      ))}
      {/* Legs */}
      <line x1="18" y1="56" x2="18" y2="60" stroke="#8b7335" strokeWidth="2" strokeLinecap="round"/>
      <line x1="46" y1="56" x2="46" y2="60" stroke="#8b7335" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );
}

// Repos — interconnected nodes / community
export function IconRepos({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="repo-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Folder base */}
      <path d="M8 18h18l4-4h22a2 2 0 012 2v32a2 2 0 01-2 2H10a2 2 0 01-2-2V18z" fill="none" stroke="url(#repo-grad)" strokeWidth="1.5"/>
      <path d="M8 18h46v2H8z" fill="#d4a01720"/>
      {/* Git branch lines */}
      <circle cx="22" cy="30" r="2.5" fill="#d4a017"/>
      <circle cx="22" cy="42" r="2.5" fill="#8b7335"/>
      <line x1="22" y1="32.5" x2="22" y2="39.5" stroke="#8b7335" strokeWidth="1.5"/>
      {/* Branch */}
      <circle cx="36" cy="36" r="2.5" fill="#d4a017"/>
      <path d="M24 32c4 0 8 2 12 4" stroke="#8b7335" strokeWidth="1.2" fill="none"/>
      {/* Second branch */}
      <circle cx="42" cy="28" r="2" fill="#8b733580"/>
      <path d="M24 30c6-1 12-2 16-2" stroke="#8b733560" strokeWidth="1" fill="none"/>
      {/* Download arrow */}
      <path d="M46 38v6m-3-3l3 3 3-3" stroke="#d4a017" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

// Resources / Book with tactical markings
export function IconResources({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="res-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Book cover */}
      <path d="M12 8h36a2 2 0 012 2v40a2 2 0 01-2 2H16a4 4 0 01-4-4V8z" fill="none" stroke="url(#res-grad)" strokeWidth="1.5"/>
      {/* Spine */}
      <line x1="18" y1="8" x2="18" y2="52" stroke="#8b7335" strokeWidth="1.5"/>
      {/* Pages */}
      <line x1="24" y1="18" x2="44" y2="18" stroke="#8b733560" strokeWidth="0.8"/>
      <line x1="24" y1="22" x2="40" y2="22" stroke="#8b733560" strokeWidth="0.8"/>
      <line x1="24" y1="26" x2="42" y2="26" stroke="#8b733560" strokeWidth="0.8"/>
      <line x1="24" y1="30" x2="38" y2="30" stroke="#8b733560" strokeWidth="0.8"/>
      {/* Classification stamp */}
      <rect x="22" y="36" width="22" height="10" rx="1" fill="#d4a01715" stroke="#d4a017" strokeWidth="0.8"/>
      <text x="33" y="43" textAnchor="middle" fill="#d4a017" fontSize="5" fontFamily="monospace">CACAO</text>
      {/* Corner fold */}
      <path d="M42 8l8 8" stroke="#8b733540" strokeWidth="0.5"/>
    </svg>
  );
}

// Documents — file cabinet / folder stack
export function IconDocuments({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="doc-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Cabinet */}
      <rect x="10" y="8" width="44" height="48" rx="2" fill="none" stroke="url(#doc-grad)" strokeWidth="1.5"/>
      {/* Drawers */}
      <rect x="14" y="12" width="36" height="12" rx="1" fill="none" stroke="#8b7335" strokeWidth="1"/>
      <rect x="28" y="16" width="8" height="4" rx="0.5" fill="#d4a01730" stroke="#d4a017" strokeWidth="0.8"/>

      <rect x="14" y="28" width="36" height="12" rx="1" fill="none" stroke="#8b7335" strokeWidth="1"/>
      <rect x="28" y="32" width="8" height="4" rx="0.5" fill="#d4a01730" stroke="#d4a017" strokeWidth="0.8"/>

      <rect x="14" y="44" width="36" height="8" rx="1" fill="none" stroke="#8b7335" strokeWidth="1"/>
      <rect x="28" y="46" width="8" height="4" rx="0.5" fill="#d4a01730" stroke="#d4a017" strokeWidth="0.8"/>
      {/* Lock icon */}
      <circle cx="51" cy="8" r="4" fill="#0a0f0a" stroke="#8b7335" strokeWidth="1"/>
      <path d="M49 8v-1.5a2 2 0 014 0V8" stroke="#d4a017" strokeWidth="0.8" fill="none"/>
      <circle cx="51" cy="9" r="0.8" fill="#d4a017"/>
    </svg>
  );
}

// Stats counters icon
export function IconStats({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="stat-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Radar screen */}
      <circle cx="32" cy="32" r="22" fill="none" stroke="url(#stat-grad)" strokeWidth="2"/>
      <circle cx="32" cy="32" r="15" fill="none" stroke="#8b733540" strokeWidth="1"/>
      <circle cx="32" cy="32" r="8" fill="none" stroke="#8b733530" strokeWidth="1"/>
      {/* Crosshair */}
      <line x1="32" y1="10" x2="32" y2="54" stroke="#8b733530" strokeWidth="0.5"/>
      <line x1="10" y1="32" x2="54" y2="32" stroke="#8b733530" strokeWidth="0.5"/>
      {/* Sweep line */}
      <line x1="32" y1="32" x2="48" y2="18" stroke="#d4a017" strokeWidth="1.5" strokeLinecap="round"/>
      {/* Blips */}
      <circle cx="38" cy="22" r="2" fill="#d4a017" opacity="0.8"/>
      <circle cx="24" cy="28" r="1.5" fill="#d4a017" opacity="0.5"/>
      <circle cx="40" cy="38" r="1.5" fill="#d4a017" opacity="0.6"/>
      <circle cx="22" cy="40" r="1" fill="#8b7335" opacity="0.4"/>
      {/* Tick marks */}
      <line x1="52" y1="32" x2="54" y2="32" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
      <line x1="49.3" y1="22" x2="51.3" y2="21" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
      <line x1="42" y1="14.7" x2="43" y2="12.7" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
      <line x1="32" y1="12" x2="32" y2="10" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
      <line x1="22" y1="14.7" x2="21" y2="12.7" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
      <line x1="14.7" y1="22" x2="12.7" y2="21" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
      <line x1="12" y1="32" x2="10" y2="32" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
      <line x1="14.7" y1="42" x2="12.7" y2="43" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
      <line x1="22" y1="49.3" x2="21" y2="51.3" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
      <line x1="32" y1="52" x2="32" y2="54" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
      <line x1="42" y1="49.3" x2="43" y2="51.3" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
      <line x1="49.3" y1="42" x2="51.3" y2="43" stroke="#8b7335" strokeWidth="1" strokeLinecap="round"/>
    </svg>
  );
}

// Integration/Plug — connector with signal
export function IconIntegration({ className = "", size = 40 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" className={className}>
      <defs>
        <linearGradient id="int-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#d4a017" />
          <stop offset="100%" stopColor="#8b7335" />
        </linearGradient>
      </defs>
      {/* Left plug */}
      <rect x="8" y="22" width="20" height="20" rx="3" fill="none" stroke="url(#int-grad)" strokeWidth="1.5"/>
      <line x1="14" y1="28" x2="14" y2="36" stroke="#d4a017" strokeWidth="2" strokeLinecap="round"/>
      <line x1="22" y1="28" x2="22" y2="36" stroke="#d4a017" strokeWidth="2" strokeLinecap="round"/>
      {/* Right plug */}
      <rect x="36" y="22" width="20" height="20" rx="3" fill="none" stroke="#8b7335" strokeWidth="1.5"/>
      <line x1="42" y1="28" x2="42" y2="36" stroke="#8b7335" strokeWidth="2" strokeLinecap="round"/>
      <line x1="50" y1="28" x2="50" y2="36" stroke="#8b7335" strokeWidth="2" strokeLinecap="round"/>
      {/* Connection spark */}
      <path d="M28 30l4-2 4 4-4 2z" fill="#d4a017" opacity="0.6"/>
      <path d="M30 32h4" stroke="#d4a017" strokeWidth="1.5"/>
      {/* Signal waves top */}
      <path d="M26 16c4-6 12-6 16 0" stroke="#d4a01760" strokeWidth="1" fill="none"/>
      <path d="M24 12c6-8 16-8 22 0" stroke="#d4a01740" strokeWidth="0.8" fill="none"/>
      {/* Cable lines bottom */}
      <line x1="18" y1="42" x2="18" y2="52" stroke="#8b7335" strokeWidth="1.5"/>
      <line x1="46" y1="42" x2="46" y2="52" stroke="#8b7335" strokeWidth="1.5"/>
      <path d="M18 52c0 4 28 4 28 0" stroke="#8b733580" strokeWidth="1" fill="none"/>
    </svg>
  );
}
