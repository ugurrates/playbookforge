"use client";
import { AlertTriangle, XCircle, Info, CheckCircle2 } from "lucide-react";
import type { ValidateResponse } from "@/lib/api";

interface Props {
  result: ValidateResponse;
}

export function ValidationReport({ result }: Props) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        {result.valid ? (
          <CheckCircle2 className="w-5 h-5 text-green-400" />
        ) : (
          <XCircle className="w-5 h-5 text-red-400" />
        )}
        <span className={`font-semibold ${result.valid ? "text-green-400" : "text-red-400"}`}>
          {result.valid ? "Valid" : "Invalid"}
        </span>
        <span className="text-xs text-[#7a7a6a] ml-2">
          {result.error_count} errors, {result.warning_count} warnings
        </span>
      </div>

      {result.issues.length > 0 && (
        <div className="space-y-1 max-h-64 overflow-y-auto">
          {result.issues.map((issue, i) => (
            <div
              key={i}
              className={`flex items-start gap-2 text-xs p-2 rounded ${
                issue.severity === "error"
                  ? "bg-red-500/10 text-red-300"
                  : issue.severity === "warning"
                  ? "bg-yellow-500/10 text-yellow-300"
                  : "bg-blue-500/10 text-blue-300"
              }`}
            >
              {issue.severity === "error" ? (
                <XCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              ) : issue.severity === "warning" ? (
                <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              ) : (
                <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              )}
              <span>
                <strong>[{issue.code}]</strong> {issue.message}
                {issue.path && <span className="opacity-60 ml-1">@ {issue.path}</span>}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
