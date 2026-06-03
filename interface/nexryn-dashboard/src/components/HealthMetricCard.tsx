import type { HealthMetric } from "../data/mockNexrynRuntime";
import { RiskIndicator } from "./RiskIndicator";

const iconClass = {
  cyan: "border-cyan-300/25 bg-cyan-300/10 text-cyan-200",
  mint: "border-emerald-300/25 bg-emerald-300/10 text-emerald-200",
  violet: "border-violet-300/25 bg-violet-300/10 text-violet-200",
  amber: "border-amber-300/25 bg-amber-300/10 text-amber-200",
};

type Props = {
  metric: HealthMetric;
};

export function HealthMetricCard({ metric }: Props) {
  const Icon = metric.icon;

  return (
    <article className="rounded-lg border border-white/10 bg-white/[0.045] p-4 shadow-runtime backdrop-blur-xl">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs text-slate-400">{metric.label}</p>
          <h3 className="mt-2 text-xl font-semibold text-white">{metric.value}</h3>
        </div>
        <div className={`grid h-9 w-9 place-items-center rounded-lg border ${iconClass[metric.tone]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <p className="mt-3 min-h-10 text-sm leading-5 text-slate-400">{metric.detail}</p>
      <div className="mt-4">
        <RiskIndicator value={metric.meter} tone={metric.tone} />
      </div>
    </article>
  );
}
