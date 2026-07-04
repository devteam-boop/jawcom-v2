import { useState, useEffect, useCallback, useMemo } from "react";
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
};

function toRfNodes(apiNodes) {
  return (apiNodes || []).map((n) => ({
    id: n.id,
    type: n.type,
    position: { x: n.x, y: n.y },
    data: { label: n.label, config: n.config || {} },
  }));
}

function toRfEdges(apiEdges) {
  return (apiEdges || []).map((e, i) => ({
    id: `e-${e.from}-${e.to}-${i}`,
    source: e.from,
    target: e.to,
    label: e.label || "",
    type: "smoothstep",
    markerEnd: { type: MarkerType.ArrowClosed },
  }));
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
  const { flow, loading, saving, publishing, save, publish, error } =
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

  const handleValidate = useCallback(() => {}, []);

  const handlePublish = useCallback(() => {
    if (flow?.id) {
      publish(flow.id);
    }
  }, [publish, flow]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Loading flow builder...
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
        publishing={publishing}
      />
      <div className="grid min-h-0 flex-1 grid-rows-1 grid-cols-1 lg:grid-cols-[200px_1fr_280px]">
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
