import type { ProtocolStatus, RiskLevel } from "../data/mockNexrynRuntime";

type Props = {
  label: string;
  value: ProtocolStatus | RiskLevel | string;
};

const valueClass: Record<string, string> = {
  Available: "border-cyan-300/30 bg-cyan-300/10 text-cyan-100",
  Recommended: "border-emerald-300/30 bg-emerald-300/10 text-emerald-100",
  Locked: "border-slate-500/30 bg-slate-500/10 text-slate-300",
  Standby: "border-violet-300/30 bg-violet-300/10 text-violet-100",
  Low: "border-emerald-300/30 bg-emerald-300/10 text-emerald-100",
  Medium: "border-amber-300/30 bg-amber-300/10 text-amber-100",
  High: "border-red-300/30 bg-red-300/10 text-red-100",
  Required: "border-cyan-300/30 bg-cyan-300/10 text-cyan-100",
};

export function ProtocolRiskBadge({ label, value }: Props) {
  return (
    <div className="rounded-lg border border-white/10 bg-graphite-950/45 p-3">
      <p className="text-[11px] text-slate-500">{label}</p>
      <span className={`mt-2 inline-flex rounded border px-2 py-1 text-xs font-medium ${valueClass[value] ?? valueClass.Standby}`}>
        {value}
      </span>
    </div>
  );
}
