"use client";

import { useEffect, useState } from "react";
import type { ProductSummary, ProductAction } from "@/lib/types";
import { listProducts, getProduct } from "@/lib/api";

export interface DesignerStep {
  id: string;
  type: "action" | "if-condition" | "parallel" | "playbook-action" | "start" | "end";
  name: string;
  description: string;
  commands: { type: string; command: string; description: string; content?: string }[];
  condition?: string;
  on_completion?: string;
  on_true?: string;
  on_false?: string;
  on_failure?: string;
  next_steps?: string[];
  product_id?: string;
  action_id?: string;
}

interface StepEditorProps {
  step: DesignerStep;
  allSteps: Record<string, DesignerStep>;
  onUpdate: (step: DesignerStep) => void;
  onDelete: (stepId: string) => void;
}

export default function StepEditor({ step, allSteps, onUpdate, onDelete }: StepEditorProps) {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [productActions, setProductActions] = useState<ProductAction[]>([]);
  const [productSearch, setProductSearch] = useState("");

  useEffect(() => {
    listProducts().then((r) => setProducts(r.products)).catch(() => {});
  }, []);

  useEffect(() => {
    if (step.product_id) {
      getProduct(step.product_id).then((p) => setProductActions(p.actions)).catch(() => {});
    } else {
      setProductActions([]);
    }
  }, [step.product_id]);

  const otherSteps = Object.values(allSteps).filter(
    (s) => s.id !== step.id && s.type !== "start" && s.type !== "end"
  );
  const allTargets = Object.values(allSteps).filter((s) => s.id !== step.id);

  const update = (partial: Partial<DesignerStep>) => {
    onUpdate({ ...step, ...partial });
  };

  const selectProductAction = (actionId: string) => {
    const action = productActions.find((a) => a.id === actionId);
    if (action) {
      const product = products.find((p) => p.id === step.product_id);
      update({
        action_id: actionId,
        commands: [
          {
            type: "http-api",
            command: `${action.http_method} ${action.endpoint_pattern}`,
            description: action.description,
            content: action.parameters
              .filter((p) => p.required)
              .map((p) => `"${p.name}": "$$${p.name}$$"`)
              .join(", "),
          },
        ],
        description: step.description || `${action.description} (${product?.name || ""})`,
      });
    }
  };

  const filteredProducts = productSearch
    ? products.filter(
        (p) =>
          p.name.toLowerCase().includes(productSearch.toLowerCase()) ||
          p.vendor.toLowerCase().includes(productSearch.toLowerCase())
      )
    : products;

  const isTerminal = step.type === "start" || step.type === "end";

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <span
            className={`w-3 h-3 rounded-full ${
              step.type === "action"
                ? "bg-blue-500"
                : step.type === "if-condition"
                ? "bg-yellow-500"
                : step.type === "parallel"
                ? "bg-green-500"
                : "bg-gray-500"
            }`}
          />
          {step.type === "start" ? "Start Step" : step.type === "end" ? "End Step" : "Edit Step"}
        </h3>
        {!isTerminal && (
          <button
            onClick={() => onDelete(step.id)}
            className="text-red-400 hover:text-red-300 text-sm px-2 py-1 rounded hover:bg-red-900/30"
          >
            Delete
          </button>
        )}
      </div>

      {/* Name */}
      <div>
        <label className="block text-sm text-[#7a7a6a] mb-1">Step Name</label>
        <input
          type="text"
          value={step.name}
          onChange={(e) => update({ name: e.target.value })}
          disabled={isTerminal}
          className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm focus:border-amber-500 focus:outline-none disabled:opacity-50"
          placeholder="Step name..."
        />
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm text-[#7a7a6a] mb-1">Description</label>
        <textarea
          value={step.description}
          onChange={(e) => update({ description: e.target.value })}
          disabled={isTerminal}
          rows={2}
          className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm focus:border-amber-500 focus:outline-none disabled:opacity-50 resize-none"
          placeholder="What does this step do..."
        />
      </div>

      {/* Type badge */}
      <div>
        <label className="block text-sm text-[#7a7a6a] mb-1">Step Type</label>
        <span className="inline-block px-3 py-1 rounded text-xs font-medium bg-[#1a2e1a] text-[#d4d4c8]">
          {step.type}
        </span>
      </div>

      {/* Action step: product + command */}
      {step.type === "action" && (
        <>
          {/* Product Selector */}
          <div>
            <label className="block text-sm text-[#7a7a6a] mb-1">Product (Optional)</label>
            <input
              type="text"
              value={productSearch}
              onChange={(e) => setProductSearch(e.target.value)}
              className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm mb-2 focus:border-amber-500 focus:outline-none"
              placeholder="Search products..."
            />
            {step.product_id ? (
              <div className="flex items-center gap-2 bg-[#1a2e1a] rounded px-3 py-2">
                <span className="text-sm text-white">
                  {products.find((p) => p.id === step.product_id)?.name || step.product_id}
                </span>
                <button
                  onClick={() => update({ product_id: undefined, action_id: undefined })}
                  className="text-red-400 hover:text-red-300 text-xs ml-auto"
                >
                  Clear
                </button>
              </div>
            ) : (
              <div className="max-h-32 overflow-y-auto space-y-1">
                {filteredProducts.slice(0, 10).map((p) => (
                  <button
                    key={p.id}
                    onClick={() => {
                      update({ product_id: p.id, action_id: undefined });
                      setProductSearch("");
                    }}
                    className="w-full text-left px-3 py-1.5 rounded text-sm text-[#d4d4c8] hover:bg-[#1a2e1a] flex items-center gap-2"
                  >
                    <span
                      className={`w-6 h-6 rounded text-[10px] font-bold flex items-center justify-center text-white ${p.logo_color}`}
                    >
                      {p.logo_abbr}
                    </span>
                    <span>{p.name}</span>
                    <span className="text-[#7a7a6a] text-xs ml-auto">{p.category}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Action Selector (when product selected) */}
          {step.product_id && productActions.length > 0 && (
            <div>
              <label className="block text-sm text-[#7a7a6a] mb-1">Product Action</label>
              <select
                value={step.action_id || ""}
                onChange={(e) => selectProductAction(e.target.value)}
                className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm focus:border-amber-500 focus:outline-none"
              >
                <option value="">Select an action...</option>
                {productActions.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name} ({a.http_method})
                  </option>
                ))}
              </select>
              {step.action_id && (
                <p className="text-xs text-[#7a7a6a] mt-1">
                  {productActions.find((a) => a.id === step.action_id)?.description}
                </p>
              )}
            </div>
          )}

          {/* Command Editor */}
          <div>
            <label className="block text-sm text-[#7a7a6a] mb-1">Command</label>
            <select
              value={step.commands?.[0]?.type || "http-api"}
              onChange={(e) => {
                const cmds = step.commands?.length ? [...step.commands] : [{ type: "http-api", command: "", description: "" }];
                cmds[0] = { ...cmds[0], type: e.target.value };
                update({ commands: cmds });
              }}
              className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm mb-2 focus:border-amber-500 focus:outline-none"
            >
              <option value="http-api">HTTP API</option>
              <option value="bash">Bash</option>
              <option value="ssh">SSH</option>
              <option value="manual">Manual</option>
              <option value="openc2-http">OpenC2</option>
            </select>
            <input
              type="text"
              value={step.commands?.[0]?.command || ""}
              onChange={(e) => {
                const cmds = step.commands?.length ? [...step.commands] : [{ type: "http-api", command: "", description: "" }];
                cmds[0] = { ...cmds[0], command: e.target.value };
                update({ commands: cmds });
              }}
              className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm mb-2 focus:border-amber-500 focus:outline-none font-mono"
              placeholder="e.g. POST /api/v1/block"
            />
            <textarea
              value={step.commands?.[0]?.content || ""}
              onChange={(e) => {
                const cmds = step.commands?.length ? [...step.commands] : [{ type: "http-api", command: "", description: "" }];
                cmds[0] = { ...cmds[0], content: e.target.value };
                update({ commands: cmds });
              }}
              rows={2}
              className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm font-mono focus:border-amber-500 focus:outline-none resize-none"
              placeholder='Request body / parameters (JSON)...'
            />
          </div>
        </>
      )}

      {/* IF-Condition */}
      {step.type === "if-condition" && (
        <>
          <div>
            <label className="block text-sm text-[#7a7a6a] mb-1">Condition Expression</label>
            <input
              type="text"
              value={step.condition || ""}
              onChange={(e) => update({ condition: e.target.value })}
              className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm font-mono focus:border-amber-500 focus:outline-none"
              placeholder='e.g. $$verdict$$ == "malicious"'
            />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-sm text-green-400 mb-1">On True &rarr;</label>
              <select
                value={step.on_true || ""}
                onChange={(e) => update({ on_true: e.target.value || undefined })}
                className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm focus:border-amber-500 focus:outline-none"
              >
                <option value="">None</option>
                {allTargets.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name || s.id}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-red-400 mb-1">On False &rarr;</label>
              <select
                value={step.on_false || ""}
                onChange={(e) => update({ on_false: e.target.value || undefined })}
                className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm focus:border-amber-500 focus:outline-none"
              >
                <option value="">None</option>
                {allTargets.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name || s.id}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </>
      )}

      {/* Parallel step */}
      {step.type === "parallel" && (
        <div>
          <label className="block text-sm text-[#7a7a6a] mb-1">Parallel Branches</label>
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {otherSteps.map((s) => (
              <label key={s.id} className="flex items-center gap-2 text-sm text-[#d4d4c8] cursor-pointer hover:bg-[#1a2e1a] rounded px-2 py-1">
                <input
                  type="checkbox"
                  checked={step.next_steps?.includes(s.id) || false}
                  onChange={(e) => {
                    const current = step.next_steps || [];
                    const next = e.target.checked
                      ? [...current, s.id]
                      : current.filter((id) => id !== s.id);
                    update({ next_steps: next });
                  }}
                  className="rounded bg-[#1a2e1a] border-[#7a7a6a]"
                />
                {s.name || s.id}
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Connection: on_completion (for action, parallel, start) */}
      {(step.type === "action" || step.type === "start" || step.type === "parallel" || step.type === "playbook-action") && (
        <div>
          <label className="block text-sm text-[#7a7a6a] mb-1">Next Step (on_completion) &rarr;</label>
          <select
            value={step.on_completion || ""}
            onChange={(e) => update({ on_completion: e.target.value || undefined })}
            className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm focus:border-amber-500 focus:outline-none"
          >
            <option value="">None (end of workflow)</option>
            {allTargets.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name || s.id}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* On Failure */}
      {step.type === "action" && (
        <div>
          <label className="block text-sm text-red-400 mb-1">On Failure &rarr; (optional)</label>
          <select
            value={step.on_failure || ""}
            onChange={(e) => update({ on_failure: e.target.value || undefined })}
            className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm focus:border-amber-500 focus:outline-none"
          >
            <option value="">None</option>
            {allTargets.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name || s.id}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
