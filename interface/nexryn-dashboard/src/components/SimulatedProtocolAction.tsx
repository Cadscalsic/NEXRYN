type Props = {
  label: string;
  disabled?: boolean;
};

export function SimulatedProtocolAction({ label, disabled = false }: Props) {
  return (
    <button
      className={[
        "h-9 rounded-lg border px-3 text-xs font-medium transition",
        disabled
          ? "cursor-not-allowed border-slate-600/50 bg-slate-700/20 text-slate-500"
          : "border-cyan-300/25 bg-cyan-300/10 text-cyan-100 hover:bg-cyan-300/15",
      ].join(" ")}
      type="button"
      disabled={disabled}
      title="Simulation Only"
      onClick={() => {
        window.alert("Simulation Only: no runtime mutation was applied.");
      }}
    >
      {label}
    </button>
  );
}
