import { useState, useEffect, useCallback, useMemo } from "react";
import { toast } from "sonner";
import {
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
} from "@xyflow/react";
import FlowCanvas from "./FlowCanvas";
import NodePalette from "./NodePalette";
import PropertiesPanel from "./PropertiesPanel";
import FlowToolbar from "./FlowToolbar";
import { useFlowBuilder } from "../hooks/useFlowBuilder";
import {
  TriggerNode,
  DelayNode,
  ConditionNode,
  SendWhatsAppNode,
  SendEmailNode,
  NotificationNode,
  WaitNode,
  EndNode,
  UpdateLeadNode,
  UpdateCompanyNode,
  AssignOwnerNode,
  ChangeLeadStageNode,
  CreateCRMTaskNode,
  CreateNoteNode,
  ApprovalNode,
  ManualTaskNode,
} from "./nodes";

const NODE_TYPES = {
  trigger: TriggerNode,
  delay: DelayNode,
  condition: ConditionNode,
  send_whatsapp: SendWhatsAppNode,
  send_email: SendEmailNode,
  notification: NotificationNode,
  wait: WaitNode,
  end: EndNode,
  update_lead: UpdateLeadNode,
  update_company: UpdateCompanyNode,
  assign_owner: AssignOwnerNode,
  change_lead_stage: ChangeLeadStageNode,
  create_crm_task: CreateCRMTaskNode,
  create_note: CreateNoteNode,
  approval: ApprovalNode,
  manual_task: ManualTaskNode,
};

function toRfNodes(apiNodes) {
  return (apiNodes || []).map((n) => {
    const x = Number(n.position?.x ?? n.x ?? 0);
    const y = Number(n.position?.y ?? n.y ?? 0);
    return {
      id: n.id ?? crypto.randomUUID(),
      type: n.type ?? "default",
      position: {
        x: Number.isNaN(x) ? 0 : x,
        y: Number.isNaN(y) ? 0 : y,
      },
      data: { label: n.label, config: n.config || {} },
    };
  });
}

function toRfEdges(apiEdges) {
  return (apiEdges || [])
    .map((e, i) => {
      const source = e.source ?? e.from;
      const target = e.target ?? e.to;
      if (source == null || target == null) return null;
      return {
        id: `e-${source}-${target}-${i}`,
        source,
        target,
        label: e.label || "",
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed },
      };
    })
    .filter(Boolean);
}

function toApiNodes(rfNodes) {
  return (rfNodes || []).map((n) => ({
    id: n.id,
    type: n.type,
    label: n.data.label,
    x: n.position.x,
    y: n.position.y,
    config: n.data.config || {},
  }));
}

function toApiEdges(rfEdges) {
  return (rfEdges || []).map((e) => ({
    from: e.source,
    to: e.target,
    label: e.label || "",
  }));
}

export default function FlowBuilder({ journeyId, journeyName }) {
  const { flow, loading, saving, publishing, validating, validation, save, validate, publish, error } =
    useFlowBuilder(journeyId);
  const [selectedId, setSelectedId] = useState(null);

  const initialNodes = useMemo(
    () => toRfNodes(flow?.definition?.nodes),
    [flow]
  );
  const initialEdges = useMemo(
    () => toRfEdges(flow?.definition?.edges),
    [flow]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(toRfNodes(flow?.definition?.nodes));
    setEdges(toRfEdges(flow?.definition?.edges));
  }, [flow, setNodes, setEdges]);

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedId) || null,
    [nodes, selectedId]
  );

  const onConnect = useCallback(
    (connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            type: "smoothstep",
            markerEnd: { type: MarkerType.ArrowClosed },
          },
          eds
        )
      );
    },
    [setEdges]
  );

  const onNodeClick = useCallback((_event, node) => {
    setSelectedId(node.id);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedId(null);
  }, []);

  const onDropNode = useCallback(
    (newNode) => {
      setNodes((nds) => nds.concat(newNode));
      setSelectedId(newNode.id);
    },
    [setNodes]
  );

  const onUpdateNode = useCallback(
    (nodeId, updates) => {
      setNodes((nds) =>
        nds.map((n) => {
          if (n.id !== nodeId) return n;
          return {
            ...n,
            data: { ...n.data, ...updates },
          };
        })
      );
    },
    [setNodes]
  );

  const buildDefinition = useCallback(() => {
    return {
      nodes: toApiNodes(nodes),
      edges: toApiEdges(edges),
    };
  }, [nodes, edges]);

  const handleSave = useCallback(() => {
    save(buildDefinition());
  }, [save, buildDefinition]);

  const handleValidate = useCallback(async () => {
    if (!flow?.id) {
      toast.error("Save the flow first before validating");
      return;
    }
    // Validate always checks the persisted definition, so make sure the
    // current canvas is saved first — otherwise it silently validates a
    // stale, previously-saved copy that may be missing edits made since.
    await save(buildDefinition());
    await validate(flow.id);
  }, [validate, save, buildDefinition, flow]);

  const handlePublish = useCallback(async () => {
    if (!flow?.id) return;
    // Same reasoning as handleValidate: publish validates the persisted
    // definition, so save the live canvas first.
    await save(buildDefinition());
    await publish(flow.id);
  }, [publish, save, buildDefinition, flow]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Loading flow builder...
      </div>
    );
  }

  const hasErrors = validation && !validation.valid;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <FlowToolbar
        journeyName={journeyName}
        onSave={handleSave}
        onValidate={handleValidate}
        onPublish={handlePublish}
        saving={saving}
        publishing={publishing}
        validating={validating}
        hasErrors={hasErrors}
      />

      {validation && (
        <div className={`border-b px-6 py-2 text-xs ${hasErrors ? "bg-red-50 border-red-200" : "bg-emerald-50 border-emerald-200"}`}>
          {hasErrors ? (
            <div className="space-y-1">
              <p className="font-semibold text-red-700">
                Validation failed — {validation.errors.length} error{validation.errors.length !== 1 ? "s" : ""}
              </p>
              <ul className="list-disc pl-4 text-red-600">
                {validation.errors.map((err, i) => (
                  <li key={i}>{err.message}</li>
                ))}
              </ul>
              {validation.warnings?.length > 0 && (
                <>
                  <p className="mt-2 font-semibold text-amber-700">
                    {validation.warnings.length} warning{validation.warnings.length !== 1 ? "s" : ""}
                  </p>
                  <ul className="list-disc pl-4 text-amber-600">
                    {validation.warnings.map((w, i) => (
                      <li key={i}>{w.message}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-emerald-700">
              <span className="font-semibold">Flow is valid</span>
              {validation.warnings?.length > 0 && (
                <span className="text-amber-600">
                  — {validation.warnings.length} warning{validation.warnings.length !== 1 ? "s" : ""}
                </span>
              )}
            </div>
          )}
        </div>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-1 grid-rows-[180px_minmax(360px,1fr)_240px] lg:grid-rows-1 lg:grid-cols-[200px_1fr_280px]">
        <NodePalette />
        <FlowCanvas
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          nodeTypes={NODE_TYPES}
          onDropNode={onDropNode}
        />
        <PropertiesPanel
          selectedNode={selectedNode}
          onUpdateNode={onUpdateNode}
        />
      </div>
    </div>
  );
}
