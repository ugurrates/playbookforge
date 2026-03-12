"use client";

import { useState, useCallback, useEffect, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Plus,
  Download,
  Upload,
  Play,
  Square,
  Zap,
  GitBranch,
  GitFork,
  CheckCircle,
  AlertTriangle,
  Save,
  ArrowLeftRight,
  FileText,
  ChevronDown,
} from "lucide-react";
import type { CacaoPlaybook, WorkflowStep } from "@/lib/types";
import { PlaybookViewer } from "@/components/PlaybookViewer";
import { ValidationReport } from "@/components/ValidationReport";
import StepEditor, { type DesignerStep } from "@/components/designer/StepEditor";
import PlaybookMetaEditor from "@/components/designer/PlaybookMetaEditor";
import { validatePlaybook, librarySave, convertPlaybook, type ValidateResponse } from "@/lib/api";

// ============================================================================
// Custom Node Component
// ============================================================================
function StepNode({
  data,
  selected,
}: {
  data: { label: string; stepType: string; description?: string };
  selected?: boolean;
}) {
  const colorMap: Record<string, string> = {
    start: "border-gray-500 bg-gray-800",
    end: "border-gray-500 bg-gray-800",
    action: "border-blue-500 bg-blue-900/50",
    "if-condition": "border-yellow-500 bg-yellow-900/50",
    parallel: "border-green-500 bg-green-900/50",
    "playbook-action": "border-amber-500 bg-amber-900/50",
  };
  const style = colorMap[data.stepType] || "border-[#2a3e2a] bg-[#111a11]";

  const iconMap: Record<string, React.ElementType> = {
    start: Play,
    end: Square,
    action: Zap,
    "if-condition": GitBranch,
    parallel: GitFork,
  };
  const Icon = iconMap[data.stepType] || Zap;

  return (
    <div
      className={`px-4 py-3 rounded border-2 ${style} min-w-[180px] max-w-[250px] transition-all ${
        selected ? "ring-2 ring-amber-400 ring-offset-2 ring-offset-[#0f1a0f]" : ""
      }`}
    >
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-[#d4d4c8] flex-shrink-0" />
        <span className="text-sm font-medium text-[#d4d4c8] truncate">{data.label}</span>
      </div>
      {data.description && (
        <p className="text-[10px] text-[#7a7a6a] mt-1 line-clamp-2">{data.description}</p>
      )}
      <span className="text-[9px] text-[#7a7a6a] font-mono">{data.stepType}</span>
    </div>
  );
}

const nodeTypes: NodeTypes = { step: StepNode };

// ============================================================================
// Conversion: DesignerState <-> CACAO <-> ReactFlow
// ============================================================================

interface PlaybookMeta {
  name: string;
  description: string;
  playbook_types: string[];
  labels: string[];
  variables: Record<string, { type: string; value?: string; description?: string; external?: boolean }>;
}

function generateId(type: string): string {
  const hex = () => Math.random().toString(16).substring(2, 6);
  return `${type}--${hex()}${hex()}-${hex()}-${hex()}-${hex()}-${hex()}${hex()}${hex()}`;
}

function stepsToPlaybook(
  steps: Record<string, DesignerStep>,
  meta: PlaybookMeta
): Record<string, unknown> {
  const workflow: Record<string, Record<string, unknown>> = {};
  let workflowStart = "";

  for (const [id, step] of Object.entries(steps)) {
    if (step.type === "start") workflowStart = id;

    const wfStep: Record<string, unknown> = {
      type: step.type,
      name: step.name,
    };

    if (step.description) wfStep.description = step.description;
    if (step.on_completion) wfStep.on_completion = step.on_completion;
    if (step.on_failure) wfStep.on_failure = step.on_failure;

    if (step.type === "action" && step.commands?.length) {
      wfStep.commands = step.commands.map((c) => ({
        type: c.type || "http-api",
        command: c.command || "",
        description: c.description || "",
        ...(c.content ? { content: c.content } : {}),
      }));
    }

    if (step.type === "if-condition") {
      if (step.condition) wfStep.condition = step.condition;
      if (step.on_true) wfStep.on_true = step.on_true;
      if (step.on_false) wfStep.on_false = step.on_false;
    }

    if (step.type === "parallel" && step.next_steps?.length) {
      wfStep.next_steps = step.next_steps;
    }

    workflow[id] = wfStep;
  }

  const variables: Record<string, Record<string, unknown>> = {};
  for (const [name, v] of Object.entries(meta.variables)) {
    variables[name] = {
      type: v.type,
      ...(v.value ? { value: v.value } : {}),
      ...(v.description ? { description: v.description } : {}),
      ...(v.external ? { external: true } : {}),
    };
  }

  const now = new Date().toISOString();
  return {
    type: "playbook",
    spec_version: "cacao-2.0",
    id: generateId("playbook"),
    name: meta.name || "Untitled Playbook",
    description: meta.description || "",
    playbook_types: meta.playbook_types.length ? meta.playbook_types : ["investigation"],
    created_by: generateId("identity"),
    created: now,
    modified: now,
    revoked: false,
    workflow_start: workflowStart,
    workflow,
    ...(meta.labels.length ? { labels: meta.labels } : {}),
    ...(Object.keys(variables).length ? { playbook_variables: variables } : {}),
  };
}

function playbookToSteps(playbook: CacaoPlaybook): {
  steps: Record<string, DesignerStep>;
  meta: PlaybookMeta;
} {
  const steps: Record<string, DesignerStep> = {};

  for (const [id, step] of Object.entries(playbook.workflow)) {
    steps[id] = {
      id,
      type: step.type as DesignerStep["type"],
      name: step.name || id.split("--")[0],
      description: step.description || "",
      commands: step.commands?.map((c) => ({
        type: c.type || "http-api",
        command: c.command || "",
        description: c.description || "",
        content: c.content,
      })) || [],
      condition: step.condition,
      on_completion: step.on_completion,
      on_true: step.on_true,
      on_false: step.on_false,
      on_failure: step.on_failure,
      next_steps: step.next_steps,
    };
  }

  const variables: PlaybookMeta["variables"] = {};
  if (playbook.playbook_variables) {
    for (const [name, v] of Object.entries(playbook.playbook_variables)) {
      variables[name] = {
        type: v.type,
        value: v.value,
        description: v.description,
        external: v.external,
      };
    }
  }

  return {
    steps,
    meta: {
      name: playbook.name || "",
      description: playbook.description || "",
      playbook_types: playbook.playbook_types || [],
      labels: playbook.labels || [],
      variables,
    },
  };
}

function stepsToFlow(steps: Record<string, DesignerStep>): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  const positions = new Map<string, { x: number; y: number }>();

  // BFS layout starting from start step
  const startId = Object.keys(steps).find((id) => steps[id].type === "start");
  if (!startId) return { nodes: [], edges: [] };

  const queue: { id: string; x: number; y: number }[] = [{ id: startId, x: 400, y: 0 }];
  const visited = new Set<string>();
  let row = 0;

  while (queue.length > 0) {
    const { id, x, y } = queue.shift()!;
    if (visited.has(id)) continue;
    visited.add(id);

    const step = steps[id];
    if (!step) continue;

    positions.set(id, { x, y });
    const nextY = y + 130;

    // Collect next step IDs
    if (step.on_completion && !visited.has(step.on_completion)) {
      queue.push({ id: step.on_completion, x, y: nextY });
      edges.push({
        id: `${id}->oc->${step.on_completion}`,
        source: id,
        target: step.on_completion,
        animated: true,
        style: { stroke: "#6366f1" },
      });
    }
    if (step.on_true && !visited.has(step.on_true)) {
      queue.push({ id: step.on_true, x: x - 150, y: nextY });
      edges.push({
        id: `${id}->t->${step.on_true}`,
        source: id,
        target: step.on_true,
        animated: true,
        label: "true",
        style: { stroke: "#22c55e" },
      });
    }
    if (step.on_false && !visited.has(step.on_false)) {
      queue.push({ id: step.on_false, x: x + 150, y: nextY });
      edges.push({
        id: `${id}->f->${step.on_false}`,
        source: id,
        target: step.on_false,
        label: "false",
        style: { stroke: "#ef4444" },
      });
    }
    if (step.next_steps) {
      step.next_steps.forEach((nid, i) => {
        if (!visited.has(nid)) {
          queue.push({ id: nid, x: x - 150 + i * 200, y: nextY });
        }
        edges.push({
          id: `${id}->p${i}->${nid}`,
          source: id,
          target: nid,
          animated: true,
          style: { stroke: "#22c55e" },
        });
      });
    }
    if (step.on_failure) {
      edges.push({
        id: `${id}->fail->${step.on_failure}`,
        source: id,
        target: step.on_failure,
        label: "fail",
        style: { stroke: "#f97316" },
      });
    }
    row++;
  }

  // Add nodes that weren't reachable from start
  for (const [id, step] of Object.entries(steps)) {
    if (!visited.has(id)) {
      positions.set(id, { x: 700, y: row * 130 });
      row++;
    }
  }

  for (const [id, step] of Object.entries(steps)) {
    const pos = positions.get(id) || { x: 0, y: 0 };
    nodes.push({
      id,
      type: "step",
      position: pos,
      data: { label: step.name || id, stepType: step.type, description: step.description },
    });
  }

  return { nodes, edges };
}

// ============================================================================
// Main Designer Page
// ============================================================================

export default function DesignerPage() {
  // Core state: steps are the source of truth
  const [steps, setSteps] = useState<Record<string, DesignerStep>>(() => {
    const startId = generateId("start");
    const endId = generateId("end");
    return {
      [startId]: { id: startId, type: "start", name: "Start", description: "", commands: [], on_completion: endId },
      [endId]: { id: endId, type: "end", name: "End", description: "", commands: [] },
    };
  });

  const [meta, setMeta] = useState<PlaybookMeta>({
    name: "New Playbook",
    description: "",
    playbook_types: ["investigation"],
    labels: [],
    variables: {},
  });

  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [showJsonPanel, setShowJsonPanel] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidateResponse | null>(null);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);
  const [stepCounter, setStepCounter] = useState(1);
  const [showAddMenu, setShowAddMenu] = useState(false);

  // ReactFlow state derived from steps
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Recompute flow whenever steps change
  useEffect(() => {
    const { nodes: n, edges: e } = stepsToFlow(steps);
    setNodes(n);
    setEdges(e);
  }, [steps, setNodes, setEdges]);

  // Load from sessionStorage (from Playbooks or Convert page)
  useEffect(() => {
    const stored = sessionStorage.getItem("playbookforge_designer_input");
    if (stored) {
      sessionStorage.removeItem("playbookforge_designer_input");
      try {
        const pb = JSON.parse(stored) as CacaoPlaybook;
        const { steps: s, meta: m } = playbookToSteps(pb);
        setSteps(s);
        setMeta(m);
        setStatusMsg({ type: "info", text: "Playbook loaded from library" });
      } catch {
        setStatusMsg({ type: "error", text: "Failed to load playbook" });
      }
    }
  }, []);

  // Generate CACAO JSON
  const cacaoJson = useMemo(() => {
    return JSON.stringify(stepsToPlaybook(steps, meta), null, 2);
  }, [steps, meta]);

  // Node click handler
  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedStepId(node.id);
    setShowJsonPanel(false);
  }, []);

  // Background click to deselect
  const onPaneClick = useCallback(() => {
    setSelectedStepId(null);
  }, []);

  // Add step
  const addStep = useCallback(
    (type: "action" | "if-condition" | "parallel") => {
      const id = generateId(type === "if-condition" ? "if-condition" : type);
      const num = stepCounter;
      setStepCounter((c) => c + 1);

      const endId = Object.keys(steps).find((k) => steps[k].type === "end");
      const newStep: DesignerStep = {
        id,
        type,
        name: `${type === "action" ? "Action" : type === "if-condition" ? "Condition" : "Parallel"} ${num}`,
        description: "",
        commands: type === "action" ? [{ type: "http-api", command: "", description: "" }] : [],
        on_completion: endId,
        ...(type === "if-condition" ? { condition: "" } : {}),
        ...(type === "parallel" ? { next_steps: [] } : {}),
      };

      // Find the last step before end and wire it to the new step
      const lastBeforeEnd = Object.values(steps).find((s) => s.on_completion === endId && s.type !== "end");

      setSteps((prev) => {
        const next = { ...prev, [id]: newStep };
        if (lastBeforeEnd) {
          next[lastBeforeEnd.id] = { ...lastBeforeEnd, on_completion: id };
        }
        return next;
      });
      setSelectedStepId(id);
      setShowAddMenu(false);
    },
    [steps, stepCounter]
  );

  // Update step
  const updateStep = useCallback((updatedStep: DesignerStep) => {
    setSteps((prev) => ({ ...prev, [updatedStep.id]: updatedStep }));
  }, []);

  // Delete step
  const deleteStep = useCallback(
    (stepId: string) => {
      const step = steps[stepId];
      if (!step || step.type === "start" || step.type === "end") return;

      setSteps((prev) => {
        const next = { ...prev };
        delete next[stepId];

        // Rewire: anything pointing to this step should point to this step's on_completion
        const replacement = step.on_completion || step.on_true || Object.keys(next).find((k) => next[k].type === "end");
        for (const [id, s] of Object.entries(next)) {
          if (s.on_completion === stepId) next[id] = { ...s, on_completion: replacement };
          if (s.on_true === stepId) next[id] = { ...next[id], on_true: replacement };
          if (s.on_false === stepId) next[id] = { ...next[id], on_false: replacement };
          if (s.next_steps?.includes(stepId)) {
            next[id] = { ...next[id], next_steps: s.next_steps.filter((ns) => ns !== stepId) };
          }
        }
        return next;
      });
      setSelectedStepId(null);
    },
    [steps]
  );

  // Validate
  const handleValidate = async () => {
    try {
      const pb = JSON.parse(cacaoJson);
      const result = await validatePlaybook(pb);
      setValidationResult(result);
      if (result.valid) {
        setStatusMsg({ type: "success", text: `Valid! ${Object.keys(steps).length} steps` });
      } else {
        setStatusMsg({ type: "error", text: `${result.error_count} errors, ${result.warning_count} warnings` });
      }
    } catch (err) {
      setStatusMsg({ type: "error", text: `Validation failed: ${err}` });
    }
  };

  // Save to library
  const handleSave = async () => {
    try {
      const pb = JSON.parse(cacaoJson);
      const result = await librarySave(pb, "designer", meta.labels);
      setStatusMsg({ type: "success", text: `Saved to library: ${result.id}` });
    } catch (err) {
      setStatusMsg({ type: "error", text: `Save failed: ${err}` });
    }
  };

  // Export CACAO JSON file
  const handleExport = () => {
    const blob = new Blob([cacaoJson], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${meta.name.replace(/\s+/g, "_").toLowerCase()}_cacao.json`;
    a.click();
    URL.revokeObjectURL(url);
    setStatusMsg({ type: "success", text: "CACAO JSON downloaded" });
  };

  // Import CACAO JSON file
  const handleImport = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json";
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        try {
          const pb = JSON.parse(ev.target?.result as string) as CacaoPlaybook;
          const { steps: s, meta: m } = playbookToSteps(pb);
          setSteps(s);
          setMeta(m);
          setStatusMsg({ type: "success", text: `Imported: ${pb.name}` });
        } catch {
          setStatusMsg({ type: "error", text: "Invalid CACAO JSON file" });
        }
      };
      reader.readAsText(file);
    };
    input.click();
  };

  // Navigate to Convert with playbook
  const handleOpenInConvert = () => {
    sessionStorage.setItem("playbookforge_convert_input", cacaoJson);
    window.location.href = "/convert";
  };

  const selectedStep = selectedStepId ? steps[selectedStepId] : null;

  return (
    <div className="h-[calc(100vh-7rem)] flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h1 className="text-xl font-bold text-white">Playbook Designer</h1>
        <div className="flex gap-2 flex-wrap">
          {/* Add Step Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowAddMenu(!showAddMenu)}
              className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 rounded text-sm flex items-center gap-1 text-white"
            >
              <Plus className="w-3.5 h-3.5" /> Add Step <ChevronDown className="w-3 h-3" />
            </button>
            {showAddMenu && (
              <div className="absolute top-full mt-1 left-0 bg-[#111a11] border border-[#2a3e2a] rounded shadow-xl z-50 min-w-[160px]">
                <button
                  onClick={() => addStep("action")}
                  className="w-full text-left px-4 py-2 text-sm text-[#d4d4c8] hover:bg-blue-900/50 flex items-center gap-2"
                >
                  <Zap className="w-3.5 h-3.5 text-blue-400" /> Action
                </button>
                <button
                  onClick={() => addStep("if-condition")}
                  className="w-full text-left px-4 py-2 text-sm text-[#d4d4c8] hover:bg-yellow-900/50 flex items-center gap-2"
                >
                  <GitBranch className="w-3.5 h-3.5 text-yellow-400" /> Condition
                </button>
                <button
                  onClick={() => addStep("parallel")}
                  className="w-full text-left px-4 py-2 text-sm text-[#d4d4c8] hover:bg-green-900/50 flex items-center gap-2"
                >
                  <GitFork className="w-3.5 h-3.5 text-green-400" /> Parallel
                </button>
              </div>
            )}
          </div>

          <button onClick={handleImport} className="px-3 py-1.5 bg-[#1a2e1a] hover:bg-[#1a2e1a] rounded text-sm flex items-center gap-1 text-white">
            <Upload className="w-3.5 h-3.5" /> Import
          </button>
          <button onClick={handleExport} className="px-3 py-1.5 bg-[#1a2e1a] hover:bg-[#1a2e1a] rounded text-sm flex items-center gap-1 text-white">
            <Download className="w-3.5 h-3.5" /> Export
          </button>
          <button onClick={handleValidate} className="px-3 py-1.5 bg-emerald-700 hover:bg-emerald-600 rounded text-sm flex items-center gap-1 text-white">
            <CheckCircle className="w-3.5 h-3.5" /> Validate
          </button>
          <button onClick={handleSave} className="px-3 py-1.5 bg-amber-700 hover:bg-amber-600 rounded text-sm flex items-center gap-1 text-white">
            <Save className="w-3.5 h-3.5" /> Save
          </button>
          <button onClick={handleOpenInConvert} className="px-3 py-1.5 bg-[#1a2e1a] hover:bg-[#1a2e1a] rounded text-sm flex items-center gap-1 text-white">
            <ArrowLeftRight className="w-3.5 h-3.5" /> Convert
          </button>
          <button
            onClick={() => { setShowJsonPanel(!showJsonPanel); setSelectedStepId(null); }}
            className={`px-3 py-1.5 rounded text-sm flex items-center gap-1 text-white ${
              showJsonPanel ? "bg-amber-600" : "bg-[#1a2e1a] hover:bg-[#1a2e1a]"
            }`}
          >
            <FileText className="w-3.5 h-3.5" /> JSON
          </button>
        </div>
      </div>

      {/* Status Message */}
      {statusMsg && (
        <div
          className={`mb-2 px-4 py-2 rounded text-sm flex items-center gap-2 ${
            statusMsg.type === "success"
              ? "bg-green-900/50 text-green-300 border border-green-800"
              : statusMsg.type === "error"
              ? "bg-red-900/50 text-red-300 border border-red-800"
              : "bg-blue-900/50 text-blue-300 border border-blue-800"
          }`}
        >
          {statusMsg.type === "success" ? (
            <CheckCircle className="w-4 h-4" />
          ) : statusMsg.type === "error" ? (
            <AlertTriangle className="w-4 h-4" />
          ) : null}
          {statusMsg.text}
          <button onClick={() => setStatusMsg(null)} className="ml-auto text-xs opacity-50 hover:opacity-100">
            &times;
          </button>
        </div>
      )}

      {/* Main content: Canvas + Right Panel */}
      <div className="flex-1 flex gap-3 min-h-0">
        {/* Left: ReactFlow Canvas */}
        <div className="flex-1 bg-[#0f1a0f] border border-[#1a2e1a] rounded overflow-hidden">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
            className="bg-[#0a0f0a]"
          >
            <Background color="#334155" gap={20} />
            <Controls className="!bg-[#111a11] !border-[#2a3e2a] !rounded [&>button]:!bg-[#111a11] [&>button]:!border-[#2a3e2a] [&>button]:!text-[#d4d4c8]" />
            <MiniMap nodeColor={() => "#6366f1"} className="!bg-[#111a11] !border-[#2a3e2a] !rounded" />
          </ReactFlow>
        </div>

        {/* Right: Editor Panel */}
        <div className="w-[380px] flex-shrink-0 bg-[#111a11] border border-[#2a3e2a] rounded p-4 overflow-y-auto">
          {showJsonPanel ? (
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">CACAO JSON Output</h3>
              <PlaybookViewer
                content={cacaoJson}
                filename={`${meta.name.replace(/\s+/g, "_").toLowerCase()}_cacao.json`}
              />
              {validationResult && (
                <div className="mt-3">
                  <ValidationReport result={validationResult} />
                </div>
              )}
            </div>
          ) : selectedStep ? (
            <StepEditor
              step={selectedStep}
              allSteps={steps}
              onUpdate={updateStep}
              onDelete={deleteStep}
            />
          ) : (
            <PlaybookMetaEditor meta={meta} onUpdate={setMeta} />
          )}
        </div>
      </div>

      {/* Step count info */}
      <div className="mt-2 flex items-center gap-4 text-xs text-[#7a7a6a]">
        <span>{Object.keys(steps).length} steps</span>
        <span>{Object.values(steps).filter((s) => s.type === "action").length} actions</span>
        <span>{Object.values(steps).filter((s) => s.type === "if-condition").length} conditions</span>
        <span>{Object.keys(meta.variables).length} variables</span>
      </div>
    </div>
  );
}
