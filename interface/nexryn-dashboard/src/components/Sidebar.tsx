import { navItems } from "../data/mockNexrynRuntime";
import type { PageId } from "../data/mockNexrynRuntime";

type Props = {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
};

export function Sidebar({ activePage, onNavigate }: Props) {
  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-white/10 bg-graphite-950/80 px-4 py-4 backdrop-blur-xl lg:min-h-screen lg:w-72 lg:border-b-0 lg:border-r">
      <div className="mb-5 flex items-center gap-3 px-2">
        <div className="grid h-10 w-10 place-items-center rounded-lg border border-cyan-300/30 bg-cyan-300/10 shadow-cyan-soft">
          <span className="font-mono text-sm font-semibold text-cyan-200">NX</span>
        </div>
        <div>
          <h1 className="text-xl font-semibold tracking-normal text-white">NEXRYN</h1>
          <p className="text-xs text-slate-400">Constitutional Cognitive Runtime</p>
        </div>
      </div>

      <nav className="flex gap-2 overflow-x-auto pb-1 lg:flex-col lg:overflow-visible">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.pageId === activePage;

          return (
            <button
              key={item.label}
              className={[
                "group flex h-11 min-w-max items-center gap-3 rounded-lg border px-3 text-sm transition",
                isActive
                  ? "border-cyan-300/40 bg-cyan-300/10 text-cyan-100 shadow-cyan-soft"
                  : item.enabled
                    ? "border-transparent text-slate-400 hover:border-white/10 hover:bg-white/[0.04] hover:text-slate-100"
                    : "cursor-not-allowed border-transparent text-slate-600",
              ].join(" ")}
              type="button"
              aria-current={isActive ? "page" : undefined}
              disabled={!item.enabled}
              title={item.enabled ? item.label : `${item.label} - coming soon`}
              onClick={() => {
                if (item.pageId) {
                  onNavigate(item.pageId);
                }
              }}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{item.label}</span>
              {!item.enabled && (
                <span className="ml-auto hidden rounded border border-white/10 px-1.5 py-0.5 text-[10px] text-slate-500 lg:inline">
                  Soon
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="mt-auto hidden rounded-lg border border-white/10 bg-white/[0.035] p-4 lg:block">
        <div className="mb-2 h-1.5 rounded-full bg-slate-800">
          <div className="h-1.5 w-[82%] rounded-full bg-cyan-300" />
        </div>
        <p className="text-xs text-slate-400">Constitutional integrity</p>
        <p className="mt-1 font-mono text-lg text-white">82%</p>
      </div>
    </aside>
  );
}
