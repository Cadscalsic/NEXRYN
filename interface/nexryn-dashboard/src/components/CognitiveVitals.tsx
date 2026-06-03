import { cognitiveVitals } from "../data/mockNexrynRuntime";

export function CognitiveVitals() {
  return (
    <aside className="rounded-lg border border-white/10 bg-white/[0.045] p-5 shadow-runtime backdrop-blur-xl xl:sticky xl:top-4">
      <div className="mb-5">
        <p className="text-xs uppercase text-cyan-200/70">Cognitive Vitals</p>
        <h3 className="mt-1 text-lg font-semibold text-white">Live mock state</h3>
      </div>

      <div className="space-y-5">
        {cognitiveVitals.map((vital) => (
          <div key={vital.label}>
            <div className="mb-2 flex items-center justify-between gap-4">
              <span className="text-sm text-slate-300">{vital.label}</span>
              <span className="font-mono text-sm text-white">{vital.value}</span>
            </div>
            <div className="h-1.5 rounded-full bg-slate-800">
              <div
                className="h-1.5 rounded-full bg-cyan-300"
                style={{ width: `${Math.round(vital.meter * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 rounded-lg border border-white/10 bg-graphite-950/60 p-4">
        <p className="text-xs text-slate-400">Constitutional mode</p>
        <p className="mt-2 text-sm font-medium text-white">Stabilization-first governance</p>
      </div>
    </aside>
  );
}
