import { cognitiveDNA } from "../data/mockNexrynRuntime";
import { RiskIndicator } from "./RiskIndicator";
import type { Tone } from "../data/mockNexrynRuntime";

const summaryItems: Array<{
  label: string;
  value: number;
  tone: Tone;
}> = [
  { label: "DNA Stability", value: cognitiveDNA.dnaStability, tone: "cyan" },
  { label: "Trait Integrity", value: cognitiveDNA.traitIntegrity, tone: "mint" },
  { label: "Mutation Pressure", value: cognitiveDNA.mutationPressure, tone: "amber" },
  { label: "Invariant Protection Level", value: cognitiveDNA.invariantProtection, tone: "violet" },
  { label: "Cooperation Bias", value: cognitiveDNA.cooperationBias, tone: "mint" },
  { label: "Curiosity Balance", value: cognitiveDNA.curiosityBalance, tone: "cyan" },
  { label: "Anti-Domination Strength", value: cognitiveDNA.antiDominationStrength, tone: "violet" },
];

export function DNAHealthSummary() {
  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {summaryItems.map((item) => (
        <article key={item.label} className="rounded-lg border border-white/10 bg-white/[0.045] p-4 shadow-runtime backdrop-blur-xl">
          <p className="text-xs text-slate-400">{item.label}</p>
          <p className="mt-2 font-mono text-xl font-semibold text-white">{item.value.toFixed(2)}</p>
          <div className="mt-4">
            <RiskIndicator value={item.value} tone={item.tone} />
          </div>
        </article>
      ))}
    </section>
  );
}
