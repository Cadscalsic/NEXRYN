import type { TraitStatus } from "../data/mockNexrynRuntime";

const statusClass: Record<TraitStatus, string> = {
  Core: "border-cyan-300/30 bg-cyan-300/10 text-cyan-100",
  Adaptive: "border-emerald-300/30 bg-emerald-300/10 text-emerald-100",
  Watched: "border-amber-300/30 bg-amber-300/10 text-amber-100",
};

type Props = {
  status: TraitStatus;
};

export function TraitStatusBadge({ status }: Props) {
  return (
    <span className={`inline-flex rounded border px-2 py-1 text-xs font-medium ${statusClass[status]}`}>
      {status}
    </span>
  );
}
