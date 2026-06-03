import { graveyard } from "../data/mockNexrynRuntime";

const defaultRecommendations = [
  "Continue graveyard observation",
  "Preserve dormant invariant archive",
  "Keep recovery protocol on standby",
];

const highPressureRecommendations = [
  "Recommend Graveyard Pressure Relief",
  "Recommend Invariant Protection reinforcement",
  "Recommend Cognitive Sleep Cycle",
  "Recommend Ontology Detoxification",
];

export function RecoveryRecommendationPanel() {
  const recommendations =
    graveyard.graveyardPressure > 0.5
      ? highPressureRecommendations
      : defaultRecommendations;

  return (
    <section className="rounded-lg border border-cyan-300/20 bg-cyan-300/[0.06] p-5 shadow-runtime backdrop-blur-xl">
      <p className="text-xs uppercase text-cyan-200/70">Recovery Recommendation</p>
      <h3 className="mt-1 text-xl font-semibold text-white">Linked to Physician, Pharmacy, and DNA System</h3>

      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {recommendations.map((recommendation) => (
          <div key={recommendation} className="rounded-lg border border-white/10 bg-graphite-950/50 p-4">
            <p className="text-sm leading-6 text-slate-300">{recommendation}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
