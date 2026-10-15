import { useMemo } from "react";
import {
  Background,
  BaseEdge,
  Controls,
  EdgeLabelRenderer,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  getSmoothStepPath,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const NODE_WIDTH = 250;
const X_GAP = 420;
const Y_GAP = 220;

function normaliseType(type = "") {
  return String(type).trim().toLowerCase();
}

function getNodeCategory(component) {
  const type = normaliseType(component.component_type);

  if (type.includes("database") || type.includes("data store")) {
    return "database";
  }

  if (type.includes("queue") || type.includes("broker")) {
    return "queue";
  }

  if (type.includes("gateway") || type.includes("load balancer")) {
    return "gateway";
  }

  if (type.includes("client") || type.includes("ui")) {
    return "client";
  }

  return "service";
}

function getTypeLabel(component) {
  const type = normaliseType(component.component_type);

  if (!type) {
    return "COMPONENT";
  }

  return type.replaceAll("_", " ").toUpperCase();
}

function ArchitectureNode({ data }) {
  const requirementDerived =
    data.groundingType === "requirement_derived";

  return (
    <div
      className={
        "architecture-flow-node architecture-flow-node-" +
        data.componentType
      }
      style={{ width: NODE_WIDTH }}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="architecture-flow-handle"
      />

      <div className="architecture-flow-node-top">
        <span className="architecture-flow-type">
          {data.typeLabel}
        </span>

        <span
          className={
            requirementDerived
              ? "architecture-flow-grounding requirement"
              : "architecture-flow-grounding structural"
          }
        >
          {requirementDerived ? "Requirement" : "Structural"}
        </span>
      </div>

      <strong className="architecture-flow-name">
        {data.name}
      </strong>

      {data.relatedRequirements.length > 0 && (
        <div className="architecture-flow-requirements">
          {data.relatedRequirements.map((requirementId) => (
            <span key={requirementId}>
              {requirementId}
            </span>
          ))}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Right}
        className="architecture-flow-handle"
      />
    </div>
  );
}

const nodeTypes = {
  architectureNode: ArchitectureNode,
};

function calculateLevels(components, connections) {
  const ids = new Set(
    components.map((component) => component.component_id)
  );

  const incomingCount = new Map();
  const adjacency = new Map();

  components.forEach((component) => {
    incomingCount.set(component.component_id, 0);
    adjacency.set(component.component_id, []);
  });

  connections.forEach((connection) => {
    if (
      !ids.has(connection.source) ||
      !ids.has(connection.target)
    ) {
      return;
    }

    adjacency.get(connection.source).push(connection.target);

    incomingCount.set(
      connection.target,
      (incomingCount.get(connection.target) || 0) + 1
    );
  });

  const queue = [];
  const levels = new Map();

  components.forEach((component) => {
    if (
      (incomingCount.get(component.component_id) || 0) === 0
    ) {
      queue.push(component.component_id);
      levels.set(component.component_id, 0);
    }
  });

  while (queue.length > 0) {
    const current = queue.shift();
    const currentLevel = levels.get(current) || 0;

    for (const target of adjacency.get(current) || []) {
      levels.set(
        target,
        Math.max(
          levels.get(target) || 0,
          currentLevel + 1
        )
      );

      incomingCount.set(
        target,
        incomingCount.get(target) - 1
      );

      if (incomingCount.get(target) === 0) {
        queue.push(target);
      }
    }
  }

  const resolvedLevels = [...levels.values()];

  const fallbackLevel =
    resolvedLevels.length > 0
      ? Math.max(...resolvedLevels) + 1
      : 0;

  components.forEach((component) => {
    if (!levels.has(component.component_id)) {
      levels.set(component.component_id, fallbackLevel);
    }
  });

  return levels;
}

function buildFlowNodes(components, connections) {
  const levels = calculateLevels(
    components,
    connections
  );

  const levelGroups = new Map();

  components.forEach((component) => {
    const level =
      levels.get(component.component_id) || 0;

    if (!levelGroups.has(level)) {
      levelGroups.set(level, []);
    }

    levelGroups.get(level).push(component);
  });

  const entries = [...levelGroups.entries()].sort(
    ([a], [b]) => a - b
  );

  const largestColumn = Math.max(
    1,
    ...entries.map(([, items]) => items.length)
  );

  const diagramHeight =
    (largestColumn - 1) * Y_GAP;

  const nodes = [];

  entries.forEach(([level, items]) => {
    const columnHeight =
      (items.length - 1) * Y_GAP;

    const startY =
      (diagramHeight - columnHeight) / 2;

    items.forEach((component, rowIndex) => {
      const category =
        getNodeCategory(component);

      nodes.push({
        id: component.component_id,
        type: "architectureNode",
        position: {
          x: level * X_GAP,
          y: startY + rowIndex * Y_GAP,
        },
        data: {
          name: component.name,
          componentType: category,
          typeLabel:
            getTypeLabel(component),
          groundingType:
            component.grounding_type,
          relatedRequirements:
            component.related_requirements || [],
        },
      });
    });
  });

  return nodes;
}

function ArchitectureEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  data,
}) {
  const [edgePath, labelX, labelY] =
    getSmoothStepPath({
      sourceX,
      sourceY,
      targetX,
      targetY,
      sourcePosition,
      targetPosition,
      borderRadius: 18,
      offset: 28,
    });

  const compactLabel =
    data?.mechanism || "";

  const fullDescription = [
    data?.relationship,
    data?.mechanism,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        className="architecture-flow-edge"
      />

      {compactLabel && (
        <EdgeLabelRenderer>
          <div
            className="architecture-edge-label architecture-edge-label-compact"
            title={fullDescription}
            style={{
              transform:
                "translate(-50%, -50%) translate(" +
                labelX +
                "px, " +
                labelY +
                "px)",
            }}
          >
            {compactLabel}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

const edgeTypes = {
  architectureEdge: ArchitectureEdge,
};

function buildFlowEdges(connections) {
  return connections.map((connection, index) => ({
    id:
      connection.source +
      "-" +
      connection.target +
      "-" +
      index,
    source: connection.source,
    target: connection.target,
    type: "architectureEdge",
    data: {
      relationship:
        connection.relationship || "",
      mechanism:
        connection.protocol_or_mechanism || "",
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 16,
      height: 16,
    },
  }));
}

function miniMapNodeColor(
  node,
  isLightTheme = false
) {
  if (isLightTheme) {
    switch (node.data?.componentType) {
      case "database":
        return "#cbd8ee";
      case "gateway":
        return "#d9cdf5";
      case "queue":
        return "#eadfc9";
      case "client":
        return "#ddd7f1";
      default:
        return "#d8d3ea";
    }
  }

  switch (node.data?.componentType) {
    case "database":
      return "#31507a";
    case "gateway":
      return "#7650b8";
    case "queue":
      return "#80632e";
    case "client":
      return "#554b91";
    default:
      return "#4f3f74";
  }
}

function ArchitectureDiagram({
  components = [],
  connections = [],
  theme = "dark",
}) {
  const nodes = useMemo(
    () =>
      buildFlowNodes(
        components,
        connections
      ),
    [components, connections]
  );

  const edges = useMemo(
    () =>
      buildFlowEdges(
        connections
      ),
    [connections]
  );

  if (components.length === 0) {
    return (
      <div className="architecture-diagram-empty">
        No architecture components were generated.
      </div>
    );
  }

  return (
    <div className="architecture-diagram-wrapper">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{
          padding: 0.2,
          minZoom: 0.32,
          maxZoom: 0.95,
        }}
        minZoom={0.2}
        maxZoom={1.6}
        nodesConnectable={false}
        nodesDraggable
        elementsSelectable
        panOnDrag
        zoomOnScroll
        proOptions={{
          hideAttribution: true,
        }}
      >
        <Background
          gap={22}
          size={1}
          color={
            theme === "light"
              ? "#d8d5e6"
              : "#302b46"
          }
        />

        <MiniMap
          nodeColor={(node) =>
            miniMapNodeColor(
              node,
              theme === "light"
            )
          }
          nodeStrokeWidth={2}
          maskColor={
            theme === "light"
              ? "rgba(246, 246, 251, 0.78)"
              : "rgba(8, 9, 18, 0.78)"
          }
          pannable
          zoomable
        />

        <Controls
          showInteractive={false}
        />
      </ReactFlow>

      <div className="architecture-diagram-legend">
        <span>
          <i className="legend-dot requirement-dot" />
          Requirement-derived
        </span>

        <span>
          <i className="legend-dot structural-dot" />
          Architecture-structural
        </span>

        <span className="diagram-help-text">
          Drag nodes · scroll to zoom · drag canvas to pan
        </span>
      </div>
    </div>
  );
}

export default ArchitectureDiagram;
