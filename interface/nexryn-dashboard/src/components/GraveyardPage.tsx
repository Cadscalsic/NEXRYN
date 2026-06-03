import { graveyard } from "../data/mockNexrynRuntime";
import { EvolutionaryTraumaMap } from "./EvolutionaryTraumaMap";
import { ExtinctionTable } from "./ExtinctionTable";
import { GraveyardMetricCard } from "./GraveyardMetricCard";
import { GraveyardPressureEngine } from "./GraveyardPressureEngine";
import { GraveyardSafetyGate } from "./GraveyardSafetyGate";
import { RecoveryRecommendationPanel } from "./RecoveryRecommendationPanel";

const metrics = [
  {
    label: "Graveyard Pressure",
    value: graveyard.graveyardPressure.toFixed(2),
    detail: "Active pressure from evolutionary debris",
    meter: graveyard.graveyardPressure,
    tone: "amber" as const,
  },
  {
    label: "Extinct Traits",
    value: String(graveyard.extinctTraits),
    detail: "Dormant or extinct cognitive traits",
    meter: graveyard.extinctTraits / 10,
    tone: "cyan" as const,
  },
  {
    label: "Rejected Merges",
    value: String(graveyard.rejectedMerges),
    detail: "Merge attempts blocked by governance",
    meter: graveyard.rejectedMerges / 12,
    tone: "violet" as const,
  },
  {
    label: "Failed Lineages",
    value: String(graveyard.failedLineages),
    detail: "Lineages retained for failure learning",
    meter: graveyard.failedLineages / 10,
    tone: "amber" as const,
  },
  {
    label: "Entropy-Pruned Strategies",
    value: String(graveyard.entropyPrunedStrategies),
    detail: "Strategies removed by entropy control",
    meter: graveyard.entropyPrunedStrategies / 10,
    tone: "violet" as const,
  },
  {
    label: "Ontology Damage",
    value: graveyard.ontologyDamage.toFixed(2),
    detail: "Structural semantic repair pressure",
    meter: graveyard.ontologyDamage,
    tone: "cyan" as const,
  },
  {
    label: "Recovery Actions",
    value: String(graveyard.recoveryActions),
    detail: "Available guided recovery paths",
    meter: graveyard.recoveryActions / 6,
    tone: "mint" as const,
  },
  {
    label: "Memory Scar Count",
    value: String(graveyard.memoryScarCount),
    detail: "Retained scars for evolutionary learning",
    meter: graveyard.memoryScarCount / 12,
    tone: "amber" as const,
  },
];

export function GraveyardPage() {
  return (
    <main className="space-y-4 p-4">
      <section className="rounded-lg border border-white/10 bg-white/[0.035] p-5 shadow-runtime backdrop-blur-xl">
        <p className="text-xs uppercase text-cyan-200/70">NEXRYN Cognitive Graveyard</p>
        <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-white">Evolutionary Debris, Extinction Memory & Graveyard Pressure</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Archived failures and extinct traits are preserved as evolutionary memory,
              pressure signals, and guarded recovery candidates.
            </p>
          </div>
          <div className="rounded-lg border border-amber-300/25 bg-amber-300/10 px-3 py-2 font-mono text-xs text-amber-100">
            AUTO_RESURRECTION_BLOCKED
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        {metrics.map((metric) => (
          <GraveyardMetricCard key={metric.label} {...metric} />
        ))}
      </section>

      <GraveyardPressureEngine />
      <EvolutionaryTraumaMap />
      <RecoveryRecommendationPanel />
      <ExtinctionTable />
      <GraveyardSafetyGate />
    </main>
  );
}
