"use client";

import { useState, useEffect, useMemo } from "react";
import { Search, X, Check, Package } from "lucide-react";
import { listProducts, type ProductListResponse } from "@/lib/api";
import { PRODUCT_CATEGORY_LABELS, type ProductSummary } from "@/lib/types";

interface ProductPickerProps {
  selected: string[];
  onChange: (ids: string[]) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  "firewall": "bg-orange-600",
  "edr-xdr": "bg-red-600",
  "siem": "bg-blue-600",
  "email-security": "bg-yellow-600",
  "waf": "bg-green-600",
  "identity-iam": "bg-amber-700",
  "threat-intel": "bg-cyan-600",
  "vulnerability-management": "bg-pink-600",
  "cloud-security": "bg-teal-600",
  "endpoint-management": "bg-amber-600",
  "ticketing": "bg-[#2a3e2a]",
};

export default function ProductPicker({ selected, onChange }: ProductPickerProps) {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listProducts()
      .then((res) => setProducts(res.products))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, []);

  // Group products by category
  const categories = useMemo(() => {
    const cats: Record<string, ProductSummary[]> = {};
    for (const p of products) {
      if (!cats[p.category]) cats[p.category] = [];
      cats[p.category].push(p);
    }
    return cats;
  }, [products]);

  // Filter products
  const filteredProducts = useMemo(() => {
    let list = products;
    if (activeCategory) {
      list = list.filter((p) => p.category === activeCategory);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.vendor.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q)
      );
    }
    return list;
  }, [products, activeCategory, search]);

  const toggle = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  const clearAll = () => onChange([]);

  if (loading) {
    return (
      <div className="text-center py-12 text-[#7a7a6a]">
        <Package className="w-8 h-8 mx-auto mb-2 animate-pulse" />
        Loading products...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Selected chips */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-xs text-[#7a7a6a] mr-1">Selected:</span>
          {selected.map((id) => {
            const p = products.find((x) => x.id === id);
            if (!p) return null;
            return (
              <span
                key={id}
                className="inline-flex items-center gap-1 px-2 py-1 bg-amber-600/20 text-amber-300 text-xs rounded-full"
              >
                <span
                  className={`w-4 h-4 rounded text-[7px] font-bold flex items-center justify-center text-white ${p.logo_color}`}
                >
                  {p.logo_abbr}
                </span>
                {p.name}
                <button
                  onClick={() => toggle(id)}
                  className="ml-0.5 hover:text-white transition"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            );
          })}
          <button
            onClick={clearAll}
            className="text-[10px] text-[#7a7a6a] hover:text-[#d4d4c8] transition ml-2"
          >
            Clear all
          </button>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#7a7a6a]" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search products by name or vendor..."
          className="w-full pl-10 pr-4 py-2 bg-[#0a0f0a] border border-[#2a3e2a] rounded text-sm text-[#d4d4c8] focus:outline-none focus:border-amber-500"
        />
      </div>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-1.5">
        <button
          onClick={() => setActiveCategory(null)}
          className={`px-2.5 py-1 text-xs rounded-full transition ${
            activeCategory === null
              ? "bg-amber-600 text-white"
              : "bg-[#111a11] text-[#7a7a6a] hover:bg-[#1a2e1a]"
          }`}
        >
          All ({products.length})
        </button>
        {Object.entries(categories).map(([cat, prods]) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(activeCategory === cat ? null : cat)}
            className={`px-2.5 py-1 text-xs rounded-full transition ${
              activeCategory === cat
                ? "bg-amber-600 text-white"
                : "bg-[#111a11] text-[#7a7a6a] hover:bg-[#1a2e1a]"
            }`}
          >
            {PRODUCT_CATEGORY_LABELS[cat] || cat} ({prods.length})
          </button>
        ))}
      </div>

      {/* Product grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
        {filteredProducts.map((p) => {
          const isSelected = selected.includes(p.id);
          return (
            <button
              key={p.id}
              onClick={() => toggle(p.id)}
              className={`relative p-3 rounded border text-left transition ${
                isSelected
                  ? "border-amber-500 bg-amber-500/10"
                  : "border-[#2a3e2a] bg-[#111a11]/50 hover:border-[#2a3e2a]"
              }`}
            >
              {isSelected && (
                <div className="absolute top-2 right-2">
                  <Check className="w-4 h-4 text-amber-400" />
                </div>
              )}
              <div className="flex items-center gap-2 mb-1.5">
                <span
                  className={`w-7 h-7 rounded text-[9px] font-bold flex items-center justify-center text-white shrink-0 ${p.logo_color}`}
                >
                  {p.logo_abbr}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-medium text-[#d4d4c8] truncate">
                    {p.name}
                  </div>
                  <div className="text-[10px] text-[#7a7a6a]">{p.vendor}</div>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`px-1.5 py-0.5 text-[9px] rounded ${
                    CATEGORY_COLORS[p.category] || "bg-[#1a2e1a]"
                  } text-white/80`}
                >
                  {PRODUCT_CATEGORY_LABELS[p.category] || p.category}
                </span>
                <span className="text-[9px] text-[#2a3e2a]">
                  {p.action_count} actions
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {filteredProducts.length === 0 && (
        <div className="text-center py-8 text-[#7a7a6a] text-sm">
          No products match your search.
        </div>
      )}
    </div>
  );
}
