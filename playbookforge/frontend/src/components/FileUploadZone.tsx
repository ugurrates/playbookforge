"use client";

import { useState, useRef, useCallback } from "react";
import { Upload, FileText, Loader2, X } from "lucide-react";
import { uploadFile } from "@/lib/api";

interface FileUploadZoneProps {
  playbookId?: string;
  onUploaded?: () => void;
}

export default function FileUploadZone({ playbookId, onUploaded }: FileUploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [description, setDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
      setError("");
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError("");
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setError("");
    try {
      await uploadFile(selectedFile, description, playbookId || "", "");
      setSelectedFile(null);
      setDescription("");
      if (inputRef.current) inputRef.current.value = "";
      onUploaded?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded p-6 text-center cursor-pointer transition ${
          dragging
            ? "border-amber-500 bg-amber-500/10"
            : "border-[#2a3e2a] hover:border-[#2a3e2a] bg-[#111a11]/30"
        }`}
      >
        <Upload className={`w-8 h-8 mx-auto mb-2 ${dragging ? "text-amber-400" : "text-[#7a7a6a]"}`} />
        <p className="text-sm text-[#7a7a6a]">
          Drop a file here or <span className="text-amber-400">browse</span>
        </p>
        <p className="text-[10px] text-[#2a3e2a] mt-1">PDF, DOCX, TXT, images — max 20 MB</p>
        <input
          ref={inputRef}
          type="file"
          onChange={handleFileSelect}
          className="hidden"
          accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.csv,.xlsx"
        />
      </div>

      {selectedFile && (
        <div className="bg-[#111a11] rounded p-3 space-y-2">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-amber-400 shrink-0" />
            <span className="text-sm text-[#d4d4c8] truncate flex-1">{selectedFile.name}</span>
            <span className="text-[10px] text-[#7a7a6a]">{formatSize(selectedFile.size)}</span>
            <button
              onClick={() => setSelectedFile(null)}
              className="text-[#7a7a6a] hover:text-[#b0b0a0]"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
            className="w-full px-3 py-1.5 bg-[#0f1a0f] border border-[#2a3e2a] rounded text-xs text-[#d4d4c8] focus:outline-none focus:border-amber-500"
          />
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full py-1.5 btn-primary text-xs transition disabled:opacity-50"
          >
            {uploading ? (
              <span className="inline-flex items-center gap-1.5">
                <Loader2 className="w-3 h-3 animate-spin" />
                Uploading...
              </span>
            ) : (
              "Upload File"
            )}
          </button>
        </div>
      )}

      {error && (
        <p className="text-xs text-red-400">{error}</p>
      )}
    </div>
  );
}
