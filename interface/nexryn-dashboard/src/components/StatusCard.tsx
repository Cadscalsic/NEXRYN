import type { StatusCardData } from "../data/mockNexrynRuntime";

const barClass = {
  cyan: "bg-cyan-300",
  mint: "bg-emerald-300",
  violet: "bg-violet-300",
  amber: "bg-amber-300",
};

const iconClass = {
  cyan: "text-cyan-200 bg-cyan-300/10 border-cyan-300/25",
  mint: "text-emerald-200 bg-emerald-300/10 border-emerald-300/25",
  violet: "text-violet-200 bg-violet-300/10 border-violet-300/25",
  amber: "text-amber-200 bg-amber-300/10 border-amber-300/25",
};

type Props = {
  card: StatusCardData;
};

export function StatusCard({ card }: Props) {
  const Icon = card.icon;

  return (
    <article className="rounded-lg border border-white/10 bg-white/[0.045] p-4 shadow-runtime backdrop-blur-xl">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs text-slate-400">{card.label}</p>
          <h3 className="mt-2 text-xl font-semibold text-white">{card.value}</h3>
        </div>
        <div className={`grid h-9 w-9 place-items-center rounded-lg border ${iconClass[card.tone]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <p className="mt-3 min-h-10 text-sm leading-5 text-slate-400">{card.detail}</p>
      <div className="mt-4 h-1.5 rounded-full bg-slate-800">
        <div
          className={`h-1.5 rounded-full ${barClass[card.tone]}`}
          style={{ width: `${Math.round(card.metric * 100)}%` }}
        />
      </div>
    </article>
  );
}
