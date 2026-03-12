"use client";
import { useState, useEffect, useCallback } from "react";
import { Upload, ArrowRight, AlertTriangle, CheckCircle2, Download, FileJson } from "lucide-react";
import { listPlatforms, validatePlaybook, convertPlaybook, convertAll, importPlaybook, detectFormat } from "@/lib/api";
import type { Platform, ValidateResponse, ConvertResponse } from "@/lib/api";
import { PlatformCard } from "@/components/PlatformCard";
import { ValidationReport } from "@/components/ValidationReport";
import { PlaybookViewer } from "@/components/PlaybookViewer";

export default function ConvertPage() {
  const [inputContent, setInputContent] = useState("");
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [detectedPlatform, setDetectedPlatform] = useState<string | null>(null);
  const [cacaoPlaybook, setCacaoPlaybook] = useState<Record<string, unknown> | null>(null);
  const [validation, setValidation] = useState<ValidateResponse | null>(null);
  const [conversions, setConversions] = useState<Record<string, ConvertResponse & { error?: string }>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<"input" | "validate" | "export">("input");

  useEffect(() => {
    listPlatforms().then((d) => setPlatforms(d.platforms)).catch(() => {});
    // Check for pre-loaded playbook from Designer or Playbooks page
    const stored = sessionStorage.getItem("playbookforge_convert_input");
    if (stored) {
      sessionStorage.removeItem("playbookforge_convert_input");
      setInputContent(stored);
    }
  }, []);

  const handleDetect = useCallback(async (content: string) => {
    if (!content.trim()) return;
    try {
      const result = await detectFormat(content);
      if (result.detected) {
        setDetectedPlatform(result.platform_id || null);
      } else {
        setDetectedPlatform(null);
      }
    } catch {
      setDetectedPlatform(null);
    }
  }, []);

  const handleImportAndValidate = async () => {
    if (!inputContent.trim()) return;
    setLoading(true);
    setError(null);

    try {
      let playbook: Record<string, unknown>;

      // Try parsing as CACAO JSON first
      try {
        const parsed = JSON.parse(inputContent);
        if (parsed.type === "playbook" && parsed.spec_version) {
          playbook = parsed;
        } else {
          throw new Error("Not CACAO");
        }
      } catch {
        // Try importing from vendor format
        const imported = await importPlaybook(inputContent);
        playbook = imported.playbook;
      }

      setCacaoPlaybook(playbook);

      // Validate
      const valResult = await validatePlaybook(playbook);
      setValidation(valResult);
      setStep("validate");
    } catch (e: any) {
      setError(e.message || "Failed to parse playbook");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!cacaoPlaybook) return;
    setLoading(true);
    setError(null);

    try {
      if (selectedPlatform) {
        const result = await convertPlaybook(cacaoPlaybook, selectedPlatform);
        setConversions({ [selectedPlatform]: result });
      } else {
        const result = await convertAll(cacaoPlaybook);
        setConversions(result.results);
      }
      setStep("export");
    } catch (e: any) {
      setError(e.message || "Export failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result as string;
      setInputContent(content);
      handleDetect(content);
    };
    reader.readAsText(file);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Convert Playbook</h1>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded p-3 flex items-center gap-2 text-sm text-red-300">
          <AlertTriangle className="w-4 h-4" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Panel */}
        <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5 space-y-4">
          <h2 className="font-semibold flex items-center gap-2">
            <Upload className="w-4 h-4 text-amber-400" />
            Input
          </h2>

          {/* File upload */}
          <label className="flex items-center justify-center border-2 border-dashed border-[#2a3e2a] rounded p-4 cursor-pointer hover:border-amber-500 transition">
            <input type="file" className="hidden" onChange={handleFileUpload} accept=".json,.yml,.yaml,.py" />
            <span className="text-sm text-[#7a7a6a]">Drop file or click to upload (.json, .yml, .yaml, .py)</span>
          </label>

          {/* Textarea */}
          <textarea
            value={inputContent}
            onChange={(e) => {
              setInputContent(e.target.value);
              handleDetect(e.target.value);
            }}
            placeholder="Paste your CACAO JSON or vendor playbook here..."
            className="w-full h-64 bg-[#0a0f0a] border border-[#2a3e2a] rounded p-3 text-xs font-mono text-[#d4d4c8] resize-none focus:outline-none focus:border-amber-500"
          />

          {detectedPlatform && (
            <div className="flex items-center gap-2 text-sm">
              <FileJson className="w-4 h-4 text-cyan-400" />
              <span className="text-[#7a7a6a]">Detected:</span>
              <span className="text-cyan-400 font-medium">{detectedPlatform}</span>
            </div>
          )}

          <button
            onClick={handleImportAndValidate}
            disabled={loading || !inputContent.trim()}
            className="w-full py-2.5 btn-primary disabled:opacity-50 disabled:cursor-not-allowed text-sm transition"
          >
            {loading ? "Processing..." : "Parse & Validate"}
          </button>

          {validation && <ValidationReport result={validation} />}
        </div>

        {/* Export Panel */}
        <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5 space-y-4">
          <h2 className="font-semibold flex items-center gap-2">
            <Download className="w-4 h-4 text-green-400" />
            Export
          </h2>

          {/* Platform selector */}
          <div className="space-y-2">
            <p className="text-xs text-[#7a7a6a]">Select target platform (or leave empty for all):</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {platforms.map((p) => (
                <PlatformCard
                  key={p.platform_id}
                  platformId={p.platform_id}
                  platformName={p.platform_name}
                  fileExtension={p.file_extension}
                  selected={selectedPlatform === p.platform_id}
                  onClick={() =>
                    setSelectedPlatform(selectedPlatform === p.platform_id ? null : p.platform_id)
                  }
                />
              ))}
            </div>
          </div>

          <button
            onClick={handleExport}
            disabled={loading || !cacaoPlaybook}
            className="w-full py-2.5 btn-primary disabled:opacity-50 disabled:cursor-not-allowed text-sm transition flex items-center justify-center gap-2"
          >
            <ArrowRight className="w-4 h-4" />
            {loading ? "Exporting..." : selectedPlatform ? `Export to ${selectedPlatform}` : "Export to All"}
          </button>

          {/* Results */}
          {Object.keys(conversions).length > 0 && (
            <div className="space-y-3 mt-4">
              {Object.entries(conversions).map(([pid, result]) => (
                <div key={pid} className="border border-[#2a3e2a] rounded overflow-hidden">
                  <div className="bg-[#111a11] px-3 py-2 flex items-center gap-2">
                    {result.success ? (
                      <CheckCircle2 className="w-4 h-4 text-green-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                    )}
                    <span className="text-sm font-medium">{pid}</span>
                    {result.filename && (
                      <span className="text-xs text-[#7a7a6a] ml-auto">{result.filename}</span>
                    )}
                  </div>
                  {result.success && result.content && (
                    <div className="p-3">
                      <PlaybookViewer content={result.content} filename={result.filename} />
                    </div>
                  )}
                  {result.error && (
                    <div className="p-3 text-xs text-red-400">{result.error}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
