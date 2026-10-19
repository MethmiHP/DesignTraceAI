import { useMemo, useCallback } from 'react';
import ReactFlow, {
  Background, Controls, MiniMap, Handle, Position,
  BaseEdge, EdgeLabelRenderer, getStraightPath,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { buildChenGraph, CHEN_SIZE } from './chenGraphBuilder.js';
import './ChenDiagram.css';

const hiddenHandle = { opacity: 0, pointerEvents: 'none' };

function Handles() {
  return <>
    {['top', 'left', 'bottom', 'right'].map(side => <Handle
      key={`target-${side}`} id={`${side}-target`} type="target"
      position={Position[side[0].toUpperCase() + side.slice(1)]}
      style={hiddenHandle}
    />)}
    {['top', 'left', 'bottom', 'right'].map(side => <Handle
      key={`source-${side}`} id={`${side}-source`} type="source"
      position={Position[side[0].toUpperCase() + side.slice(1)]}
      style={hiddenHandle}
    />)}
  </>;
}

function Entity({ data }) {
  return <div className="chen-entity"><Handles /><span>{data.label}</span></div>;
}
function Attribute({ data }) {
  return <div className="chen-attribute"><Handles />
    <span className={data.primaryKey ? 'chen-key' : ''}>{data.label}</span>
  </div>;
}
function Relationship({ data }) {
  return <div className="chen-relationship"><Handles />
    <svg viewBox="0 0 112 112" aria-hidden="true" preserveAspectRatio="none">
      <polygon points="56,2 110,56 56,110 2,56" fill="#ede9fe" stroke="#6d28d9" strokeWidth="2" />
    </svg>
    <span>{data.label}</span>
  </div>;
}

function ChenLine({ id, sourceX, sourceY, targetX, targetY, style, data }) {
  const [path] = getStraightPath({ sourceX, sourceY, targetX, targetY });
  const hasLabel = Boolean(data?.cardinality);
  const nearSource = data?.cardinalityAt === 'source';
  const fraction = nearSource ? 0.16 : 0.84;
  const labelX = sourceX + (targetX - sourceX) * fraction;
  const labelY = sourceY + (targetY - sourceY) * fraction;
  return <>
    <BaseEdge id={id} path={path} style={style} />
    {hasLabel && <EdgeLabelRenderer>
      <div className="chen-cardinality nodrag nopan" style={{
        position: 'absolute',
        transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY - 15}px)`,
        pointerEvents: 'none',
      }}>{data.cardinality}</div>
    </EdgeLabelRenderer>}
  </>;
}

const nodeTypes = { chenEntity: Entity, chenAttribute: Attribute, chenRelationship: Relationship };
const edgeTypes = { chenLine: ChenLine };
const xmlEscape = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;',
}[char]));

function graphToSvg(graph) {
  const { nodes, edges } = graph;
  if (!nodes.length) return '';
  const margin = 90;
  const minX = Math.min(...nodes.map(n => n.position.x)) - margin;
  const minY = Math.min(...nodes.map(n => n.position.y)) - margin;
  const maxX = Math.max(...nodes.map(n => n.position.x + CHEN_SIZE[n.type].width)) + margin;
  const maxY = Math.max(...nodes.map(n => n.position.y + CHEN_SIZE[n.type].height)) + margin;
  const byId = new Map(nodes.map(n => [n.id, n]));
  const center = n => ({
    x: n.position.x + CHEN_SIZE[n.type].width / 2,
    y: n.position.y + CHEN_SIZE[n.type].height / 2,
  });
  const anchor = (node, handle) => {
    const { x, y } = center(node);
    const { width, height } = CHEN_SIZE[node.type];
    if (handle.startsWith('left')) return { x: x - width / 2, y };
    if (handle.startsWith('right')) return { x: x + width / 2, y };
    if (handle.startsWith('top')) return { x, y: y - height / 2 };
    return { x, y: y + height / 2 };
  };
  const lines = edges.map(e => {
    const source = byId.get(e.source), target = byId.get(e.target);
    if (!source || !target) return '';
    const a = anchor(source, e.sourceHandle), b = anchor(target, e.targetHandle);
    const cardinality = e.data?.cardinality;
    const t = e.data?.cardinalityAt === 'source' ? 0.16 : 0.84;
    const labelX = a.x + (b.x - a.x) * t;
    const labelY = a.y + (b.y - a.y) * t - 15;
    const label = cardinality
      ? `<rect x="${labelX - 12}" y="${labelY - 14}" width="24" height="22" rx="5" fill="white" stroke="#dbeafe"/><text x="${labelX}" y="${labelY + 2}" font-size="14" font-weight="700" text-anchor="middle" fill="#1d4ed8">${xmlEscape(cardinality)}</text>`
      : '';
    return `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}" stroke="#64748b" stroke-width="1.7"/>${label}`;
  }).join('');
  const shapes = nodes.map(n => {
    const { x, y } = n.position;
    const { width, height } = CHEN_SIZE[n.type];
    const cx = x + width / 2, cy = y + height / 2;
    const label = xmlEscape(n.data.label);
    if (n.type === 'chenEntity') return `<rect x="${x}" y="${y}" width="${width}" height="${height}" fill="#f5f3ff" stroke="#6d28d9" stroke-width="2"/><text x="${cx}" y="${cy + 5}" text-anchor="middle" font-size="15" font-weight="700" fill="#1e1b4b">${label}</text>`;
    if (n.type === 'chenRelationship') return `<polygon points="${cx},${y + 2} ${x + width - 2},${cy} ${cx},${y + height - 2} ${x + 2},${cy}" fill="#ede9fe" stroke="#6d28d9" stroke-width="2"/><text x="${cx}" y="${cy + 4}" text-anchor="middle" font-size="12" fill="#312e81">${label}</text>`;
    return `<ellipse cx="${cx}" cy="${cy}" rx="${width / 2 - 2}" ry="${height / 2 - 2}" fill="white" stroke="#64748b" stroke-width="2"/><text x="${cx}" y="${cy + 4}" text-anchor="middle" font-size="12" fill="#334155" ${n.data.primaryKey ? 'text-decoration="underline" font-weight="600"' : ''}>${label}</text>`;
  }).join('');
  const width = maxX - minX, height = maxY - minY;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="${minX} ${minY} ${width} ${height}"><rect x="${minX}" y="${minY}" width="${width}" height="${height}" fill="white"/>${lines}${shapes}</svg>`;
}

export default function ChenDiagram({ design, projectId }) {
  const graph = useMemo(() => buildChenGraph(design), [design]);
  const download = useCallback(() => {
    if (!graph.nodes.length) return;
    const blob = new Blob([graphToSvg(graph)], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${String(projectId || 'database').replace(/[^a-zA-Z0-9_-]/g, '_')}_chen.svg`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }, [graph, projectId]);

  return <div className="chen-section">
    <div className="chen-header">
      <strong>Chen ER Diagram (Conceptual)</strong>
      <button type="button" onClick={download} disabled={!graph.nodes.length}>Download Chen SVG</button>
    </div>
    <p>Foreign-key columns already represented by relationships are omitted from the conceptual attributes. Cardinalities come from generated relationship metadata.</p>
    <div className="chen-flow">
      <ReactFlow
        nodes={graph.nodes} edges={graph.edges}
        nodeTypes={nodeTypes} edgeTypes={edgeTypes}
        fitView fitViewOptions={{ padding: 0.15 }}
        minZoom={0.08} maxZoom={2}
        nodesDraggable={false} nodesConnectable={false}
        elementsSelectable={false} proOptions={{ hideAttribution: true }}
      >
        <Background gap={24} color="#e9e5fa" />
        <Controls />
        <MiniMap pannable zoomable />
      </ReactFlow>
    </div>
  </div>;
}
