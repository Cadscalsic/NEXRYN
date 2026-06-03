import { cognitiveHealthMetrics } from "../data/mockNexrynRuntime";
import { HealthMetricCard } from "./HealthMetricCard";
import { PhysicianPanel } from "./PhysicianPanel";

export function CognitiveHealthPage() {
  return (
    <main className="space-y-4 p-4">
      <section className="rounded-lg border border-white/10 bg-white/[0.035] p-5 shadow-runtime backdrop-blur-xl">
        <p className="text-xs uppercase text-cyan-200/70">Cognitive Health</p>
        <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-white">Runtime health monitoring</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Health telemetry for stabilization mode, identity integrity, pressure, drift,
              and recovery posture.
            </p>
          </div>
          <div className="rounded-lg border border-emerald-300/25 bg-emerald-300/10 px-3 py-2 font-mono text-xs text-emerald-100">
            PHYSICIAN_PANEL_V1
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cognitiveHealthMetrics.map((metric) => (
          <HealthMetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      <PhysicianPanel />
    </main>
  );
}
