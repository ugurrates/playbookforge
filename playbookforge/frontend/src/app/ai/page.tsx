"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Bot,
  Send,
  Loader2,
  ChevronRight,
  ChevronLeft,
  Package,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Download,
  Workflow,
  Save,
  ArrowLeftRight,
  Sparkles,
  BarChart3,
} from "lucide-react";
import ProductPicker from "@/components/ProductPicker";
import { PlaybookViewer } from "@/components/PlaybookViewer";
import { ExportModal } from "@/components/ExportModal";
import { StepList } from "@/components/StepList";
import { ValidationReport } from "@/components/ValidationReport";
import {
  aiGenerate,
  aiEnrich,
  aiAnalyze,
  validatePlaybook,
  librarySave,
  type ValidateResponse,
  type AIAnalyzeResponse,
} from "@/lib/api";
import type { CacaoPlaybook } from "@/lib/types";

// Dynamic example prompts based on selected products
function getExamplePrompts(selectedProducts: string[]): string[] {
  const hasEdr = selectedProducts.some((p) =>
    ["crowdstrike_falcon", "sentinelone", "ms_defender_endpoint", "vmware_carbon_black", "cortex_xdr"].includes(p)
  );
  const hasFirewall = selectedProducts.some((p) =>
    ["paloalto_ngfw", "fortinet_fortigate", "checkpoint_firewall", "cisco_asa"].includes(p)
  );
  const hasIdentity = selectedProducts.some((p) =>
    ["entra_id", "active_directory", "okta", "cyberark"].includes(p)
  );
  const hasThreatIntel = selectedProducts.some((p) =>
    ["virustotal", "abuseipdb", "alienvault_otx"].includes(p)
  );
  const hasEmail = selectedProducts.some((p) =>
    ["proofpoint_tap", "mimecast", "ms_defender_office365"].includes(p)
  );
  const hasSiem = selectedProducts.some((p) =>
    ["splunk_enterprise", "ibm_qradar", "elastic_siem"].includes(p)
  );

  const prompts: string[] = [];

  if (hasEdr && hasThreatIntel) {
    prompts.push(
      "Create a malware incident response playbook: detect malicious file hash, look up reputation, isolate the endpoint, collect forensic data, and create an incident ticket"
    );
  }
  if (hasFirewall && hasSiem) {
    prompts.push(
      "Build a suspicious IP blocking playbook: query SIEM for alerts, validate the threat, block IP on the firewall, and log the action"
    );
  }
  if (hasIdentity && hasEmail) {
    prompts.push(
      "Design a compromised account response playbook: detect phishing email, disable user account, revoke active sessions, quarantine the message, and reset credentials"
    );
  }
  if (hasEdr && hasIdentity) {
    prompts.push(
      "Create a lateral movement detection playbook: isolate compromised endpoint, disable the user account, search for related IOCs across the environment"
    );
  }
  if (hasThreatIntel) {
    prompts.push(
      "Build a threat intelligence enrichment workflow: receive an IOC, check reputation on multiple TI platforms, create a ticket with findings"
    );
  }

  // Generic fallbacks
  if (prompts.length === 0) {
    prompts.push(
      "Create a phishing email investigation playbook that extracts IOCs, checks reputation, and blocks malicious senders",
      "Build a malware containment playbook that isolates infected hosts and collects forensic data",
      "Design a brute-force detection playbook that checks failed logins and blocks suspicious IPs"
    );
  }

  return prompts.slice(0, 3);
}

type WizardStep = 1 | 2 | 3;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function AnalysisDisplay({ analysis }: { analysis: Record<string, any> }) {
  const scores = analysis.scores as Record<string, { score?: number }> | undefined;
  const strengths = analysis.strengths as string[] | undefined;
  const weaknesses = analysis.weaknesses as string[] | undefined;
  const recommendations = analysis.recommendations as Array<string | { description?: string }> | undefined;

  return (
    <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-4 space-y-3">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <BarChart3 className="w-4 h-4 text-cyan-400" /> Quality Analysis
      </h3>
      {analysis.overall_score !== undefined && (
        <div className="flex items-center gap-3">
          <span className="text-3xl font-bold text-cyan-400">
            {String(analysis.overall_score)}
          </span>
          <span className="text-sm text-[#7a7a6a]">/ 100</span>
        </div>
      )}
      {scores && typeof scores === "object" && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {Object.entries(scores).map(([key, val]) => (
            <div key={key} className="bg-[#111a11] rounded p-2">
              <div className="text-[10px] text-[#7a7a6a] uppercase">{key.replace(/_/g, " ")}</div>
              <div className="text-sm font-semibold text-[#d4d4c8]">
                {val && typeof val === "object" && val.score !== undefined ? String(val.score) : String(val)}
              </div>
            </div>
          ))}
        </div>
      )}
      {strengths && Array.isArray(strengths) && strengths.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-green-400 mb-1">Strengths</h4>
          <ul className="text-xs text-[#7a7a6a] space-y-0.5">
            {strengths.map((s, i) => (
              <li key={i}>+ {s}</li>
            ))}
          </ul>
        </div>
      )}
      {weaknesses && Array.isArray(weaknesses) && weaknesses.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-red-400 mb-1">Weaknesses</h4>
          <ul className="text-xs text-[#7a7a6a] space-y-0.5">
            {weaknesses.map((s, i) => (
              <li key={i}>- {s}</li>
            ))}
          </ul>
        </div>
      )}
      {recommendations && Array.isArray(recommendations) && recommendations.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-yellow-400 mb-1">Recommendations</h4>
          <ul className="text-xs text-[#7a7a6a] space-y-0.5">
            {recommendations.map((r, i) => (
              <li key={i}>
                {typeof r === "string" ? r : r.description || JSON.stringify(r)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function AIPage() {
  const router = useRouter();

  // Wizard state
  const [step, setStep] = useState<WizardStep>(1);
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [prompt, setPrompt] = useState("");

  // Generation state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [modelUsed, setModelUsed] = useState<string>("");

  // Result actions state
  const [view, setView] = useState<"steps" | "json">("steps");
  const [showExport, setShowExport] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidateResponse | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AIAnalyzeResponse | null>(null);
  const [enriching, setEnriching] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [validating, setValidating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setValidationResult(null);
    setAnalysisResult(null);
    setStatusMsg(null);

    try {
      const res = await aiGenerate(
        prompt,
        selectedProducts.length > 0 ? selectedProducts : undefined
      );
      setResult(res.playbook);
      setModelUsed(res.model_used);
      setStep(3);
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : "AI generation failed";
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = async () => {
    if (!result) return;
    setValidating(true);
    try {
      const vr = await validatePlaybook(result);
      setValidationResult(vr);
      setStatusMsg({
        type: vr.valid ? "success" : "error",
        text: vr.valid
          ? "Playbook is valid!"
          : `${vr.error_count} errors, ${vr.warning_count} warnings`,
      });
    } catch {
      setStatusMsg({ type: "error", text: "Validation request failed" });
    } finally {
      setValidating(false);
    }
  };

  const handleEnrich = async () => {
    if (!result) return;
    setEnriching(true);
    setStatusMsg(null);
    try {
      const res = await aiEnrich(result);
      setResult(res.playbook);
      setStatusMsg({ type: "success", text: "Playbook enriched with AI improvements!" });
      setValidationResult(null);
      setAnalysisResult(null);
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : "Enrichment failed";
      setStatusMsg({ type: "error", text: errMsg });
    } finally {
      setEnriching(false);
    }
  };

  const handleAnalyze = async () => {
    if (!result) return;
    setAnalyzing(true);
    setStatusMsg(null);
    try {
      const res = await aiAnalyze(result);
      setAnalysisResult(res);
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : "Analysis failed";
      setStatusMsg({ type: "error", text: errMsg });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSave = async () => {
    if (!result) return;
    setSaving(true);
    try {
      await librarySave(result, "ai-generated", ["ai-generated"]);
      setStatusMsg({ type: "success", text: "Saved to library!" });
    } catch (e: unknown) {
      const errMsg = e instanceof Error ? e.message : "Save failed";
      setStatusMsg({ type: "error", text: errMsg });
    } finally {
      setSaving(false);
    }
  };

  const handleOpenDesigner = () => {
    if (result) {
      sessionStorage.setItem("playbookforge_designer_input", JSON.stringify(result));
      router.push("/designer");
    }
  };

  const handleOpenConvert = () => {
    if (result) {
      sessionStorage.setItem("playbookforge_convert_input", JSON.stringify(result, null, 2));
      router.push("/convert");
    }
  };

  const examplePrompts = getExamplePrompts(selectedProducts);
  const resultPlaybook = result as unknown as CacaoPlaybook | null;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Bot className="w-6 h-6 text-amber-400" />
          AI Playbook Generator
        </h1>
        <span className="text-xs text-[#7a7a6a]">
          Powered by Ollama / OpenAI / Claude
        </span>
      </div>

      {/* Wizard progress */}
      <div className="flex items-center gap-2">
        {[
          { n: 1, label: "Select Products", icon: Package },
          { n: 2, label: "Describe Playbook", icon: FileText },
          { n: 3, label: "Result", icon: CheckCircle2 },
        ].map(({ n, label, icon: Icon }, i) => (
          <div key={n} className="flex items-center gap-2 flex-1">
            <button
              onClick={() => {
                if (n === 3 && !result) return;
                setStep(n as WizardStep);
              }}
              disabled={n === 3 && !result}
              className={`flex items-center gap-2 px-3 py-2 rounded text-sm font-medium transition w-full ${
                step === n
                  ? "bg-amber-600/20 text-amber-300 border border-amber-500/50"
                  : step > n
                    ? "bg-[#111a11] text-[#d4d4c8] border border-[#2a3e2a] hover:border-[#2a3e2a]"
                    : "bg-[#0f1a0f] text-[#7a7a6a] border border-[#1a2e1a]"
              }`}
            >
              <span
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                  step > n
                    ? "bg-green-600 text-white"
                    : step === n
                      ? "bg-amber-600 text-white"
                      : "bg-[#1a2e1a] text-[#7a7a6a]"
                }`}
              >
                {step > n ? <CheckCircle2 className="w-3.5 h-3.5" /> : n}
              </span>
              <span className="hidden sm:inline">{label}</span>
              <Icon className="w-4 h-4 sm:hidden" />
            </button>
            {i < 2 && <ChevronRight className="w-4 h-4 text-[#2a3e2a] shrink-0" />}
          </div>
        ))}
      </div>

      {/* ======== STEP 1: Product Selection ======== */}
      {step === 1 && (
        <div className="space-y-4">
          <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5">
            <h2 className="text-lg font-semibold mb-1">
              Select Security Products
            </h2>
            <p className="text-sm text-[#7a7a6a] mb-4">
              Choose the products/tools that should be used in the generated playbook.
              The AI will use their real API actions to create executable workflow steps.
              <span className="text-[#7a7a6a] ml-1">(Optional — skip to generate a generic playbook)</span>
            </p>
            <ProductPicker
              selected={selectedProducts}
              onChange={setSelectedProducts}
            />
          </div>

          <div className="flex justify-end">
            <button
              onClick={() => setStep(2)}
              className="px-5 py-2.5 bg-amber-600 hover:bg-amber-500 rounded text-sm font-medium flex items-center gap-2 transition"
            >
              {selectedProducts.length > 0
                ? `Continue with ${selectedProducts.length} product${selectedProducts.length > 1 ? "s" : ""}`
                : "Skip — Generic Playbook"}
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ======== STEP 2: Describe Playbook ======== */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5 space-y-4">
            <h2 className="text-lg font-semibold mb-1">
              Describe Your Playbook
            </h2>
            <p className="text-sm text-[#7a7a6a]">
              Describe the security automation workflow you want to create in plain English.
              {selectedProducts.length > 0 && (
                <span className="text-amber-400 ml-1">
                  AI will use the {selectedProducts.length} selected product{selectedProducts.length > 1 ? "s" : ""} and their API actions.
                </span>
              )}
            </p>

            {/* Example prompts */}
            <div className="space-y-1.5">
              <p className="text-xs text-[#7a7a6a] uppercase tracking-wider">Examples</p>
              {examplePrompts.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setPrompt(ex)}
                  className="block w-full text-left text-sm text-[#7a7a6a] hover:text-[#d4d4c8] bg-[#111a11] hover:bg-[#1a2e1a] border border-[#2a3e2a] rounded p-2.5 transition"
                >
                  {ex}
                </button>
              ))}
            </div>

            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the security playbook you want to create..."
              className="w-full h-36 bg-[#0a0f0a] border border-[#2a3e2a] rounded p-3 text-sm text-[#d4d4c8] resize-none focus:outline-none focus:border-amber-500"
            />

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded p-3 text-sm text-red-300 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                {error}
              </div>
            )}
          </div>

          <div className="flex items-center justify-between">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 bg-[#111a11] hover:bg-[#1a2e1a] rounded text-sm flex items-center gap-2 text-[#7a7a6a] transition"
            >
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
            <button
              onClick={handleGenerate}
              disabled={loading || !prompt.trim()}
              className="px-6 py-2.5 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 rounded text-sm font-medium flex items-center gap-2 transition"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Generating...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" /> Generate Playbook
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* ======== STEP 3: Result ======== */}
      {step === 3 && result && (
        <div className="space-y-4">
          {/* Status */}
          {statusMsg && (
            <div
              className={`flex items-center gap-2 px-4 py-2 rounded text-sm ${
                statusMsg.type === "success"
                  ? "bg-green-500/10 border border-green-500/30 text-green-300"
                  : "bg-red-500/10 border border-red-500/30 text-red-300"
              }`}
            >
              {statusMsg.type === "success" ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                <AlertTriangle className="w-4 h-4" />
              )}
              {statusMsg.text}
            </div>
          )}

          {/* Info bar */}
          <div className="flex items-center justify-between bg-[#0f1a0f] border border-[#1a2e1a] rounded px-4 py-2">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-[#d4d4c8]">
                {(result as Record<string, unknown>).name as string || "Generated Playbook"}
              </span>
              <span className="text-xs text-[#7a7a6a]">
                Model: {modelUsed}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setView("steps")}
                className={`px-2.5 py-1 rounded text-xs transition ${
                  view === "steps"
                    ? "bg-amber-600 text-white"
                    : "bg-[#111a11] text-[#7a7a6a] hover:text-[#d4d4c8]"
                }`}
              >
                Steps
              </button>
              <button
                onClick={() => setView("json")}
                className={`px-2.5 py-1 rounded text-xs transition ${
                  view === "json"
                    ? "bg-amber-600 text-white"
                    : "bg-[#111a11] text-[#7a7a6a] hover:text-[#d4d4c8]"
                }`}
              >
                JSON
              </button>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleValidate}
              disabled={validating}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded text-xs font-medium flex items-center gap-1.5 transition"
            >
              {validating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
              Validate
            </button>
            <button
              onClick={handleEnrich}
              disabled={enriching}
              className="px-3 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 rounded text-xs font-medium flex items-center gap-1.5 transition"
            >
              {enriching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Enrich with AI
            </button>
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="px-3 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 rounded text-xs font-medium flex items-center gap-1.5 transition"
            >
              {analyzing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <BarChart3 className="w-3.5 h-3.5" />}
              Analyze Quality
            </button>

            <div className="w-px bg-[#1a2e1a] mx-1" />

            <button
              onClick={() => setShowExport(true)}
              className="px-3 py-2 bg-amber-600 hover:bg-amber-500 rounded text-xs font-medium flex items-center gap-1.5 transition"
            >
              <Download className="w-3.5 h-3.5" /> Export
            </button>
            <button
              onClick={handleOpenDesigner}
              className="px-3 py-2 bg-[#1a2e1a] hover:bg-[#1a2e1a] rounded text-xs font-medium flex items-center gap-1.5 transition"
            >
              <Workflow className="w-3.5 h-3.5" /> Open in Designer
            </button>
            <button
              onClick={handleOpenConvert}
              className="px-3 py-2 bg-[#1a2e1a] hover:bg-[#1a2e1a] rounded text-xs font-medium flex items-center gap-1.5 transition"
            >
              <ArrowLeftRight className="w-3.5 h-3.5" /> Open in Convert
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-3 py-2 bg-[#1a2e1a] hover:bg-[#1a2e1a] disabled:opacity-50 rounded text-xs font-medium flex items-center gap-1.5 transition"
            >
              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              Save to Library
            </button>
          </div>

          {/* Validation result */}
          {validationResult && (
            <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-4">
              <ValidationReport result={validationResult} />
            </div>
          )}

          {/* Analysis result */}
          {analysisResult && (
            <AnalysisDisplay analysis={analysisResult.analysis} />
          )}

          {/* Content view */}
          <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5">
            {view === "steps" && resultPlaybook?.workflow ? (
              <StepList
                workflow={resultPlaybook.workflow}
                workflowStart={resultPlaybook.workflow_start}
              />
            ) : (
              <PlaybookViewer
                content={JSON.stringify(result, null, 2)}
                filename="ai_generated_playbook.json"
              />
            )}
          </div>

          {/* Navigate back */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2 bg-[#111a11] hover:bg-[#1a2e1a] rounded text-sm flex items-center gap-2 text-[#7a7a6a] transition"
            >
              <ChevronLeft className="w-4 h-4" /> Modify Prompt
            </button>
            <button
              onClick={() => {
                setResult(null);
                setPrompt("");
                setSelectedProducts([]);
                setStep(1);
                setValidationResult(null);
                setAnalysisResult(null);
                setStatusMsg(null);
                setError(null);
              }}
              className="px-4 py-2 bg-[#111a11] hover:bg-[#1a2e1a] rounded text-sm text-[#7a7a6a] transition"
            >
              Start Over
            </button>
          </div>
        </div>
      )}

      {/* Export Modal */}
      {showExport && result && (
        <ExportModal
          playbook={result}
          onClose={() => setShowExport(false)}
        />
      )}
    </div>
  );
}
