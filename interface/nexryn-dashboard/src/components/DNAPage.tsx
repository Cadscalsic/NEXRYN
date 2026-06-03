import { useState } from "react";
import { dnaTraits } from "../data/mockNexrynRuntime";
import type { DNATrait } from "../data/mockNexrynRuntime";
import { DNAHealthSummary } from "./DNAHealthSummary";
import { DNAProtectionGate } from "./DNAProtectionGate";
import { DNATraitCard } from "./DNATraitCard";
import { TraitDetailPanel } from "./TraitDetailPanel";

export function DNAPage() {
  const [selectedTrait, setSelectedTrait] = useState<DNATrait>(dnaTraits[0]);

  return (
    <main className="space-y-4 p-4">
      <section className="relative overflow-hidden rounded-lg border border-white/10 bg-white/[0.035] p-5 shadow-runtime backdrop-blur-xl">
        <div className="absolute right-8 top-6 h-32 w-20 opacity-20 dna-helix" />
        <p className="text-xs uppercase text-cyan-200/70">NEXRYN Cognitive DNA</p>
        <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-white">Constitutional Cognitive Genetics & Long-Term Stability Traits</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Long-term trait architecture for truth, restraint, cooperation,
              identity continuity, and invariant protection.
            </p>
          </div>
          <div className="rounded-lg border border-cyan-300/25 bg-cyan-300/10 px-3 py-2 font-mono text-xs text-cyan-100">
            DNA_TRAITS_LOCKED
          </div>
        </div>
      </section>

      <DNAHealthSummary />
      <DNAProtectionGate />

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          {dnaTraits.map((trait) => (
            <DNATraitCard
              key={trait.id}
              trait={trait}
              selected={trait.id === selectedTrait.id}
              onSelect={setSelectedTrait}
            />
          ))}
        </div>

        <TraitDetailPanel trait={selectedTrait} />
      </section>
    </main>
  );
}
