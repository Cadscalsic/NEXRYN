import type { PharmacyProtocol } from "../data/mockNexrynRuntime";
import { ProtocolRiskBadge } from "./ProtocolRiskBadge";
import { SimulatedProtocolAction } from "./SimulatedProtocolAction";

const iconClass = {
  cyan: "border-cyan-300/25 bg-cyan-300/10 text-cyan-200",
  mint: "border-emerald-300/25 bg-emerald-300/10 text-emerald-200",
  violet: "border-violet-300/25 bg-violet-300/10 text-violet-200",
  amber: "border-amber-300/25 bg-amber-300/10 text-amber-200",
};

type Props = {
  protocol: PharmacyProtocol;
};

export function ProtocolCard({ protocol }: Props) {
  const Icon = protocol.icon;
  const isLocked = protocol.status === "Locked";

  return (
    <article className="rounded-lg border border-white/10 bg-white/[0.045] p-5 shadow-runtime backdrop-blur-xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs text-cyan-200/70">{protocol.category}</p>
          <h3 className="mt-2 text-lg font-semibold text-white">{protocol.name}</h3>
        </div>
        <div className={`grid h-10 w-10 place-items-center rounded-lg border ${iconClass[protocol.tone]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <p className="mt-4 min-h-16 text-sm leading-6 text-slate-400">{protocol.purpose}</p>

      <div className="mt-5 grid grid-cols-2 gap-2">
        <ProtocolRiskBadge label="Status" value={protocol.status} />
        <ProtocolRiskBadge label="Intensity" value={protocol.intensity} />
        <ProtocolRiskBadge
          label="Constitutional Approval"
          value={protocol.constitutionalApprovalRequired ? "Required" : "Not Required"}
        />
        <ProtocolRiskBadge label="Dependency Risk" value={protocol.dependencyRisk} />
        <ProtocolRiskBadge label="Side Effect Risk" value={protocol.sideEffectRisk} />
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        <SimulatedProtocolAction label="Request Protocol" disabled={isLocked} />
        <SimulatedProtocolAction label="Simulate Effect" disabled={isLocked} />
        <SimulatedProtocolAction label="View Safety Report" />
      </div>
    </article>
  );
}
