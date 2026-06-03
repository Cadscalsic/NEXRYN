import type { Tone } from "../data/mockNexrynRuntime";

const badgeClass: Record<Tone, string> = {
  cyan: "border-cyan-300/30 bg-cyan-300/10 text-cyan-100",
  mint: "border-emerald-300/30 bg-emerald-300/10 text-emerald-100",
  violet: "border-violet-300/30 bg-violet-300/10 text-violet-100",
  amber: "border-amber-300/30 bg-amber-300/10 text-amber-100",
};

type Props = {
  label: string;
  tone: Tone;
};

export function DiagnosisBadge({ label, tone }: Props) {
  return (
    <span className={`inline-flex rounded-lg border px-3 py-1.5 text-sm font-medium ${badgeClass[tone]}`}>
      {label}
    </span>
  );
}
