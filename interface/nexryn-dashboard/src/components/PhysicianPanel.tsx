import {
  diagnosisCategories,
  physicianDiagnosis,
} from "../data/mockNexrynRuntime";
import { DiagnosisBadge } from "./DiagnosisBadge";

export function PhysicianPanel() {
  const activeDiagnosis = diagnosisCategories.find((category) => category.active);

  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.045] p-5 shadow-runtime backdrop-blur-xl">
      <div className="flex flex-col gap-3 border-b border-white/10 pb-5 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase text-cyan-200/70">Physician Runtime</p>
          <h3 className="mt-1 text-xl font-semibold text-white">NEXRYN Cognitive Physician</h3>
        </div>
        {activeDiagnosis && (
          <DiagnosisBadge label={activeDiagnosis.label} tone={activeDiagnosis.tone} />
        )}
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <PhysicianField label="Diagnosis" value={physicianDiagnosis.diagnosis} />
        <PhysicianField label="Severity" value={physicianDiagnosis.severity} />
        <PhysicianField label="Recommendation" value={physicianDiagnosis.recommendation} wide />
        <PhysicianField
          label="Treatment Required"
          value={physicianDiagnosis.treatmentRequired ? "Yes" : "No"}
        />
        <PhysicianField
          label="Monitoring Required"
          value={physicianDiagnosis.monitoringRequired ? "Yes" : "No"}
        />
        <PhysicianField label="Risk Level" value={physicianDiagnosis.riskLevel} />
      </div>
    </section>
  );
}

type PhysicianFieldProps = {
  label: string;
  value: string;
  wide?: boolean;
};

function PhysicianField({ label, value, wide = false }: PhysicianFieldProps) {
  return (
    <div className={`rounded-lg border border-white/10 bg-graphite-950/55 p-4 ${wide ? "md:col-span-2 xl:col-span-1" : ""}`}>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-medium leading-5 text-white">{value}</p>
    </div>
  );
}
