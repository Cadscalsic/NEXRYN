import { LockKeyhole, ShieldCheck } from "lucide-react";

const protectionRules = [
  "Core traits cannot be deleted",
  "Trait mutation requires governance approval",
  "Truth priority cannot be overridden",
  "Anti-domination cannot be disabled",
  "Identity continuity must remain protected",
];

export function DNAProtectionGate() {
  return (
    <section className="relative overflow-hidden rounded-lg border border-violet-300/20 bg-violet-300/[0.055] p-5 shadow-runtime backdrop-blur-xl">
      <div className="absolute right-6 top-4 h-28 w-16 opacity-20 dna-helix" />
      <div className="flex items-start gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-lg border border-violet-300/25 bg-violet-300/10 text-violet-100">
          <LockKeyhole className="h-4 w-4" />
        </div>
        <div>
          <p className="text-xs uppercase text-violet-200/75">DNA Constitutional Protection</p>
          <h3 className="mt-1 text-xl font-semibold text-white">Protected cognitive genetics</h3>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {protectionRules.map((rule) => (
          <div key={rule} className="flex items-center gap-2 rounded-lg border border-white/10 bg-graphite-950/50 p-3">
            <ShieldCheck className="h-4 w-4 shrink-0 text-cyan-200" />
            <span className="text-sm leading-5 text-slate-300">{rule}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
