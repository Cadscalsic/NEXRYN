import { physicianRecommendedProtocol } from "../data/mockNexrynRuntime";

export function PhysicianRecommendation() {
  return (
    <section className="rounded-lg border border-cyan-300/20 bg-cyan-300/[0.06] p-5 shadow-runtime backdrop-blur-xl">
      <p className="text-xs uppercase text-cyan-200/70">Physician Recommendation</p>
      <h3 className="mt-1 text-xl font-semibold text-white">Protocol guidance</h3>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <RecommendationField
          label="Current Diagnosis"
          value={physicianRecommendedProtocol.currentDiagnosis}
        />
        <RecommendationField
          label="Recommended Protocol"
          value={physicianRecommendedProtocol.recommendedProtocol}
        />
        <RecommendationField
          label="Suggested Action"
          value={physicianRecommendedProtocol.suggestedAction}
        />
      </div>
    </section>
  );
}

type RecommendationFieldProps = {
  label: string;
  value: string;
};

function RecommendationField({ label, value }: RecommendationFieldProps) {
  return (
    <div className="rounded-lg border border-white/10 bg-graphite-950/50 p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-medium leading-5 text-white">{value}</p>
    </div>
  );
}
