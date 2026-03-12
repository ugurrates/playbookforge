"use client";

import { useState, useEffect, useCallback } from "react";
import { FileText, Download, Trash2, Loader2, Eye, X } from "lucide-react";
import { listUploadedFiles, downloadFile, deleteFile, type UploadedFileInfo } from "@/lib/api";

interface FileListProps {
  playbookId?: string;
  refreshKey?: number;
}

export default function FileList({ playbookId, refreshKey }: FileListProps) {
  const [files, setFiles] = useState<UploadedFileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [viewingFile, setViewingFile] = useState<UploadedFileInfo | null>(null);
  const [viewUrl, setViewUrl] = useState<string | null>(null);

  const loadFiles = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listUploadedFiles(playbookId);
      setFiles(res.files);
    } catch {
      setFiles([]);
    } finally {
      setLoading(false);
    }
  }, [playbookId]);

  useEffect(() => {
    loadFiles();
  }, [loadFiles, refreshKey]);

  const handleDownload = async (f: UploadedFileInfo) => {
    try {
      const blob = await downloadFile(f.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = f.original_filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
    }
  };

  const handleView = async (f: UploadedFileInfo) => {
    // For PDFs and images, open inline viewer
    try {
      const blob = await downloadFile(f.id);
      const url = URL.createObjectURL(blob);
      setViewingFile(f);
      setViewUrl(url);
    } catch (err) {
      console.error("View failed:", err);
    }
  };

  const closeViewer = () => {
    if (viewUrl) {
      URL.revokeObjectURL(viewUrl);
    }
    setViewingFile(null);
    setViewUrl(null);
  };

  const handleDelete = async (fileId: string) => {
    setDeletingId(fileId);
    try {
      await deleteFile(fileId);
      setFiles((prev) => prev.filter((f) => f.id !== fileId));
      if (viewingFile?.id === fileId) {
        closeViewer();
      }
    } catch (err) {
      console.error("Delete failed:", err);
    } finally {
      setDeletingId(null);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return iso;
    }
  };

  const isViewable = (contentType: string) => {
    return (
      contentType === "application/pdf" ||
      contentType.startsWith("image/") ||
      contentType === "text/plain"
    );
  };

  if (loading) {
    return (
      <div className="text-center py-8 text-[#7a7a6a]">
        <Loader2 className="w-5 h-5 mx-auto animate-spin mb-1" />
        <span className="text-xs">Loading files...</span>
      </div>
    );
  }

  if (files.length === 0 && !viewingFile) {
    return (
      <div className="text-center py-8 text-[#7a7a6a] text-sm">
        No files uploaded yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Inline Document Viewer */}
      {viewingFile && viewUrl && (
        <div className="bg-[#0f1a0f] border border-amber-500/30 rounded overflow-hidden">
          {/* Viewer header */}
          <div className="flex items-center justify-between px-4 py-2 bg-[#111a11] border-b border-[#2a3e2a]">
            <div className="flex items-center gap-2 min-w-0">
              <FileText className="w-4 h-4 text-amber-400 shrink-0" />
              <span className="text-sm text-[#d4d4c8] truncate">{viewingFile.original_filename}</span>
              <span className="text-[10px] text-[#7a7a6a]">{formatSize(viewingFile.file_size)}</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleDownload(viewingFile)}
                className="p-1.5 rounded hover:bg-[#1a2e1a] text-[#7a7a6a] hover:text-[#d4d4c8] transition"
                title="Download"
              >
                <Download className="w-4 h-4" />
              </button>
              <button
                onClick={closeViewer}
                className="p-1.5 rounded hover:bg-[#1a2e1a] text-[#7a7a6a] hover:text-[#d4d4c8] transition"
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
          {/* Viewer content */}
          <div className="bg-[#0a0f0a]">
            {viewingFile.content_type === "application/pdf" ? (
              <iframe
                src={viewUrl}
                className="w-full border-0"
                style={{ height: "75vh" }}
                title={viewingFile.original_filename}
              />
            ) : viewingFile.content_type.startsWith("image/") ? (
              <div className="flex items-center justify-center p-4" style={{ maxHeight: "75vh" }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={viewUrl}
                  alt={viewingFile.original_filename}
                  className="max-w-full max-h-[70vh] object-contain rounded"
                />
              </div>
            ) : (
              <iframe
                src={viewUrl}
                className="w-full border-0 bg-white"
                style={{ height: "60vh" }}
                title={viewingFile.original_filename}
              />
            )}
          </div>
        </div>
      )}

      {/* File list */}
      {files.map((f) => {
        const isActive = viewingFile?.id === f.id;
        return (
          <div
            key={f.id}
            className={`flex items-center gap-3 p-3 rounded border transition ${
              isActive
                ? "bg-amber-500/10 border-amber-500/30"
                : "bg-[#111a11] border-[#2a3e2a]"
            }`}
          >
            <FileText className={`w-5 h-5 shrink-0 ${isActive ? "text-amber-400" : "text-red-400"}`} />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-[#d4d4c8] truncate">{f.original_filename}</p>
              <p className="text-[10px] text-[#7a7a6a]">
                {formatSize(f.file_size)} &middot; {formatDate(f.uploaded_at)}
                {f.description && <span> &middot; {f.description}</span>}
              </p>
            </div>
            {isViewable(f.content_type) && (
              <button
                onClick={() => (isActive ? closeViewer() : handleView(f))}
                className={`p-1.5 rounded transition ${
                  isActive
                    ? "bg-amber-600/20 text-amber-300"
                    : "hover:bg-[#1a2e1a] text-[#7a7a6a] hover:text-[#d4d4c8]"
                }`}
                title={isActive ? "Close viewer" : "View"}
              >
                <Eye className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => handleDownload(f)}
              className="p-1.5 rounded hover:bg-[#1a2e1a] text-[#7a7a6a] hover:text-[#d4d4c8] transition"
              title="Download"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleDelete(f.id)}
              disabled={deletingId === f.id}
              className="p-1.5 rounded hover:bg-red-600/20 text-[#7a7a6a] hover:text-red-400 transition disabled:opacity-50"
              title="Delete"
            >
              {deletingId === f.id ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
            </button>
          </div>
        );
      })}
    </div>
  );
}
