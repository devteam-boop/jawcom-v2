import { useCallback, useRef } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

function CanvasInner({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onNodeClick,
  onPaneClick,
  nodeTypes,
  onDropNode,
}) {
  const reactFlowWrapper = useRef(null);
  const { screenToFlowPosition } = useReactFlow();

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const type = event.dataTransfer.getData("application/reactflow");
      if (!type || !reactFlowWrapper.current) return;
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });
      const newId = `${type}_${Date.now()}`;
      const newNode = {
        id: newId,
        type,
        position,
        data: { label: `${type.charAt(0).toUpperCase() + type.slice(1)} node`, config: {} },
      };
      onDropNode(newNode);
    },
    [screenToFlowPosition, onDropNode]
  );

  return (
    <main className="relative h-full w-full bg-secondary/30" ref={reactFlowWrapper}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        onDrop={onDrop}
        onDragOver={onDragOver}
        fitView
        panOnDrag
        zoomOnScroll
        panOnScroll={false}
        nodesDraggable={true}
        nodesConnectable={true}
        elementsSelectable={true}
        deleteKeyCode="Delete"
        snapToGrid
        snapGrid={[20, 20]}
      >
        <Background gap={20} size={1} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </main>
  );
}

export default function FlowCanvas(props) {
  return (
    <ReactFlowProvider>
      <CanvasInner {...props} />
    </ReactFlowProvider>
  );
}
