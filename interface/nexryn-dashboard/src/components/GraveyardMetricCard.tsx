import type { Tone } from "../data/mockNexrynRuntime";
import { RiskIndicator } from "./RiskIndicator";

type Props = {
  label: string;
  value: string;
  detail: string;
  meter: number;
  tone: Tone;
};

export function GraveyardMetricCard({ label, value, detail, meter, tone }: Props) {
  return (
    <article className="rounded-lg border border-white/10 bg-white/[0.045] p-4 shadow-runtime backdrop-blur-xl">
      <p className="text-xs text-slate-400">{label}</p>
      <h3 className="mt-2 font-mono text-xl font-semibold text-white">{value}</h3>
      <p className="mt-3 min-h-10 text-sm leading-5 text-slate-400">{detail}</p>
      <div className="mt-4">
        <RiskIndicator value={meter} tone={tone} />
      </div>
    </article>
  );
}
