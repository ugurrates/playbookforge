"use client";

import { useState } from "react";

interface PlaybookMeta {
  name: string;
  description: string;
  playbook_types: string[];
  labels: string[];
  variables: Record<string, { type: string; value?: string; description?: string; external?: boolean }>;
}

interface PlaybookMetaEditorProps {
  meta: PlaybookMeta;
  onUpdate: (meta: PlaybookMeta) => void;
}

const PLAYBOOK_TYPES = [
  "investigation",
  "detection",
  "prevention",
  "mitigation",
  "remediation",
  "notification",
  "attack",
];

export default function PlaybookMetaEditor({ meta, onUpdate }: PlaybookMetaEditorProps) {
  const [newLabel, setNewLabel] = useState("");
  const [newVarName, setNewVarName] = useState("");
  const [newVarType, setNewVarType] = useState("string");

  const update = (partial: Partial<PlaybookMeta>) => {
    onUpdate({ ...meta, ...partial });
  };

  const addLabel = () => {
    if (newLabel && !meta.labels.includes(newLabel)) {
      update({ labels: [...meta.labels, newLabel] });
      setNewLabel("");
    }
  };

  const removeLabel = (label: string) => {
    update({ labels: meta.labels.filter((l) => l !== label) });
  };

  const addVariable = () => {
    if (newVarName && !meta.variables[newVarName]) {
      update({
        variables: {
          ...meta.variables,
          [newVarName]: { type: newVarType, external: true },
        },
      });
      setNewVarName("");
    }
  };

  const removeVariable = (name: string) => {
    const next = { ...meta.variables };
    delete next[name];
    update({ variables: next });
  };

  const updateVariable = (name: string, field: string, value: string | boolean) => {
    update({
      variables: {
        ...meta.variables,
        [name]: { ...meta.variables[name], [field]: value },
      },
    });
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">Playbook Properties</h3>

      {/* Name */}
      <div>
        <label className="block text-sm text-[#7a7a6a] mb-1">Playbook Name</label>
        <input
          type="text"
          value={meta.name}
          onChange={(e) => update({ name: e.target.value })}
          className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm focus:border-amber-500 focus:outline-none"
          placeholder="My Security Playbook"
        />
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm text-[#7a7a6a] mb-1">Description</label>
        <textarea
          value={meta.description}
          onChange={(e) => update({ description: e.target.value })}
          rows={3}
          className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-2 text-white text-sm focus:border-amber-500 focus:outline-none resize-none"
          placeholder="Describe the playbook purpose..."
        />
      </div>

      {/* Playbook Types */}
      <div>
        <label className="block text-sm text-[#7a7a6a] mb-1">Playbook Types</label>
        <div className="flex flex-wrap gap-2">
          {PLAYBOOK_TYPES.map((t) => (
            <label key={t} className="flex items-center gap-1 cursor-pointer">
              <input
                type="checkbox"
                checked={meta.playbook_types.includes(t)}
                onChange={(e) => {
                  const types = e.target.checked
                    ? [...meta.playbook_types, t]
                    : meta.playbook_types.filter((pt) => pt !== t);
                  update({ playbook_types: types });
                }}
                className="rounded bg-[#1a2e1a] border-[#2a3e2a]"
              />
              <span className="text-xs text-[#d4d4c8]">{t}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Labels */}
      <div>
        <label className="block text-sm text-[#7a7a6a] mb-1">Labels</label>
        <div className="flex flex-wrap gap-1 mb-2">
          {meta.labels.map((l) => (
            <span
              key={l}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-amber-900/50 text-amber-300"
            >
              {l}
              <button onClick={() => removeLabel(l)} className="hover:text-red-400">&times;</button>
            </span>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addLabel()}
            className="flex-1 bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-1.5 text-white text-sm focus:border-amber-500 focus:outline-none"
            placeholder="Add label..."
          />
          <button onClick={addLabel} className="px-3 py-1.5 bg-amber-600 text-white text-sm rounded hover:bg-amber-500">
            Add
          </button>
        </div>
      </div>

      {/* Variables */}
      <div>
        <label className="block text-sm text-[#7a7a6a] mb-1">Variables</label>
        <div className="space-y-2 mb-2">
          {Object.entries(meta.variables).map(([name, v]) => (
            <div key={name} className="bg-[#1a2e1a] rounded p-2 text-sm">
              <div className="flex items-center justify-between mb-1">
                <span className="text-amber-300 font-mono text-xs">{name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[#7a7a6a] text-xs">{v.type}</span>
                  <label className="flex items-center gap-1 text-xs text-[#7a7a6a] cursor-pointer">
                    <input
                      type="checkbox"
                      checked={v.external || false}
                      onChange={(e) => updateVariable(name, "external", e.target.checked)}
                      className="rounded bg-[#1a2e1a] border-[#2a3e2a]"
                    />
                    external
                  </label>
                  <button onClick={() => removeVariable(name)} className="text-red-400 hover:text-red-300 text-xs">
                    &times;
                  </button>
                </div>
              </div>
              <input
                type="text"
                value={v.value || ""}
                onChange={(e) => updateVariable(name, "value", e.target.value)}
                className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-2 py-1 text-white text-xs focus:border-amber-500 focus:outline-none mb-1"
                placeholder="Default value..."
              />
              <input
                type="text"
                value={v.description || ""}
                onChange={(e) => updateVariable(name, "description", e.target.value)}
                className="w-full bg-[#1a2e1a] border border-[#2a3e2a] rounded px-2 py-1 text-white text-xs focus:border-amber-500 focus:outline-none"
                placeholder="Description..."
              />
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={newVarName}
            onChange={(e) => setNewVarName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addVariable()}
            className="flex-1 bg-[#1a2e1a] border border-[#2a3e2a] rounded px-3 py-1.5 text-white text-sm focus:border-amber-500 focus:outline-none"
            placeholder="Variable name..."
          />
          <select
            value={newVarType}
            onChange={(e) => setNewVarType(e.target.value)}
            className="bg-[#1a2e1a] border border-[#2a3e2a] rounded px-2 py-1.5 text-white text-xs focus:border-amber-500 focus:outline-none"
          >
            <option value="string">string</option>
            <option value="integer">integer</option>
            <option value="boolean">boolean</option>
            <option value="ipv4-addr">ipv4-addr</option>
            <option value="ipv6-addr">ipv6-addr</option>
            <option value="uri">uri</option>
            <option value="hash">hash</option>
            <option value="list">list</option>
          </select>
          <button onClick={addVariable} className="px-3 py-1.5 bg-amber-600 text-white text-sm rounded hover:bg-amber-500">
            Add
          </button>
        </div>
      </div>
    </div>
  );
}
