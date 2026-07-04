import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FlowBuilder } from "@/modules/journeys";
import { journeyService } from "@/services/journeys";
import { Plus } from "lucide-react";

export default function Automation() {
  const navigate = useNavigate();
  const [journeys, setJourneys] = useState([]);
  const [selectedJourneyId, setSelectedJourneyId] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    journeyService
      .list()
      .then((data) => {
        setJourneys(data);
        if (data.length > 0) setSelectedJourneyId(data[0].id);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const selectedJourney = journeys.find((j) => j.id === selectedJourneyId);

  return (
    <div data-testid="page-automation" className="flex h-full min-h-0 flex-col">
      <PageHeader
        title="Automation"
        description="Visual customer journey builder"
        actions={
          <div className="flex items-center gap-2">
            <Select
              value={selectedJourneyId || ""}
              onValueChange={setSelectedJourneyId}
            >
              <SelectTrigger className="h-9 w-[240px]">
                <SelectValue placeholder="Select a journey..." />
              </SelectTrigger>
              <SelectContent>
                {journeys.map((j) => (
                  <SelectItem key={j.id} value={j.id}>
                    {j.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button size="sm" onClick={() => navigate("/journeys")}>
              <Plus className="mr-1.5 h-3.5 w-3.5" /> New Journey
            </Button>
          </div>
        }
      />
      <div className="flex-1 min-h-0">
        {loading ? (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            Loading...
          </div>
        ) : !selectedJourneyId ? (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            No journeys available. Create one to start building.
          </div>
        ) : (
          <FlowBuilder
            journeyId={selectedJourneyId}
            journeyName={selectedJourney?.name}
          />
        )}
      </div>
    </div>
  );
}
