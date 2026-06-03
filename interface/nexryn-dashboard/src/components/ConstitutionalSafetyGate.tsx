import { CheckCircle2, ShieldAlert } from "lucide-react";

const safetyRules = [
  "Physician diagnosis required",
  "Governance kernel approval required",
  "Direct runtime mutation blocked",
  "Temporary intervention only",
  "Dependency prevention active",
];

type Props = {
  title?: string;
  subtitle?: string;
  eyebrow?: string;
  rules?: string[];
};

export function ConstitutionalSafetyGate({
  title = "Simulation-only regulation",
  subtitle = "Constitutional Safety Gate",
  eyebrow = "Constitutional Safety Gate",
  rules = safetyRules,
}: Props) {
  return (
    <section className="rounded-lg border border-violet-300/20 bg-violet-300/[0.055] p-5 shadow-runtime backdrop-blur-xl">
      <div className="flex items-start gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-lg border border-violet-300/25 bg-violet-300/10 text-violet-100">
          <ShieldAlert className="h-4 w-4" />
        </div>
        <div>
          <p className="text-xs uppercase text-violet-200/75">{eyebrow}</p>
          <h3 className="mt-1 text-xl font-semibold text-white">{title}</h3>
          {subtitle && <p className="mt-2 text-sm text-slate-400">{subtitle}</p>}
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {safetyRules.map((rule) => (
          <div key={rule} className="flex items-center gap-2 rounded-lg border border-white/10 bg-graphite-950/50 p-3">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-cyan-200" />
            <span className="text-sm leading-5 text-slate-300">{rule}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
