"use client";

import { useState } from "react";
import { FileDown, Loader2 } from "lucide-react";
import { generatePdf, generateLibraryPdf } from "@/lib/api";

interface PdfDownloadButtonProps {
  playbook?: Record<string, unknown>;
  libraryId?: string;
  label?: string;
  className?: string;
}

export default function PdfDownloadButton({
  playbook,
  libraryId,
  label = "Download PDF",
  className = "",
}: PdfDownloadButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      let blob: Blob;
      if (libraryId) {
        blob = await generateLibraryPdf(libraryId);
      } else if (playbook) {
        blob = await generatePdf(playbook);
      } else {
        return;
      }

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const name = playbook
        ? (playbook.name as string || "playbook").replace(/\s+/g, "_")
        : libraryId || "playbook";
      a.download = `${name}_report.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF download failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={loading || (!playbook && !libraryId)}
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium transition ${
        loading
          ? "bg-[#1a2e1a] text-[#7a7a6a] cursor-wait"
          : "bg-red-600/20 text-red-300 hover:bg-red-600/30"
      } ${className}`}
    >
      {loading ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : (
        <FileDown className="w-3.5 h-3.5" />
      )}
      {loading ? "Generating..." : label}
    </button>
  );
}
