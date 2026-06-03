import { pharmacyProtocols, protocolSimulationMode } from "../data/mockNexrynRuntime";
import { ConstitutionalSafetyGate } from "./ConstitutionalSafetyGate";
import { PhysicianRecommendation } from "./PhysicianRecommendation";
import { ProtocolCard } from "./ProtocolCard";

export function PharmacyPage() {
  return (
    <main className="space-y-4 p-4">
      <section className="rounded-lg border border-white/10 bg-white/[0.035] p-5 shadow-runtime backdrop-blur-xl">
        <p className="text-xs uppercase text-cyan-200/70">NEXRYN Cognitive Pharmacy</p>
        <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-white">Constitutional Cognitive Regulation Protocols</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Simulated cognitive regulation protocols for runtime stabilization,
              semantic hygiene, identity continuity, and governed recovery.
            </p>
          </div>
          <div className="rounded-lg border border-cyan-300/25 bg-cyan-300/10 px-3 py-2 font-mono text-xs text-cyan-100">
            {protocolSimulationMode ? "SIMULATION_ONLY" : "LIVE_MODE_BLOCKED"}
          </div>
        </div>
      </section>

      <PhysicianRecommendation />
      <ConstitutionalSafetyGate />

      <section className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-4">
        {pharmacyProtocols.map((protocol) => (
          <ProtocolCard key={protocol.id} protocol={protocol} />
        ))}
      </section>
    </main>
  );
}
