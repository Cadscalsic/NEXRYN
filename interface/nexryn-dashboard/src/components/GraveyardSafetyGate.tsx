import { ArchiveRestore, ShieldCheck } from "lucide-react";

const safetyRules = [
  "Extinct traits are not deleted permanently",
  "Graveyard items are archived for learning",
  "Recovery requires physician recommendation",
  "Resurrection requires governance approval",
  "Failed lineages cannot auto-promote",
  "Unsafe merges remain blocked",
];

export function GraveyardSafetyGate() {
  return (
    <section className="rounded-lg border border-amber-300/20 bg-amber-300/[0.055] p-5 shadow-runtime backdrop-blur-xl">
      <div className="flex items-start gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-lg border border-amber-300/25 bg-amber-300/10 text-amber-100">
          <ArchiveRestore className="h-4 w-4" />
        </div>
        <div>
          <p className="text-xs uppercase text-amber-200/75">Graveyard Constitutional Safety</p>
          <h3 className="mt-1 text-xl font-semibold text-white">Evolutionary memory, not automatic resurrection</h3>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {safetyRules.map((rule) => (
          <div key={rule} className="flex items-center gap-2 rounded-lg border border-white/10 bg-graphite-950/50 p-3">
            <ShieldCheck className="h-4 w-4 shrink-0 text-cyan-200" />
            <span className="text-sm leading-5 text-slate-300">{rule}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
