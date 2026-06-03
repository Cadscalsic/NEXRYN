import { graveyardItems } from "../data/mockNexrynRuntime";

export function ExtinctionTable() {
  return (
    <section className="overflow-hidden rounded-lg border border-white/10 bg-white/[0.045] shadow-runtime backdrop-blur-xl">
      <div className="border-b border-white/10 p-5">
        <p className="text-xs uppercase text-cyan-200/70">Extinction Memory</p>
        <h3 className="mt-1 text-xl font-semibold text-white">Archived traits and rejected lineages</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-[980px] w-full text-left text-sm">
          <thead className="bg-graphite-950/70 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Trait / Strategy</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Reason</th>
              <th className="px-4 py-3">Net Fitness</th>
              <th className="px-4 py-3">Stability Score</th>
              <th className="px-4 py-3">Last Seen</th>
              <th className="px-4 py-3">Recovery Potential</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {graveyardItems.map((item) => (
              <tr key={item.id} className="text-slate-300">
                <td className="px-4 py-4 font-mono text-xs text-cyan-100">{item.name}</td>
                <td className="px-4 py-4">{item.type}</td>
                <td className="px-4 py-4 text-slate-400">{item.reason}</td>
                <td className="px-4 py-4 font-mono">{item.netFitness.toFixed(2)}</td>
                <td className="px-4 py-4 font-mono">{item.stabilityScore.toFixed(2)}</td>
                <td className="px-4 py-4">{item.lastSeen}</td>
                <td className="px-4 py-4">{item.recoveryPotential}</td>
                <td className="px-4 py-4">{item.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
