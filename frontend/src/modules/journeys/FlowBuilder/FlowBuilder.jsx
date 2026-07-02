import { useState } from "react";
import FlowCanvas from "./FlowCanvas";
import NodePalette from "./NodePalette";
import PropertiesPanel from "./PropertiesPanel";
import FlowToolbar from "./FlowToolbar";
import { useFlowBuilder } from "../hooks/useFlowBuilder";

export default function FlowBuilder({ journeyId, journeyName }) {
  const { flow, loading, saving, save } = useFlowBuilder(journeyId);
  const [selectedId, setSelectedId] = useState(null);

  const selectedNode = flow?.nodes?.find((n) => n.id === selectedId) || null;

  const handleSave = () => {
    if (flow) save(flow);
  };

  const handleValidate = () => {
    // TODO: implement validation
  };

  const handlePublish = () => {
    // TODO: implement publish
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Loading flow builder…
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <FlowToolbar
        journeyName={journeyName}
        onSave={handleSave}
        onValidate={handleValidate}
        onPublish={handlePublish}
        saving={saving}
      />
      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[200px_1fr_280px]">
        <NodePalette />
        <FlowCanvas flow={flow} onSave={save} />
        <PropertiesPanel selectedNode={selectedNode} />
      </div>
    </div>
  );
}
