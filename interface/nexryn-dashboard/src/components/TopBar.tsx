import { runtimeStatus } from "../data/mockNexrynRuntime";

const toneClass = {
  cyan: "text-cyan-200 bg-cyan-300/10 border-cyan-300/25",
  mint: "text-emerald-200 bg-emerald-300/10 border-emerald-300/25",
  violet: "text-violet-200 bg-violet-300/10 border-violet-300/25",
  amber: "text-amber-200 bg-amber-300/10 border-amber-300/25",
};

export function TopBar() {
  return (
    <header className="flex flex-col gap-3 border-b border-white/10 bg-graphite-900/72 px-4 py-4 backdrop-blur-xl xl:flex-row xl:items-center xl:justify-between">
      <div>
        <p className="text-xs uppercase text-cyan-200/70">Runtime overview</p>
        <h2 className="mt-1 text-xl font-semibold text-white sm:text-2xl">
          Constitutional Cognitive Runtime
        </h2>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {runtimeStatus.map((status) => (
          <div
            key={status.label}
            className={`rounded-lg border px-3 py-2 ${toneClass[status.tone]}`}
          >
            <p className="text-[11px] text-slate-400">{status.label}</p>
            <p className="mt-0.5 text-sm font-medium">{status.value}</p>
          </div>
        ))}
      </div>
    </header>
  );
}
