const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Platform {
  platform_name: string;
  platform_id: string;
  file_extension: string;
}

export interface ValidationIssue {
  severity: string;
  code: string;
  message: string;
  path: string;
}

export interface ValidateResponse {
  valid: boolean;
  error_count: number;
  warning_count: number;
  issues: ValidationIssue[];
  playbook_summary: Record<string, unknown>;
}

export interface ConvertResponse {
  success: boolean;
  platform: string;
  filename: string;
  content: string;
  content_type: string;
}

export interface ImportResponse {
  success: boolean;
  detected_platform: string;
  playbook: Record<string, unknown>;
}

export interface DetectResponse {
  detected: boolean;
  platform_id?: string;
  platform_name?: string;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function listPlatforms() {
  return apiFetch<{ platforms: Platform[]; importers: Platform[]; total: number }>("/platforms");
}

export async function validatePlaybook(playbook: Record<string, unknown>) {
  return apiFetch<ValidateResponse>("/validate", {
    method: "POST",
    body: JSON.stringify({ playbook }),
  });
}

export async function convertPlaybook(playbook: Record<string, unknown>, targetPlatform: string) {
  return apiFetch<ConvertResponse>("/convert", {
    method: "POST",
    body: JSON.stringify({ playbook, target_platform: targetPlatform }),
  });
}

export async function convertAll(playbook: Record<string, unknown>) {
  return apiFetch<{ success: boolean; results: Record<string, ConvertResponse & { error?: string }> }>(
    "/convert/all",
    { method: "POST", body: JSON.stringify({ playbook }) }
  );
}

export async function importPlaybook(content: string, sourcePlatform?: string) {
  return apiFetch<ImportResponse>("/import", {
    method: "POST",
    body: JSON.stringify({ content, source_platform: sourcePlatform }),
  });
}

export async function detectFormat(content: string) {
  return apiFetch<DetectResponse>("/import/detect", {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function importAndConvert(content: string, targetPlatform: string, sourcePlatform?: string) {
  return apiFetch<ConvertResponse>("/import/convert", {
    method: "POST",
    body: JSON.stringify({ content, target_platform: targetPlatform, source_platform: sourcePlatform }),
  });
}

export async function healthCheck() {
  return apiFetch<{ status: string }>("/health");
}

// Library API

export interface LibraryEntry {
  id: string;
  name: string;
  description: string;
  source_platform: string;
  source_repo: string;
  playbook_types: string[];
  step_count: number;
  action_count: number;
  tags: string[];
  mitre_techniques: string[];
  created_at: string;
}

export interface LibraryListResponse {
  total: number;
  offset: number;
  limit: number;
  playbooks: LibraryEntry[];
}

export interface LibraryStatsResponse {
  total: number;
  by_platform: Record<string, number>;
  top_tags: Record<string, number>;
}

export async function libraryList(params?: {
  platform?: string;
  search?: string;
  tag?: string;
  limit?: number;
  offset?: number;
}) {
  const qs = new URLSearchParams();
  if (params?.platform) qs.set("platform", params.platform);
  if (params?.search) qs.set("search", params.search);
  if (params?.tag) qs.set("tag", params.tag);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const query = qs.toString() ? `?${qs}` : "";
  return apiFetch<LibraryListResponse>(`/library${query}`);
}

export async function libraryStats() {
  return apiFetch<LibraryStatsResponse>("/library/stats");
}

export async function libraryGet(id: string) {
  return apiFetch<LibraryEntry & { cacao_playbook: Record<string, unknown>; source_file: string }>(`/library/${id}`);
}

export async function librarySave(playbook: Record<string, unknown>, source_platform: string = "designer", tags: string[] = []) {
  return apiFetch<{ id: string; success: boolean }>("/library", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ playbook, source_platform, tags }),
  });
}

// ============================================================================
// Product Catalog API
// ============================================================================

import type { Product, ProductSummary, ProductAction } from "./types";

export interface ProductListResponse {
  total: number;
  products: ProductSummary[];
}

export async function listProducts(category?: string) {
  const qs = category ? `?category=${encodeURIComponent(category)}` : "";
  return apiFetch<ProductListResponse>(`/products${qs}`);
}

export async function getProduct(id: string) {
  return apiFetch<Product>(`/products/${id}`);
}

export async function searchProducts(q: string) {
  return apiFetch<ProductListResponse>(`/products/search?q=${encodeURIComponent(q)}`);
}

export async function getProductActions(productIds: string[]) {
  return apiFetch<Record<string, ProductAction[]>>("/products/actions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_ids: productIds }),
  });
}

export async function getProductCategories() {
  return apiFetch<Record<string, number>>("/products/categories");
}

// ============================================================================
// AI / LLM API
// ============================================================================

export interface AIGenerateResponse {
  success: boolean;
  playbook: Record<string, unknown>;
  model_used: string;
}

export interface AIAnalyzeResponse {
  success: boolean;
  analysis: Record<string, unknown>;
  model_used: string;
}

export async function aiGenerate(prompt: string, productIds?: string[], model: string = "auto") {
  return apiFetch<AIGenerateResponse>("/ai/generate", {
    method: "POST",
    body: JSON.stringify({ prompt, model, product_ids: productIds || null }),
  });
}

export async function aiEnrich(playbook: Record<string, unknown>, model: string = "auto") {
  return apiFetch<AIGenerateResponse>("/ai/enrich", {
    method: "POST",
    body: JSON.stringify({ playbook, model }),
  });
}

export async function aiAnalyze(playbook: Record<string, unknown>, model: string = "auto") {
  return apiFetch<AIAnalyzeResponse>("/ai/analyze", {
    method: "POST",
    body: JSON.stringify({ playbook, model }),
  });
}

// ============================================================================
// Blue Team Integration API
// ============================================================================

export interface IntegrationInfo {
  name: string;
  description: string;
  url: string;
  connected: boolean;
  version: string | null;
  error: string | null;
}

export interface IntegrationsStatusResponse {
  integrations: IntegrationInfo[];
  connected_count: number;
  total_count: number;
}

export interface ThreatItem {
  id: string;
  title: string;
  source: string;
  severity: string;
  description: string;
  url: string;
  published: string;
  tags: string[];
  cve_ids: string[];
}

export interface ThreatsResponse {
  threats: ThreatItem[];
  count: number;
  source: string;
}

export async function getIntegrationsStatus() {
  return apiFetch<IntegrationsStatusResponse>("/integrations/status");
}

export async function getRecentThreats(limit: number = 10) {
  return apiFetch<ThreatsResponse>(`/integrations/threats?limit=${limit}`);
}

export async function getThreatContext(indicator: string) {
  return apiFetch<{ indicator: string; context: Record<string, unknown>; source: string }>(
    "/integrations/context",
    {
      method: "POST",
      body: JSON.stringify({ indicator }),
    }
  );
}

export async function getPlaybookSuggestions(cve: string) {
  return apiFetch<{ cve: string; suggestions: Array<Record<string, unknown>>; source: string }>(
    `/integrations/playbook-suggestions?cve=${encodeURIComponent(cve)}`
  );
}

// ============================================================================
// PDF API
// ============================================================================

export async function generatePdf(playbook: Record<string, unknown>, includeValidation: boolean = true): Promise<Blob> {
  const res = await fetch(`${API_BASE}/playbook/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ playbook, include_validation: includeValidation }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.blob();
}

export async function generateLibraryPdf(playbookId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/library/${playbookId}/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.blob();
}

// ============================================================================
// File Upload API
// ============================================================================

export interface UploadedFileInfo {
  id: string;
  filename: string;
  original_filename: string;
  description: string;
  playbook_id: string | null;
  file_size: number;
  content_type: string;
  uploaded_at: string;
  tags: string[];
}

export async function uploadFile(
  file: File,
  description: string = "",
  playbookId: string = "",
  tags: string = "",
): Promise<{ success: boolean; file: UploadedFileInfo }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("description", description);
  formData.append("playbook_id", playbookId);
  formData.append("tags", tags);

  const res = await fetch(`${API_BASE}/files/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function listUploadedFiles(playbookId?: string) {
  const qs = playbookId ? `?playbook_id=${encodeURIComponent(playbookId)}` : "";
  return apiFetch<{ total: number; files: UploadedFileInfo[] }>(`/files${qs}`);
}

export async function downloadFile(fileId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/files/${fileId}/download`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.blob();
}

export async function deleteFile(fileId: string) {
  return apiFetch<{ success: boolean; deleted: string }>(`/files/${fileId}`, {
    method: "DELETE",
  });
}

// ============================================================================
// Resources / Best Practices API
// ============================================================================

export interface IntegrationStepInfo {
  order: number;
  title: string;
  description: string;
  code_example: string;
}

export interface BestPracticeSummary {
  id: string;
  title: string;
  description: string;
  category: string;
  difficulty: string;
  step_count: number;
  tags: string[];
  type: "best-practice";
}

export interface BestPracticeDetail extends BestPracticeSummary {
  steps: IntegrationStepInfo[];
  related_product_ids: string[];
  mitre_techniques: string[];
}

export interface IntegrationGuideSummary {
  id: string;
  title: string;
  description: string;
  category: string;
  product_id: string;
  difficulty: string;
  step_count: number;
  tags: string[];
  type: "integration-guide";
}

export interface IntegrationGuideDetail extends IntegrationGuideSummary {
  prerequisites: string[];
  steps: IntegrationStepInfo[];
}

export async function listBestPractices(category?: string, difficulty?: string) {
  const qs = new URLSearchParams();
  if (category) qs.set("category", category);
  if (difficulty) qs.set("difficulty", difficulty);
  const query = qs.toString() ? `?${qs}` : "";
  return apiFetch<{ total: number; best_practices: BestPracticeSummary[] }>(`/resources/best-practices${query}`);
}

export async function getBestPractice(id: string) {
  return apiFetch<BestPracticeDetail>(`/resources/best-practices/${id}`);
}

export async function listIntegrationGuides(category?: string, productId?: string) {
  const qs = new URLSearchParams();
  if (category) qs.set("category", category);
  if (productId) qs.set("product_id", productId);
  const query = qs.toString() ? `?${qs}` : "";
  return apiFetch<{ total: number; integration_guides: IntegrationGuideSummary[] }>(`/resources/integration-guides${query}`);
}

export async function getIntegrationGuide(id: string) {
  return apiFetch<IntegrationGuideDetail>(`/resources/integration-guides/${id}`);
}

export async function searchResources(q: string) {
  return apiFetch<{ total: number; results: (BestPracticeSummary | IntegrationGuideSummary)[] }>(
    `/resources/search?q=${encodeURIComponent(q)}`
  );
}

export async function getEdrResources() {
  return apiFetch<{
    best_practices: BestPracticeSummary[];
    integration_guides: IntegrationGuideSummary[];
    total: number;
  }>("/resources/edr");
}

// ============================================================================
// Community Repos API
// ============================================================================

export interface RepoInfo {
  id: string;
  name: string;
  url: string;
  platform: string;
  description: string;
  branch: string;
  playbook_paths: string[];
  file_patterns: string[];
  enabled: boolean;
  status: string;
  last_sync: string | null;
  playbooks_imported: number;
  playbooks_failed: number;
  error_message: string;
}

export interface RepoSyncStatus {
  total_repos: number;
  synced: number;
  syncing: number;
  errors: number;
  pending: number;
  total_playbooks_imported: number;
  is_syncing: boolean;
}

export async function listRepos() {
  return apiFetch<{ total: number; repos: RepoInfo[] }>("/repos");
}

export async function getRepoSyncStatus() {
  return apiFetch<RepoSyncStatus>("/repos/status");
}

export async function syncAllRepos() {
  return apiFetch<{ status: string; repos?: number; message?: string }>("/repos/sync", {
    method: "POST",
  });
}

export async function syncRepo(repoId: string) {
  return apiFetch<{ status: string; repo_id?: string; message?: string }>(
    `/repos/${repoId}/sync`,
    { method: "POST" }
  );
}

export async function toggleRepo(repoId: string, enabled: boolean) {
  return apiFetch<{ status: string; repo_id: string; enabled: boolean }>(
    `/repos/${repoId}`,
    { method: "PATCH", body: JSON.stringify({ enabled }) }
  );
}
