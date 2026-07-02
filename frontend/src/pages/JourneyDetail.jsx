import { useParams, Navigate, useLocation } from "react-router-dom";
import { useState } from "react";
import PageHeader from "@/components/PageHeader";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { JourneyDashboard, RunningInstances, JourneySettings, FlowBuilder } from "@/modules/journeys";
import { JOURNEY_LIST, STAGE_MAPPINGS } from "@/dummy-data/journeys";

const SECTIONS = [
  { key: "dashboard", label: "Dashboard" },
  { key: "flow", label: "Flow" },
  { key: "running", label: "Running" },
  { key: "settings", label: "Settings" },
];

export default function JourneyDetail() {
  const { id } = useParams();
  const location = useLocation();
  const section = location.pathname.split("/").pop() || "dashboard";

  const journey = JOURNEY_LIST.find((j) => j.id === id);
  const mappings = STAGE_MAPPINGS.filter((sm) => sm.journeyId === id);

  if (!journey) {
    return <Navigate to="/journeys" replace />;
  }

  const handleTabChange = (value) => {
    window.history.pushState(null, "", `/journeys/${id}/${value}`);
  };

  return (
    <div data-testid="page-journey-detail" className="flex h-full min-h-0 flex-col">
      <PageHeader
        title={journey.name}
        description={`Status: ${journey.status} · ${mappings.length} stage mapping${mappings.length !== 1 ? "s" : ""}`}
      />

      <div className="border-b border-border px-4 md:px-8">
        <Tabs value={section} onValueChange={handleTabChange}>
          <TabsList>
            {SECTIONS.map((s) => (
              <TabsTrigger key={s.key} value={s.key} className="text-xs">
                {s.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-6 md:px-8">
        {section === "dashboard" && <JourneyDashboard journey={journey} />}
        {section === "flow" && <FlowBuilder journeyId={id} journeyName={journey.name} />}
        {section === "running" && <RunningInstances />}
        {section === "settings" && <JourneySettings journey={journey} mappings={mappings} />}
      </div>
    </div>
  );
}
