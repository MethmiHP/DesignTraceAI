
// chenGraphBuilder.js
// Builds a Chen-style conceptual ER diagram from a generated database design.

// IMPORTANT:
// These sizes must match ChenDiagram.css and ChenDiagram.jsx.
export const CHEN_SIZE = {
  chenEntity: { width: 180, height: 64 },
  chenAttribute: { width: 174, height: 62 },
  chenRelationship: { width: 112, height: 112 },
};

const ENTITY_WIDTH = CHEN_SIZE.chenEntity.width;
const ENTITY_HEIGHT = CHEN_SIZE.chenEntity.height;
const ATTRIBUTE_WIDTH = CHEN_SIZE.chenAttribute.width;
const ATTRIBUTE_HEIGHT = CHEN_SIZE.chenAttribute.height;
const RELATIONSHIP_WIDTH = CHEN_SIZE.chenRelationship.width;
const RELATIONSHIP_HEIGHT = CHEN_SIZE.chenRelationship.height;

// Large spacing makes the diagram easier to read.
const COLUMN_SPACING = 1050;
const ROW_SPACING = 850;
const COLUMNS = 2;

function normalizeRelationshipType(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[_\s]+/g, "-");
}

function getCardinalities(relationship) {
  const type = normalizeRelationshipType(
    relationship.relationship_type ||
    relationship.cardinality ||
    relationship.type
  );

  if (type === "one-to-one" || type === "1:1") {
    return ["1", "1"];
  }

  if (
    type === "one-to-many" ||
    type === "1:n" ||
    type === "1:m"
  ) {
    return ["1", "N"];
  }

  if (
    type === "many-to-one" ||
    type === "n:1" ||
    type === "m:1"
  ) {
    return ["N", "1"];
  }

  if (
    type === "many-to-many" ||
    type === "m:n" ||
    type === "n:m"
  ) {
    return ["M", "N"];
  }

  // Never invent cardinalities if they are not specified.
  return ["", ""];
}

function makeEdge(id, source, target, label = "") {
  return {
    id,
    source,
    target,
    type: "straight",
    label,
    style: {
      stroke: "#64748b",
      strokeWidth: 1.7,
    },
    labelStyle: {
      fill: "#1e293b",
      fontSize: 17,
      fontWeight: 700,
    },
    labelBgPadding: [7, 6],
    labelBgBorderRadius: 5,
    labelBgStyle: {
      fill: "#ffffff",
      fillOpacity: 1,
    },
    zIndex: 0,
  };
}

function getNodeCenter(node) {
  const size = CHEN_SIZE[node.type];

  return {
    x: node.position.x + size.width / 2,
    y: node.position.y + size.height / 2,
  };
}

function chooseHandle(from, to, isSource) {
  const a = getNodeCenter(from);
  const b = getNodeCenter(to);

  const dx = b.x - a.x;
  const dy = b.y - a.y;

  let side;

  if (Math.abs(dx) > Math.abs(dy)) {
    side = dx >= 0 ? "right" : "left";
  } else {
    side = dy >= 0 ? "bottom" : "top";
  }

  if (!isSource) {
    const opposite = {
      left: "right",
      right: "left",
      top: "bottom",
      bottom: "top",
    };

    side = opposite[side];
  }

  return `${side}-${isSource ? "source" : "target"}`;
}

function connectNodes(
  id,
  source,
  target,
  label = "",
  options = {}
) {
  const edge = makeEdge(id, source.id, target.id, label);

  edge.sourceHandle = chooseHandle(source, target, true);
  edge.targetHandle = chooseHandle(source, target, false);

  if (options.cardinality) {
    edge.data = {
      cardinality: true,
      entityEnd: options.entityEnd || "source",
    };
  }

  return edge;
}

function createAttributePositions(entity, attributes) {
  const count = attributes.length;

  if (count === 0) {
    return [];
  }

  const positions = [];

  // Use rows above and below the entity instead of
  // a circular arrangement. This reduces collisions.
  const topCount = Math.ceil(count / 2);
  const bottomCount = count - topCount;

  const centerX = entity.position.x + ENTITY_WIDTH / 2;

  function addRow(start, rowCount, centerY) {
    if (rowCount === 0) {
      return;
    }

    const spacing = ATTRIBUTE_WIDTH + 46;
    const totalWidth = (rowCount - 1) * spacing;

    for (let i = 0; i < rowCount; i++) {
      positions.push({
        index: start + i,
        x:
          centerX -
          totalWidth / 2 +
          i * spacing -
          ATTRIBUTE_WIDTH / 2,
        y: centerY - ATTRIBUTE_HEIGHT / 2,
      });
    }
  }

  addRow(
    0,
    topCount,
    entity.position.y - 175
  );

  addRow(
    topCount,
    bottomCount,
    entity.position.y + ENTITY_HEIGHT + 175
  );

  return positions;
}

export function buildChenGraph(design) {
  const tables = Array.isArray(design?.tables)
    ? design.tables
    : [];

  const relationships = Array.isArray(design?.relationships)
    ? design.relationships
    : [];

  const nodes = [];
  const edges = [];

  const tableNodes = new Map();
  const relationshipPairs = new Map();

  // ----------------------------------------------------
  // STEP 1: Create entity nodes.
  // ----------------------------------------------------

  tables.forEach((table, index) => {
    const tableName = table.table_name || table.name;

    if (!tableName) {
      return;
    }

    const column = index % COLUMNS;
    const row = Math.floor(index / COLUMNS);

    const entity = {
      id: `entity-${index}`,
      type: "chenEntity",
      position: {
        x: 420 + column * COLUMN_SPACING,
        y: 320 + row * ROW_SPACING,
      },
      data: {
        label: tableName,
      },
      draggable: false,
    };

    nodes.push(entity);
    tableNodes.set(tableName, entity);

    // ------------------------------------------------
    // STEP 2: Create conceptual attributes.
    // ------------------------------------------------

    const columns = Array.isArray(table.columns)
      ? table.columns
      : [];

    // A foreign key represented by a relationship
    // does not need to appear again as an attribute.
    const attributes = columns.filter(
      (column) =>
        !column.foreign_key || column.primary_key
    );

    const positions = createAttributePositions(
      entity,
      attributes
    );

    positions.forEach((position) => {
      const attribute = attributes[position.index];

      const attributeNode = {
        id: `attribute-${index}-${position.index}`,
        type: "chenAttribute",
        position: {
          x: position.x,
          y: position.y,
        },
        data: {
          label:
            attribute.name ||
            attribute.column_name ||
            "",
          primaryKey: Boolean(attribute.primary_key),
        },
        draggable: false,
      };

      nodes.push(attributeNode);

      edges.push(
        connectNodes(
          `entity-attribute-${index}-${position.index}`,
          entity,
          attributeNode
        )
      );
    });
  });

  // ----------------------------------------------------
  // STEP 3: Create relationship diamonds.
  // ----------------------------------------------------

  relationships.forEach((relationship, index) => {
    const source = tableNodes.get(
      relationship.from_table
    );

    const target = tableNodes.get(
      relationship.to_table
    );

    if (!source || !target) {
      return;
    }

    const sourceCenter = getNodeCenter(source);
    const targetCenter = getNodeCenter(target);

    const midpointX =
      (sourceCenter.x + targetCenter.x) / 2;

    const midpointY =
      (sourceCenter.y + targetCenter.y) / 2;

    // Track repeated relationships between the same
    // pair of entities so their diamonds can be offset.
    const pairKey = [
      source.id,
      target.id,
    ].sort().join("|");

    const pairCount =
      relationshipPairs.get(pairKey) || 0;

    relationshipPairs.set(
      pairKey,
      pairCount + 1
    );

    const dx = targetCenter.x - sourceCenter.x;
    const dy = targetCenter.y - sourceCenter.y;

    const distance = Math.hypot(dx, dy) || 1;

    // Perpendicular offset prevents repeated diamonds
    // from sitting directly on top of each other.
    const perpendicularX = -dy / distance;
    const perpendicularY = dx / distance;

    const offset =
      pairCount === 0
        ? 0
        : Math.ceil(pairCount / 2) *
          150 *
          (pairCount % 2 === 0 ? -1 : 1);

    const relationshipNode = {
      id: `relationship-${index}`,
      type: "chenRelationship",
      position: {
        x:
          midpointX -
          RELATIONSHIP_WIDTH / 2 +
          perpendicularX * offset,
        y:
          midpointY -
          RELATIONSHIP_HEIGHT / 2 +
          perpendicularY * offset,
      },
      data: {
        label:
          relationship.name ||
          relationship.label ||
          "relates",
      },
      draggable: false,
    };

    nodes.push(relationshipNode);

    const [
      sourceCardinality,
      targetCardinality,
    ] = getCardinalities(relationship);

    // Cardinality belongs to the entity end,
    // not to the relationship diamond.
    edges.push(
      connectNodes(
        `relationship-${index}-source`,
        source,
        relationshipNode,
        sourceCardinality,
        {
          cardinality: true,
          entityEnd: "source",
        }
      )
    );

    edges.push(
      connectNodes(
        `relationship-${index}-target`,
        relationshipNode,
        target,
        targetCardinality,
        {
          cardinality: true,
          entityEnd: "target",
        }
      )
    );
  });

  return {
    nodes,
    edges,
  };
}
