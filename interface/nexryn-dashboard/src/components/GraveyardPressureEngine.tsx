import { graveyard, pressureFactors } from "../data/mockNexrynRuntime";
import { RiskIndicator } from "./RiskIndicator";

const factors = [
  ["Failed merge pressure", pressureFactors.failedMergePressure],
  ["Extinct trait pressure", pressureFactors.extinctTraitPressure],
  ["Ontology damage pressure", pressureFactors.ontologyDamagePressure],
  ["Entropy pruning pressure", pressureFactors.entropyPruningPressure],
  ["Unstable lineage pressure", pressureFactors.unstableLineagePressure],
  ["Recovery debt", pressureFactors.recoveryDebt],
] as const;

function riskLevel(score: number) {
  if (score >= 0.75) return "Critical";
  if (score >= 0.5) return "Elevated";
  if (score >= 0.25) return "Watched";
  return "Low";
}

export function GraveyardPressureEngine() {
  return (
    <section className="rounded-lg border border-violet-300/20 bg-violet-300/[0.055] p-5 shadow-runtime backdrop-blur-xl">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase text-violet-200/75">Graveyard Pressure Engine</p>
          <h3 className="mt-1 text-xl font-semibold text-white">Evolutionary pressure calculation</h3>
        </div>
        <div className="rounded-lg border border-cyan-300/25 bg-cyan-300/10 px-3 py-2 text-right">
          <p className="text-[11px] text-slate-400">Final Score</p>
          <p className="font-mono text-lg text-cyan-100">{graveyard.graveyardPressure.toFixed(2)}</p>
          <p className="text-xs text-slate-400">{riskLevel(graveyard.graveyardPressure)}</p>
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {factors.map(([label, value]) => (
          <div key={label} className="rounded-lg border border-white/10 bg-graphite-950/50 p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <span className="text-sm text-slate-300">{label}</span>
              <span className="font-mono text-sm text-white">{value.toFixed(2)}</span>
            </div>
            <RiskIndicator value={value} tone="violet" />
          </div>
        ))}
      </div>
    </section>
  );
}
