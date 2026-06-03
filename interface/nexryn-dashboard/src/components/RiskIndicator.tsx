import type { Tone } from "../data/mockNexrynRuntime";

const fillClass: Record<Tone, string> = {
  cyan: "bg-cyan-300",
  mint: "bg-emerald-300",
  violet: "bg-violet-300",
  amber: "bg-amber-300",
};

type Props = {
  value: number;
  tone: Tone;
};

export function RiskIndicator({ value, tone }: Props) {
  const normalized = Math.max(0, Math.min(value, 1));

  return (
    <div className="h-1.5 rounded-full bg-slate-800">
      <div
        className={`h-1.5 rounded-full ${fillClass[tone]}`}
        style={{ width: `${Math.round(normalized * 100)}%` }}
      />
    </div>
  );
}
