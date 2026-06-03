import type { DNATrait } from "../data/mockNexrynRuntime";
import { RiskIndicator } from "./RiskIndicator";
import { TraitStatusBadge } from "./TraitStatusBadge";

type Props = {
  trait: DNATrait;
  selected: boolean;
  onSelect: (trait: DNATrait) => void;
};

export function DNATraitCard({ trait, selected, onSelect }: Props) {
  return (
    <button
      className={[
        "rounded-lg border p-4 text-left shadow-runtime backdrop-blur-xl transition",
        selected
          ? "border-cyan-300/45 bg-cyan-300/[0.075] shadow-cyan-soft"
          : "border-white/10 bg-white/[0.045] hover:border-cyan-300/25 hover:bg-white/[0.065]",
      ].join(" ")}
      type="button"
      onClick={() => onSelect(trait)}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs text-cyan-200/70">Constitutional Trait</p>
          <h3 className="mt-2 text-lg font-semibold text-white">{trait.name}</h3>
        </div>
        <TraitStatusBadge status={trait.status} />
      </div>

      <p className="mt-3 min-h-12 text-sm leading-5 text-slate-400">{trait.constitutionalRole}</p>

      <div className="mt-4 space-y-3">
        <TraitMeter label="Stability Score" value={trait.stabilityScore} tone={trait.tone} />
        <TraitMeter label="Inheritance Strength" value={trait.inheritanceStrength} tone="mint" />
        <TraitMeter label="Mutation Resistance" value={trait.mutationResistance} tone="violet" />
        <TraitMeter label="Adaptive Weight" value={trait.adaptiveWeight} tone="cyan" />
      </div>

      <div className="mt-4 rounded-lg border border-white/10 bg-graphite-950/50 p-3">
        <p className="text-[11px] text-slate-500">Risk if weakened</p>
        <p className="mt-1 text-xs leading-5 text-slate-300">{trait.riskIfWeakened}</p>
      </div>
    </button>
  );
}

type TraitMeterProps = {
  label: string;
  value: number;
  tone: DNATrait["tone"];
};

function TraitMeter({ label, value, tone }: TraitMeterProps) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between gap-3">
        <span className="text-xs text-slate-500">{label}</span>
        <span className="font-mono text-xs text-slate-200">{value.toFixed(2)}</span>
      </div>
      <RiskIndicator value={value} tone={tone} />
    </div>
  );
}
