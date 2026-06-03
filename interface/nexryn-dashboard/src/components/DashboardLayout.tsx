import { useState } from "react";
import { CognitiveVitals } from "./CognitiveVitals";
import { CognitiveHealthPage } from "./CognitiveHealthPage";
import { DNAPage } from "./DNAPage";
import { GraveyardPage } from "./GraveyardPage";
import { PharmacyPage } from "./PharmacyPage";
import { SemanticMapPlaceholder } from "./SemanticMapPlaceholder";
import { Sidebar } from "./Sidebar";
import { StatusCard } from "./StatusCard";
import { TopBar } from "./TopBar";
import { statusCards } from "../data/mockNexrynRuntime";
import type { PageId } from "../data/mockNexrynRuntime";

export function DashboardLayout() {
  const [activePage, setActivePage] = useState<PageId>("overview");

  return (
    <div className="min-h-screen bg-graphite-950 text-slate-100">
      <div className="runtime-shell min-h-screen lg:flex">
        <Sidebar activePage={activePage} onNavigate={setActivePage} />

        <div className="min-w-0 flex-1">
          <TopBar />

          {activePage === "overview" && <OverviewPage />}
          {activePage === "cognitive-health" && <CognitiveHealthPage />}
          {activePage === "pharmacy" && <PharmacyPage />}
          {activePage === "dna" && <DNAPage />}
          {activePage === "graveyard" && <GraveyardPage />}
        </div>
      </div>
    </div>
  );
}

function OverviewPage() {
  return (
    <main className="grid gap-4 p-4 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div className="space-y-4">
        <section className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
          {statusCards.map((card) => (
            <StatusCard key={card.label} card={card} />
          ))}
        </section>

        <SemanticMapPlaceholder />
      </div>

      <CognitiveVitals />
    </main>
  );
}
