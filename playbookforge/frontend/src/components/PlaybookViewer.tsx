"use client";
import { useState } from "react";
import { Copy, Check, Download } from "lucide-react";

interface Props {
  content: string;
  filename?: string;
  language?: string;
}

export function PlaybookViewer({ content, filename, language }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "playbook.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="relative group">
      <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition z-10">
        <button
          onClick={handleCopy}
          className="p-1.5 rounded bg-[#1a2e1a] hover:bg-[#1a2e1a] text-[#d4d4c8]"
          title="Copy"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
        </button>
        {filename && (
          <button
            onClick={handleDownload}
            className="p-1.5 rounded bg-[#1a2e1a] hover:bg-[#1a2e1a] text-[#d4d4c8]"
            title="Download"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
      {filename && (
        <div className="text-[10px] text-[#7a7a6a] font-mono mb-1">{filename}</div>
      )}
      <pre className="text-xs text-[#d4d4c8] max-h-96 overflow-auto whitespace-pre">
        {content}
      </pre>
    </div>
  );
}
