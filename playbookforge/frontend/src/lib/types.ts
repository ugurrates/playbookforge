export interface CacaoPlaybook {
  type: string;
  spec_version: string;
  id: string;
  name: string;
  description?: string;
  playbook_types?: string[];
  workflow_start: string;
  workflow: Record<string, WorkflowStep>;
  playbook_variables?: Record<string, Variable>;
  labels?: string[];
  external_references?: ExternalReference[];
  created?: string;
  modified?: string;
  priority?: number;
  severity?: number;
  impact?: number;
}

export interface WorkflowStep {
  type: string;
  name?: string;
  description?: string;
  commands?: Command[];
  on_completion?: string;
  on_success?: string;
  on_failure?: string;
  on_true?: string;
  on_false?: string;
  condition?: string;
  next_steps?: string[];
  playbook_id?: string;
}

export interface Command {
  type: string;
  command?: string;
  description?: string;
  content?: string;
}

export interface Variable {
  type: string;
  value?: string;
  description?: string;
  constant?: boolean;
  external?: boolean;
}

export interface ExternalReference {
  name: string;
  url?: string;
  description?: string;
  source?: string;
}

export const STEP_TYPE_COLORS: Record<string, string> = {
  start: "bg-gray-600",
  end: "bg-gray-600",
  action: "bg-blue-600",
  "playbook-action": "bg-amber-600",
  "if-condition": "bg-yellow-600",
  "while-condition": "bg-yellow-700",
  "switch-condition": "bg-yellow-700",
  parallel: "bg-green-600",
};

export const PLATFORM_LOGOS: Record<string, { color: string; abbr: string }> = {
  xsoar: { color: "bg-blue-600", abbr: "XS" },
  shuffle: { color: "bg-orange-500", abbr: "SH" },
  sentinel: { color: "bg-cyan-600", abbr: "SE" },
  fortisoar: { color: "bg-red-600", abbr: "FS" },
  splunk_soar: { color: "bg-green-600", abbr: "SP" },
  google_secops: { color: "bg-yellow-500", abbr: "GS" },
};

// ============================================================================
// Product Catalog Types
// ============================================================================

export interface ActionParameter {
  name: string;
  type: string;
  required: boolean;
  description: string;
  example?: string;
}

export interface ProductAction {
  id: string;
  name: string;
  description: string;
  http_method: string;
  endpoint_pattern: string;
  parameters: ActionParameter[];
  cacao_activity?: string;
}

export interface Product {
  id: string;
  name: string;
  vendor: string;
  category: string;
  description: string;
  auth_types: string[];
  base_url_pattern: string;
  actions: ProductAction[];
  logo_abbr: string;
  logo_color: string;
}

export interface ProductSummary {
  id: string;
  name: string;
  vendor: string;
  category: string;
  description: string;
  action_count: number;
  logo_abbr: string;
  logo_color: string;
}

export interface ProductListResponse {
  total: number;
  products: ProductSummary[];
}

export const PRODUCT_CATEGORY_LABELS: Record<string, string> = {
  "firewall": "Firewall / NGFW",
  "edr-xdr": "EDR / XDR",
  "siem": "SIEM",
  "email-security": "Email Security",
  "waf": "WAF",
  "identity-iam": "Identity / IAM",
  "threat-intel": "Threat Intelligence",
  "vulnerability-management": "Vulnerability Management",
  "cloud-security": "Cloud Security",
  "endpoint-management": "Endpoint Management",
  "ticketing": "Ticketing / ITSM",
};

// ============================================================================
// Resource Types & Constants
// ============================================================================

export const RESOURCE_CATEGORY_LABELS: Record<string, string> = {
  "edr": "EDR / XDR",
  "siem": "SIEM",
  "email": "Email Security",
  "identity": "Identity / IAM",
  "firewall": "Firewall",
  "threat-intel": "Threat Intelligence",
  "cloud": "Cloud Security",
  "incident-response": "Incident Response",
  "general": "General",
};

export const RESOURCE_CATEGORY_COLORS: Record<string, string> = {
  "edr": "bg-red-600",
  "siem": "bg-blue-600",
  "email": "bg-yellow-600",
  "identity": "bg-amber-700",
  "firewall": "bg-orange-600",
  "threat-intel": "bg-cyan-600",
  "cloud": "bg-teal-600",
  "incident-response": "bg-pink-600",
  "general": "bg-[#1a2e1a]",
};

export const DIFFICULTY_COLORS: Record<string, string> = {
  "beginner": "bg-green-600",
  "intermediate": "bg-yellow-600",
  "advanced": "bg-red-600",
};
