import { evolutionaryTraumaGroups } from "../data/mockNexrynRuntime";
import type { Tone } from "../data/mockNexrynRuntime";

const toneClass: Record<Tone, string> = {
  cyan: "border-cyan-300/20 bg-cyan-300/10 text-cyan-100",
  mint: "border-emerald-300/20 bg-emerald-300/10 text-emerald-100",
  violet: "border-violet-300/20 bg-violet-300/10 text-violet-100",
  amber: "border-amber-300/20 bg-amber-300/10 text-amber-100",
};

export function EvolutionaryTraumaMap() {
  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.045] p-5 shadow-runtime backdrop-blur-xl">
      <p className="text-xs uppercase text-cyan-200/70">Evolutionary Trauma Map</p>
      <h3 className="mt-1 text-xl font-semibold text-white">Debris groups retained for learning</h3>

      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {evolutionaryTraumaGroups.map((group) => (
          <article key={group.label} className="rounded-lg border border-white/10 bg-graphite-950/50 p-4">
            <h4 className="text-sm font-semibold text-white">{group.label}</h4>
            <div className="mt-3 flex flex-wrap gap-2">
              {group.items.map((item) => (
                <span key={item} className={`rounded border px-2 py-1 text-xs ${toneClass[group.tone]}`}>
                  {item}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
