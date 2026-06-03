import type { DNATrait } from "../data/mockNexrynRuntime";
import { TraitStatusBadge } from "./TraitStatusBadge";

type Props = {
  trait: DNATrait;
};

export function TraitDetailPanel({ trait }: Props) {
  return (
    <aside className="rounded-lg border border-white/10 bg-white/[0.045] p-5 shadow-runtime backdrop-blur-xl xl:sticky xl:top-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase text-cyan-200/70">Trait Detail Panel</p>
          <h3 className="mt-1 text-xl font-semibold text-white">{trait.name}</h3>
        </div>
        <TraitStatusBadge status={trait.status} />
      </div>

      <DetailSection title="Description" body={trait.description} />
      <DetailSection title="Why it matters" body={trait.whyItMatters} />
      <DetailList title="Protected behaviors" items={trait.protectedBehaviors} />
      <DetailList title="Failure risks" items={trait.failureRisks} />
      <DetailList title="Connected systems" items={trait.connectedSystems} />
      <DetailSection title="Suggested monitoring" body={trait.suggestedMonitoring} />
    </aside>
  );
}

type DetailSectionProps = {
  title: string;
  body: string;
};

function DetailSection({ title, body }: DetailSectionProps) {
  return (
    <div className="mt-5 rounded-lg border border-white/10 bg-graphite-950/50 p-4">
      <p className="text-xs text-slate-500">{title}</p>
      <p className="mt-2 text-sm leading-6 text-slate-300">{body}</p>
    </div>
  );
}

type DetailListProps = {
  title: string;
  items: string[];
};

function DetailList({ title, items }: DetailListProps) {
  return (
    <div className="mt-5 rounded-lg border border-white/10 bg-graphite-950/50 p-4">
      <p className="text-xs text-slate-500">{title}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item} className="rounded border border-cyan-300/20 bg-cyan-300/10 px-2 py-1 text-xs text-cyan-100">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
