"use client";

import { useState, useEffect } from "react";
import { FolderOpen } from "lucide-react";
import FileUploadZone from "@/components/FileUploadZone";
import FileList from "@/components/FileList";
import { listUploadedFiles } from "@/lib/api";

export default function DocumentsPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [totalFiles, setTotalFiles] = useState<number | null>(null);

  useEffect(() => {
    listUploadedFiles()
      .then((res) => setTotalFiles(res.total))
      .catch(() => setTotalFiles(null));
  }, [refreshKey]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FolderOpen className="w-6 h-6 text-amber-400" />
          Documents
        </h1>
        {totalFiles !== null && (
          <span className="text-sm text-[#7a7a6a]">{totalFiles} files</span>
        )}
      </div>

      <p className="text-sm text-[#7a7a6a]">
        Upload PDF documents, reports, and reference materials for your SOC team.
        Files uploaded here are accessible to all analysts.
      </p>

      {/* Upload Zone */}
      <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5">
        <h2 className="text-sm font-medium text-[#d4d4c8] mb-3">Upload Document</h2>
        <FileUploadZone onUploaded={() => setRefreshKey((k) => k + 1)} />
      </div>

      {/* File List */}
      <div className="bg-[#0f1a0f] border border-[#1a2e1a] rounded p-5">
        <h2 className="text-sm font-medium text-[#d4d4c8] mb-3">All Documents</h2>
        <FileList refreshKey={refreshKey} />
      </div>
    </div>
  );
}
