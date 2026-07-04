import { useMemo, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SearchBar from "@/components/SearchBar";
import FilterBar from "@/components/FilterBar";
import DataTable from "@/components/DataTable";
import StatusBadge from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { getLeadStages } from "@/services/stageProvider";
import { Plus, Zap, Target } from "lucide-react";

const FILTER_TABS = [
  { label: "All", value: "all" },
  { label: "Active", value: "Active" },
  { label: "Draft", value: "Draft" },
  { label: "Paused", value: "Paused" },
];

export default function JourneyList({ journeys, search, onSearchChange, filter, onFilterChange, onCreate }) {
  const navigate = useNavigate();
  const [stageLabels, setStageLabels] = useState({});

  useEffect(() => {
    getLeadStages().then((stages) => {
      const map = {};
      stages.forEach((s) => { map[s.value] = s.label; });
      setStageLabels(map);
    });
  }, []);

  const rows = useMemo(() => {
    return journeys.filter((j) => {
      if (filter !== "all" && j.status !== filter) return false;
      if (search && !j.name.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [journeys, filter, search]);

  const filterOptions = FILTER_TABS.map((f) => ({
    ...f,
    count: f.value === "all" ? journeys.length : journeys.filter((j) => j.status === f.value).length,
  }));

  const columns = [
    {
      key: "name",
      label: "Journey Name",
      render: (r) => (
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold">{r.name}</span>
        </div>
      ),
    },
    { key: "status", label: "Status", render: (r) => <StatusBadge status={r.status} /> },
    {
      key: "trigger",
      label: "Trigger",
      render: (r) => {
        const mapping = r.stageMappings?.[0];
        if (!mapping) {
          return <span className="text-xs text-muted-foreground">Not configured</span>;
        }
        const label = stageLabels[mapping.stage_key] || mapping.stage_key;
        return (
          <span className="inline-flex items-center gap-1 text-xs text-foreground">
            <Target className="h-3 w-3 text-primary" />
            {label}
          </span>
        );
      },
    },
    {
      key: "running",
      label: "Running",
      render: (r) => <span className="font-mono text-xs font-semibold">{r.runningCount || 0}</span>,
    },
    {
      key: "health",
      label: "Health",
      render: (r) => {
        if (!r.health) return <span className="text-xs text-muted-foreground">—</span>;
        const tone = r.health >= 90 ? "success" : r.health >= 70 ? "warning" : "danger";
        return <StatusBadge status={tone === "success" ? "Active" : tone === "warning" ? "Open" : "Lost"} tone={tone} />;
      },
    },
  ];

  return (
    <div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <SearchBar
          value={search}
          onChange={onSearchChange}
          placeholder="Search journeys…"
          className="w-full sm:max-w-sm"
          testId="journeys-search"
        />
        <div className="flex items-center gap-2">
          <FilterBar options={filterOptions} value={filter} onChange={onFilterChange} testId="journeys-filter" />
          <Button size="sm" onClick={onCreate} data-testid="journey-create">
            <Plus className="mr-2 h-3.5 w-3.5" /> Create Journey
          </Button>
        </div>
      </div>

      <div className="mt-4">
        <DataTable
          columns={columns}
          rows={rows}
          onRowClick={(row) => navigate(`/journeys/${row.id}`)}
          testId="journeys-table"
        />
      </div>
    </div>
  );
}
