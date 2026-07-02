import { useState } from "react";
import PageHeader from "@/components/PageHeader";
import { JourneyList } from "@/modules/journeys";
import { JOURNEY_LIST, STAGE_MAPPINGS } from "@/dummy-data/journeys";

export default function Journeys() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const enriched = JOURNEY_LIST.map((j) => ({
    ...j,
    stageMappings: STAGE_MAPPINGS.filter((sm) => sm.journeyId === j.id),
    runningCount: Math.floor(Math.random() * 150),
    health: Math.floor(70 + Math.random() * 30),
  }));

  return (
    <div data-testid="page-journeys">
      <PageHeader
        title="Journeys"
        description="Manage your stage-to-flow mappings, flow builder, and running instances."
      />
      <div className="space-y-4 px-4 py-6 md:px-8">
        <JourneyList
          journeys={enriched}
          search={search}
          onSearchChange={setSearch}
          filter={filter}
          onFilterChange={setFilter}
          onCreate={() => {}}
        />
      </div>
    </div>
  );
}
