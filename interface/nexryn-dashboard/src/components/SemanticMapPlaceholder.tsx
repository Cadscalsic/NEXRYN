import { semanticNodes } from "../data/mockNexrynRuntime";

const nodeClass = {
  cyan: "border-cyan-300/50 bg-cyan-300/12 text-cyan-100 shadow-[0_0_24px_rgba(53,215,255,0.18)]",
  blue: "border-blue-300/50 bg-blue-300/12 text-blue-100 shadow-[0_0_24px_rgba(59,130,246,0.16)]",
  mint: "border-emerald-300/50 bg-emerald-300/12 text-emerald-100 shadow-[0_0_24px_rgba(86,240,189,0.16)]",
  violet: "border-violet-300/50 bg-violet-300/12 text-violet-100 shadow-[0_0_24px_rgba(139,92,246,0.16)]",
  amber: "border-amber-300/50 bg-amber-300/12 text-amber-100 shadow-[0_0_24px_rgba(244,201,93,0.14)]",
};

const connections = [
  "M 240 88 L 130 170",
  "M 240 88 L 338 172",
  "M 130 170 L 240 230",
  "M 338 172 L 240 230",
  "M 240 230 L 154 296",
  "M 240 230 L 332 296",
  "M 154 296 L 332 296",
];

export function SemanticMapPlaceholder() {
  return (
    <section className="min-h-[420px] rounded-lg border border-white/10 bg-white/[0.035] p-5 shadow-runtime backdrop-blur-xl">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase text-cyan-200/70">Semantic Cognitive Map</p>
          <h3 className="mt-1 text-lg font-semibold text-white">Constitutional topology</h3>
        </div>
        <div className="rounded-lg border border-cyan-300/20 bg-cyan-300/10 px-3 py-2 font-mono text-xs text-cyan-100">
          MAP_PLACEHOLDER_V1
        </div>
      </div>

      <div className="relative mx-auto mt-6 h-[330px] max-w-[480px] overflow-hidden rounded-lg border border-white/10 bg-graphite-950/70">
        <div className="absolute inset-0 semantic-grid" />
        <svg
          aria-hidden="true"
          className="absolute inset-0 h-full w-full"
          viewBox="0 0 480 330"
          preserveAspectRatio="none"
        >
          {connections.map((path) => (
            <path
              key={path}
              d={path}
              fill="none"
              stroke="rgba(53, 215, 255, 0.28)"
              strokeWidth="1.2"
            />
          ))}
        </svg>

        {semanticNodes.map((node) => (
          <div
            key={node.label}
            className={`absolute flex min-h-10 min-w-24 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-lg border px-3 text-center text-xs font-medium backdrop-blur-md ${nodeClass[node.tone]}`}
            style={{ left: `${node.x}%`, top: `${node.y}%` }}
          >
            {node.label}
          </div>
        ))}
      </div>
    </section>
  );
}
