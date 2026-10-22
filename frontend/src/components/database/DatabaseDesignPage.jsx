import ChenDiagram from "./ChenDiagram";
import { useEffect, useMemo, useRef, useState } from "react";

import mermaid from "mermaid";

import {

  ArrowRight,

  Check,

  CheckCircle2,

  ChevronDown,

  CircleAlert,

  ClipboardList,

  Code2,

  Database,

  Download,

  FileJson,

  FileText,

  GitBranch,

  Layers3,

  LoaderCircle,

  Maximize2,

  Plus,

  RefreshCw,

  Search,

  ShieldCheck,

  Sparkles,

  Table2,

  Trash2,

  WandSparkles,

  X,

  ZoomIn,

  ZoomOut,

} from "lucide-react";

import {

  downloadFile,

  generateDatabaseDesign,

} from "../../services/databaseApi";

import "./DatabaseDesignPage.css";

const DATABASE_EXAMPLES = {
  hospital: { project_id: "TEST-HOSPITAL-AI-001", project_name: "Hospital Management System", project_description: "A system for managing patients, doctors, and hospital appointments.", architecture_style: "Layered", constraints: ["Use a relational database.", "Each appointment must reference an existing patient and doctor.", "Patient email addresses must be unique."], requirements: [
    {requirement_id:"FR-001",requirement_text:"The system shall register patients with name and unique email address.",requirement_type:"functional",database_relevant:true},
    {requirement_id:"FR-002",requirement_text:"The system shall store doctor name and specialization.",requirement_type:"functional",database_relevant:true},
    {requirement_id:"FR-003",requirement_text:"Patients shall book appointments with doctors, and each appointment shall have an appointment date and status.",requirement_type:"functional",database_relevant:true},
  ]},
  library: { project_id:"TEST-LIBRARY-002",project_name:"Library Management System",project_description:"Manage books, library members, and borrowing records.",architecture_style:"Layered",constraints:["Book ISBN values must be unique.","Member email addresses must be unique.","Publication year must be greater than zero.","Each borrowing record must reference an existing book and member."],requirements:[
    {requirement_id:"FR-001",requirement_text:"The system shall store books with title, ISBN, author, and publication year.",requirement_type:"functional",database_relevant:true},
    {requirement_id:"FR-002",requirement_text:"The system shall register members with name and unique email address.",requirement_type:"functional",database_relevant:true},
    {requirement_id:"FR-003",requirement_text:"Members shall borrow books and the system shall record borrowing and return dates.",requirement_type:"functional",database_relevant:true},
  ]},
  university: { project_id:"TEST-UNIVERSITY-001",project_name:"Student Course Registration System",project_description:"Manage students, instructors, courses, and registrations.",architecture_style:"Layered",constraints:["Student email addresses must be unique.","Course codes must be unique.","Course credit hours must be greater than zero.","Course maximum capacity must be greater than zero.","Each registration must reference an existing student and course."],requirements:[
    {requirement_id:"FR-001",requirement_text:"The system shall register students with a unique email address.",requirement_type:"functional",database_relevant:true},
    {requirement_id:"FR-002",requirement_text:"The system shall store instructors and their departments.",requirement_type:"functional",database_relevant:true},
    {requirement_id:"FR-003",requirement_text:"The system shall store courses with unique course codes, credit hours, maximum capacity, and instructor details.",requirement_type:"functional",database_relevant:true},
    {requirement_id:"FR-004",requirement_text:"Students shall register for courses and the system shall record registration date and grade.",requirement_type:"functional",database_relevant:true},
  ]},
};

const EXAMPLE_REQUIREMENTS = [

  {

    requirement_id: "FR-001",

    requirement_text:

      "The system shall register patients with name and unique email address.",

    requirement_type: "functional",

    database_relevant: true,

  },

  {

    requirement_id: "FR-002",

    requirement_text:

      "The system shall store doctor name and specialization.",

    requirement_type: "functional",

    database_relevant: true,

  },

  {

    requirement_id: "FR-003",

    requirement_text:

      "Patients shall book appointments with doctors, and each appointment shall have an appointment date and status.",

    requirement_type: "functional",

    database_relevant: true,

  },

];

const TABS = [

  { id: "diagram", label: "ER Diagram", icon: GitBranch },

  { id: "schema", label: "Schema", icon: Table2 },

  { id: "relationships", label: "Relationships", icon: Layers3 },

  { id: "traceability", label: "Traceability", icon: ClipboardList },

  { id: "validation", label: "Validation", icon: ShieldCheck },

  { id: "sql", label: "SQL Preview", icon: Code2 },

];

function newRequirement(index) {

  return {

    requirement_id: `FR-${String(index).padStart(3, "0")}`,

    requirement_text: "",

    requirement_type: "functional",

    database_relevant: true,

  };

}

function mermaidIdentifier(value) {

  const clean = String(value || "unnamed")

    .replace(/[^a-zA-Z0-9_]/g, "_");

  return /^[a-zA-Z_]/.test(clean) ? clean : `T_${clean}`;

}

function buildMermaid(design) {

  const lines = ["erDiagram"];

  for (const table of design?.tables || []) {

    const tableName = mermaidIdentifier(table.table_name);

    lines.push(`  ${tableName} {`);

    for (const column of table.columns || []) {

      const dataType = mermaidIdentifier(

        String(column.data_type || "string").replace(/\([^)]*\)/g, "")

      );

      const columnName = mermaidIdentifier(column.name);

      const key = column.primary_key

        ? " PK"

        : column.foreign_key

        ? " FK"

        : "";

      lines.push(`    ${dataType} ${columnName}${key}`);

    }

    lines.push("  }");

  }

  for (const relationship of design?.relationships || []) {

    const parent = mermaidIdentifier(relationship.from_table);

    const child = mermaidIdentifier(relationship.to_table);

    const symbol =

      relationship.relationship_type === "one-to-one"

        ? "||--||"

        : relationship.relationship_type === "many-to-one"

        ? "}o--||"

        : relationship.relationship_type === "many-to-many"

        ? "}o--o{"

        : "||--o{";

    const label = String(

      relationship.foreign_key || "references"

    ).replace(/"/g, "'");

    lines.push(

      `  ${parent} ${symbol} ${child} : "${label}"`

    );

  }

  return lines.join("\n");

}

function MermaidDiagram({ definition }) {
  const [theme, setTheme] = useState(document.documentElement.getAttribute("data-theme") || "dark");
  useEffect(() => { const observer = new MutationObserver(() => setTheme(document.documentElement.getAttribute("data-theme") || "dark")); observer.observe(document.documentElement, {attributes:true,attributeFilter:["data-theme"]}); return () => observer.disconnect(); }, []);

  const containerRef = useRef(null);

  const [zoom, setZoom] = useState(1);

  const [renderError, setRenderError] = useState("");

  useEffect(() => {

    let cancelled = false;

    async function renderDiagram() {

      if (!containerRef.current || !definition) return;

      try {

        mermaid.initialize({

          startOnLoad: false,

          securityLevel: "strict",

          theme: "base",

          themeVariables: {

            primaryColor: theme === "dark" ? "#28233f" : "#f1ecff",

            primaryTextColor: theme === "dark" ? "#f5f2ff" : "#30244d",

            primaryBorderColor: "#8e7be9",

            lineColor: "#8e7be9",

            secondaryColor: theme === "dark" ? "#201c35" : "#f7f3ff",

            tertiaryColor: theme === "dark" ? "#161326" : "#ffffff",

            background: theme === "dark" ? "#171527" : "#ffffff",

            fontFamily: "Inter, sans-serif",

          },

        });

        const id = `designtrace-er-${Date.now()}-${Math.floor(

          Math.random() * 100000

        )}`;

        const { svg } = await mermaid.render(id, definition);

        if (!cancelled && containerRef.current) {

          containerRef.current.innerHTML = svg;

          setRenderError("");

        }

      } catch (error) {

        if (!cancelled) {

          setRenderError(error.message || "Diagram rendering failed.");

        }

      }

    }

    renderDiagram();

    return () => {

      cancelled = true;

    };

  }, [definition, theme]);

  return (

    <div className="db-diagram-shell">

      <div className="db-diagram-toolbar">

        <div className="db-diagram-toolbar-left">

          <span className="db-live-dot" />

          Generated ER diagram

        </div>

        <div className="db-diagram-actions">

          <button

            title="Zoom out"

            onClick={() =>

              setZoom((value) => Math.max(0.5, value - 0.15))

            }

          >

            <ZoomOut size={16} />

          </button>

          <span>{Math.round(zoom * 100)}%</span>

          <button

            title="Zoom in"

            onClick={() =>

              setZoom((value) => Math.min(2, value + 0.15))

            }

          >

            <ZoomIn size={16} />

          </button>

          <button title="Reset zoom" onClick={() => setZoom(1)}>

            <Maximize2 size={16} />

          </button>

        </div>

      </div>

      <div className="db-diagram-canvas">

        {renderError ? (

          <div className="db-diagram-error">

            <CircleAlert size={25} />

            <p>Could not render the ER diagram.</p>

            <small>{renderError}</small>

          </div>

        ) : (

          <div

            className="db-mermaid-render"

            style={{ transform: `scale(${zoom})` }}

            ref={containerRef}

          />

        )}

      </div>

    </div>

  );

}

function Metric({ icon: Icon, value, label, tone }) {

  return (

    <div className={`db-metric db-metric-${tone}`}>

      <div className="db-metric-icon">

        <Icon size={18} />

      </div>

      <div>

        <strong>{value}</strong>

        <span>{label}</span>

      </div>

    </div>

  );

}

function SchemaTable({ table, selected, onSelect }) {

  return (

    <button

      className={`db-schema-card ${selected ? "selected" : ""}`}

      onClick={onSelect}

    >

      <div className="db-schema-card-header">

        <div>

          <Database size={16} />

          <strong>{table.table_name}</strong>

        </div>

        <span>{table.columns?.length || 0} columns</span>

      </div>

      <div className="db-schema-columns">

        {(table.columns || []).map((column) => (

          <div className="db-schema-column" key={column.name}>

            <div>

              {column.primary_key ? (

                <span className="db-key-label pk">PK</span>

              ) : column.foreign_key ? (

                <span className="db-key-label fk">FK</span>

              ) : (

                <span className="db-column-bullet" />

              )}

              <span>{column.name}</span>

            </div>

            <code>{column.data_type}</code>

          </div>

        ))}

      </div>

    </button>

  );

}

function TableInspector({ table, onUpdate }) {

  if (!table) {

    return (

      <div className="db-inspector-empty">

        Select a table to view its properties.

      </div>

    );

  }

  function updateColumn(index, field, value) {

    const columns = table.columns.map((column, i) =>

      i === index ? { ...column, [field]: value } : column

    );

    onUpdate({ ...table, columns });

  }

  return (

    <div className="db-inspector-content">

      <div className="db-inspector-intro">

        <span className="db-small-label">SELECTED TABLE</span>

        <h3>{table.table_name}</h3>

        <p>

          Inspect or edit this local draft. Edits are not yet saved

          to the backend or revalidated.

        </p>

      </div>

      <div className="db-form-field">

        <label>Table Name</label>

        <input

          value={table.table_name}

          onChange={(event) =>

            onUpdate({

              ...table,

              table_name: event.target.value,

            })

          }

        />

      </div>

      <div className="db-form-field">

        <label>Purpose</label>

        <textarea

          rows={2}

          value={table.purpose || ""}

          placeholder="Describe the purpose of this table"

          onChange={(event) =>

            onUpdate({

              ...table,

              purpose: event.target.value,

            })

          }

        />

      </div>

      <div className="db-inspector-subtitle">

        <h4>Columns ({table.columns?.length || 0})</h4>

        <span>Local draft</span>

      </div>

      <div className="db-inspector-column-list">

        {(table.columns || []).map((column, index) => (

          <div className="db-inspector-column" key={index}>

            <div className="db-inspector-column-top">

              <span>

                {column.primary_key

                  ? "Primary key"

                  : column.foreign_key

                  ? "Foreign key"

                  : "Column"}

              </span>

              <code>{column.data_type}</code>

            </div>

            <div className="db-inspector-fields">

              <input

                aria-label="Column name"

                value={column.name}

                onChange={(event) =>

                  updateColumn(index, "name", event.target.value)

                }

              />

              <input

                aria-label="Column data type"

                value={column.data_type}

                onChange={(event) =>

                  updateColumn(index, "data_type", event.target.value)

                }

              />

            </div>

          </div>

        ))}

      </div>

    </div>

  );

}

export default function DatabaseDesignPage({ onProjectChange }) {
  const [selectedExample, setSelectedExample] = useState("hospital");

  const [projectId, setProjectId] = useState("TEST-HOSPITAL-AI-001");

  const [projectName, setProjectName] = useState(

    "Hospital Management System"

  );

  const [projectDescription, setProjectDescription] = useState("A system for managing patients, doctors, and hospital appointments.");

  const [requirements, setRequirements] = useState(

    EXAMPLE_REQUIREMENTS.map((item) => ({ ...item }))

  );

  const [architectureStyle, setArchitectureStyle] = useState("Layered");

  const [databaseType, setDatabaseType] = useState("Relational");

  const [constraints, setConstraints] = useState(

    "Use a relational database.\nEach appointment must reference an existing patient and doctor.\nPatient email addresses must be unique."

  );

  const [result, setResult] = useState(null);
  const [sqlContent, setSqlContent] = useState("");
  const [sqlLoading, setSqlLoading] = useState(false);
  const [sqlError, setSqlError] = useState("");

  const [draftDesign, setDraftDesign] = useState(null);

  const [selectedTableIndex, setSelectedTableIndex] = useState(0);

  const [activeTab, setActiveTab] = useState("diagram");
  const [diagramType, setDiagramType] = useState("crow");

  const [showInputs, setShowInputs] = useState(true);

  const [isGenerating, setIsGenerating] = useState(false);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  const [hasLocalEdits, setHasLocalEdits] = useState(false);

  useEffect(() => {
    if (activeTab !== "sql" || !result?.project_id) return;

    const controller = new AbortController();
    const loadSql = async () => {
      setSqlLoading(true);
      setSqlError("");
      setSqlContent("");

      try {
        const response = await fetch(
          `http://127.0.0.1:8000/api/database-design/artifacts/${encodeURIComponent(result.project_id)}/sql`,
          { signal: controller.signal }
        );
        if (!response.ok) {
          throw new Error(`Could not load SQL (HTTP ${response.status}).`);
        }
        const content = await response.text();
        if (!controller.signal.aborted) setSqlContent(content);
      } catch (err) {
        if (!controller.signal.aborted) setSqlError(err.message);
      } finally {
        if (!controller.signal.aborted) setSqlLoading(false);
      }
    };

    loadSql();
    return () => controller.abort();
  }, [activeTab, result?.project_id]);

  const diagramDefinition = useMemo(

    () => buildMermaid(draftDesign),

    [draftDesign]

  );

  const filteredTables = useMemo(

    () =>

      (draftDesign?.tables || []).filter((table) =>

        table.table_name.toLowerCase().includes(search.toLowerCase())

      ),

    [draftDesign, search]

  );

  function updateRequirement(index, field, value) {

    setRequirements((current) =>

      current.map((item, i) =>

        i === index ? { ...item, [field]: value } : item

      )

    );

  }

  function addRequirement() {

    const existing = new Set(

      requirements.map((item) => item.requirement_id)

    );

    let next = 1;

    while (existing.has(`FR-${String(next).padStart(3, "0")}`)) {

      next += 1;

    }

    setRequirements((current) => [

      ...current,

      newRequirement(next),

    ]);

  }

  function loadExample(exampleKey = selectedExample) {
    const example = DATABASE_EXAMPLES[exampleKey];
    if (!example) return;
    setSelectedExample(exampleKey);
    setProjectId(example.project_id);
    setProjectName(example.project_name);
    setProjectDescription(example.project_description);
    setRequirements(example.requirements.map(item => ({...item})));
    setArchitectureStyle(example.architecture_style);
    setDatabaseType("Relational");
    setConstraints(example.constraints.join("\n"));
    setResult(null);
    setDraftDesign(null);
    setSqlContent("");
    setHasLocalEdits(false);
    setError("");
    setShowInputs(true);
    onProjectChange?.({id: example.project_id, name: example.project_name});
  }

  async function handleGenerate() {

    setError("");

    const usableRequirements = requirements

      .filter((item) => item.requirement_text.trim())

      .map((item) => ({

        ...item,

        requirement_id: item.requirement_id.trim(),

      }));

    if (!projectId.trim() || !projectName.trim() || !projectDescription.trim()) {

      setError("Project ID, project name, and project description are required.");

      return;

    }

    if (usableRequirements.length === 0) {

      setError("Enter at least one requirement.");

      return;

    }

    const ids = usableRequirements.map((item) => item.requirement_id);

    if (ids.some((id) => !id) || new Set(ids).size !== ids.length) {

      setError("Every requirement must have a unique, nonempty ID.");

      return;

    }

    const payload = {

      project: {

        project_id: projectId.trim(),

        project_name: projectName.trim(),

        project_description: projectDescription.trim(),

        requirements: usableRequirements,

      },

      architecture_context: {

        architecture_style: architectureStyle,

        database_type: databaseType,

        constraints: constraints

          .split("\n")

          .map((item) => item.trim())

          .filter(Boolean),

      },

      generation_method: "gemini",

      extracted_concepts: null,

    };

    setIsGenerating(true);

    try {

      const data = await generateDatabaseDesign(payload);

      if (!data.design?.tables) {

        throw new Error(

          "The backend response does not contain design.tables."

        );

      }

      setResult(data);
      onProjectChange?.({id: projectId.trim(), name: projectName.trim()});

      setDraftDesign(structuredClone(data.design));

      setSelectedTableIndex(0);

      setActiveTab("diagram");

      setHasLocalEdits(false);

      setShowInputs(false);

    } catch (err) {

      setError(err.message || "Database generation failed.");

    } finally {

      setIsGenerating(false);

    }

  }

  function updateSelectedTable(updatedTable) {

    setDraftDesign((current) => ({

      ...current,

      tables: current.tables.map((table, index) =>

        index === selectedTableIndex ? updatedTable : table

      ),

    }));

    setHasLocalEdits(true);

  }

  function exportJSON() {

    if (!result) return;

    const content = {

      ...result,

      design: draftDesign,

      local_draft_modified: hasLocalEdits,

      note: hasLocalEdits

        ? "Local edits have not been revalidated."

        : "Generated backend response.",

    };

    downloadFile(

      `${result.project_id}_database_draft.json`,

      JSON.stringify(content, null, 2),

      "application/json"

    );

  }

  function exportMermaid() {

    if (!draftDesign) return;

    downloadFile(

      `${result?.project_id || "database"}_diagram.mmd`,

      diagramDefinition,

      "text/plain"

    );

  }

  const tables = draftDesign?.tables || [];

  const relationships = draftDesign?.relationships || [];

  const mapping = result?.mapping_validation;

  const validation = result?.schema_validation;

  const selectedTable = tables[selectedTableIndex];

  return (

    <div className="database-studio">

      <div className="db-page-header">

        <div>

          <div className="db-breadcrumb-label">

            DESIGN MODULES <span>→</span> DATABASE DESIGN

          </div>

          <h1>Database Design</h1>

          <p>

            Turn requirements into a traceable, validated relational

            database blueprint.

          </p>

        </div>

        <div className="db-page-header-actions">

          <span className="db-engine-tag">

            <Sparkles size={14} />

            RoBERTa + Gemini

          </span>

          <button

            className="db-secondary-button"

            onClick={() => setShowInputs((value) => !value)}

          >

            <ClipboardList size={16} />

            {showInputs ? "Hide Inputs" : "Show Inputs"}

          </button>

          <button

            className="db-secondary-button"

            onClick={exportJSON}

            disabled={!result}

          >

            <Download size={16} />

            Export Design

          </button>

        </div>

      </div>

      <div className="db-demo-notice">

        <div className="db-notice-icon">

          <WandSparkles size={18} />

        </div>

        <div>

          {/* <strong>Standalone Module Demonstration</strong> */}

          <p>

            Enter requirements or load an example to generate a database design.

            This Module generates and validates database drafts. Coordinator approval is managed separately.

          </p>

        </div>

        <span>Progress Demo</span>

      </div>

      <div className={`db-main-grid ${!showInputs ? "inputs-hidden" : ""}`}>

        {showInputs && (

          <section className="db-surface db-input-section">

            <div className="db-surface-heading">

              <div>

                <span className="db-small-label">01 / INPUT</span>

                <h2>Design Context</h2>

                <p>Provide the requirements for this module.</p>

              </div>

              <button

                className="db-text-button"

                onClick={() => loadExample()}

              >

                <RefreshCw size={14} />

                Load Example

              </button>

            </div>

            <div className="db-example-picker">
              <label htmlFor="db-example-select">QUICK START / SAMPLE PROJECT</label>
              <div className="db-example-controls">
                <select id="db-example-select" value={selectedExample} onChange={event => setSelectedExample(event.target.value)}>
                  <option value="hospital">Hospital Management</option>
                  <option value="library">Library Management</option>
                  <option value="university">University Registration</option>
                </select>
                <button type="button" onClick={() => loadExample()}><WandSparkles size={15}/> Load Example</button>
              </div>
              <small>Fills project details, requirements, and architecture constraints. Click Generate.</small>
            </div>
            <div className="db-input-content">

              <div className="db-form-field">

                <label>Project ID</label>

                <input

                  value={projectId}

                  onChange={(event) => setProjectId(event.target.value)}

                  placeholder="e.g. hospital-001"

                />

              </div>

              <div className="db-form-field">

                <label>Project Name</label>

                <input

                  value={projectName}

                  onChange={(event) => setProjectName(event.target.value)}

                  placeholder="Project name"

                />

              </div>

              <div className="db-form-field">

                <label htmlFor="db-project-description">Project Description</label>

                <textarea

                  id="db-project-description"

                  value={projectDescription}

                  onChange={(event) => setProjectDescription(event.target.value)}

                  placeholder="Describe what your project does and who uses it."

                  rows={3}

                  required

                />

              </div>

              <div className="db-section-heading">

                <div>

                  <h3>Functional Requirements</h3>

                  <small>{requirements.length} items</small>

                </div>

              </div>

              {requirements.map((requirement, index) => (

                <div className="db-requirement" key={index}>

                  <div className="db-requirement-header">

                    <span>REQUIREMENT {String(index + 1).padStart(2, "0")}</span>

                    <button

                      title="Remove requirement"

                      onClick={() =>

                        setRequirements((current) =>

                          current.filter((_, i) => i !== index)

                        )

                      }

                    >

                      <Trash2 size={15} />

                    </button>

                  </div>

                  <div className="db-form-field">

                    <label>Requirement ID</label>

                    <input

                      value={requirement.requirement_id}

                      onChange={(event) =>

                        updateRequirement(

                          index,

                          "requirement_id",

                          event.target.value

                        )

                      }

                    />

                  </div>

                  <div className="db-form-field">

                    <label>Requirement Statement</label>

                    <textarea

                      rows={3}

                      value={requirement.requirement_text}

                      onChange={(event) =>

                        updateRequirement(

                          index,

                          "requirement_text",

                          event.target.value

                        )

                      }

                    />

                  </div>

                  <div className="db-requirement-bottom">

                    <select

                      aria-label="Requirement type"

                      value={requirement.requirement_type}

                      onChange={(event) =>

                        updateRequirement(

                          index,

                          "requirement_type",

                          event.target.value

                        )

                      }

                    >

                      <option value="functional">Functional</option>

                      <option value="non-functional">Non-functional</option>

                    </select>

                    <label className="db-checkbox">

                      <input

                        type="checkbox"

                        checked={requirement.database_relevant}

                        onChange={(event) =>

                          updateRequirement(

                            index,

                            "database_relevant",

                            event.target.checked

                          )

                        }

                      />

                      DB relevant

                    </label>

                  </div>

                </div>

              ))}

              <button className="db-add-button" onClick={addRequirement}>

                <Plus size={16} />

                Add Requirement

              </button>

              <div className="db-section-heading">

                <div>

                  <h3>Architecture Context</h3>

                  <small>Technical design constraints</small>

                </div>

              </div>

              <div className="db-form-field">

                <label>Architecture Style</label>

                <select

                  value={architectureStyle}

                  onChange={(event) =>

                    setArchitectureStyle(event.target.value)

                  }

                >

                  <option value="Layered">Layered</option>

                  <option value="Monolithic">Monolithic</option>

                  <option value="Microservices">Microservices</option>

                  <option value="Event-driven">Event-driven</option>

                </select>

              </div>

              <div className="db-form-field">

                <label>Database Type</label>

                <select

                  value={databaseType}

                  onChange={(event) =>

                    setDatabaseType(event.target.value)

                  }

                >

                  <option value="Relational">Relational</option>

                </select>

              </div>

              <div className="db-form-field">

                <label>Database Constraints</label>

                <textarea

                  rows={5}

                  value={constraints}

                  onChange={(event) =>

                    setConstraints(event.target.value)

                  }

                  placeholder="One constraint per line"

                />

              </div>

              {error && (

                <div className="db-error-box" role="alert">

                  <CircleAlert size={18} />

                  <span>{error}</span>

                </div>

              )}

              <button

                className="db-generate-button"

                onClick={handleGenerate}

                disabled={isGenerating}

              >

                {isGenerating ? (

                  <>

                    <LoaderCircle size={18} className="db-spin" />

                    Generating Design...

                  </>

                ) : (

                  <>

                    <Sparkles size={18} />

                    Generate Database Design

                    <ArrowRight size={17} />

                  </>

                )}

              </button>

              {/* <p className="db-input-footnote">

                Uses your existing FastAPI database generation pipeline.

              </p> */}

            </div>

          </section>

        )}

        <section className="db-surface db-output-section">

          <div className="db-surface-heading db-output-heading">

            <div>

              <span className="db-small-label">02 / GENERATED OUTPUT</span>

              <h2>Database Blueprint</h2>

              <p>Explore schema structure and requirement coverage.</p>

            </div>

            {result && (

              <span

                className={`db-validation-pill ${

                  result.overall_valid ? "passed" : "failed"

                }`}

              >

                {result.overall_valid ? (

                  <CheckCircle2 size={15} />

                ) : (

                  <CircleAlert size={15} />

                )}

                {result.overall_valid

                  ? "Backend checks passed"

                  : "Checks need review"}

              </span>

            )}

          </div>

          {!result && !isGenerating && (

            <div className="db-empty-output">

              <div className="db-empty-art">

                <Database size={45} strokeWidth={1.4} />

              </div>

              <span className="db-small-label">YOUR DATABASE BLUEPRINT</span>

              <h3>From requirements to a relational design.</h3>

              <p>

                Use the input panel to generate your first schema.

                The ER diagram, tables, relationships, and validation

                results will appear here.

              </p>

              <div className="db-empty-flow">

                <span>Requirements</span>

                <ArrowRight size={14} />

                <span>Database Schema</span>

                <ArrowRight size={14} />

                <span>Validation</span>

              </div>

            </div>

          )}

          {isGenerating && (

            <div className="db-empty-output">

              <LoaderCircle size={44} className="db-spin db-loading-icon" />

              <h3>Generating your database blueprint</h3>

              <p>

                Extracting concepts, generating tables with Gemini,

                checking the design, and creating artifacts.

              </p>

            </div>

          )}

          {result && !isGenerating && (

            <div className="db-output-content">

              <div className="db-output-topline">

                <div>

                  <h3>{projectName}</h3>

                  <p>{result.project_id} · Generated draft</p>

                </div>

                <div className="db-output-tools">

                  <button

                    className="db-icon-text-button"

                    onClick={exportMermaid}

                  >

                    <Download size={15} />

                    Mermaid

                  </button>

                  <button

                    className="db-icon-text-button"

                    onClick={exportJSON}

                  >

                    <FileJson size={15} />

                    JSON

                  </button>

                </div>

              </div>

              {hasLocalEdits && (

                <div className="db-edit-warning">

                  <CircleAlert size={17} />

                  Local edits are not revalidated. Regenerate to

                  obtain a new backend-validated design.

                </div>

              )}

              <div className="db-tab-bar">

                {TABS.map((tab) => {

                  const Icon = tab.icon;

                  return (

                    <button

                      key={tab.id}

                      className={activeTab === tab.id ? "active" : ""}

                      onClick={() => setActiveTab(tab.id)}

                    >

                      <Icon size={15} />

                      {tab.label}

                    </button>

                  );

                })}

              </div>

              {activeTab === "diagram" && (

                <>

                  <div className="db-chen-switch" role="group" aria-label="ER diagram notation">
                    <button type="button" className={diagramType === "chen" ? "selected" : ""} onClick={() => setDiagramType("chen")}>Chen ER Diagram (Conceptual)</button>
                    <button type="button" className={diagramType === "crow" ? "selected" : ""} onClick={() => setDiagramType("crow")}>Crow’s Foot ER Diagram (Logical)</button>
                  </div>
                  {diagramType === "chen" ? <ChenDiagram design={draftDesign} projectId={result?.project_id} /> : <MermaidDiagram definition={diagramDefinition} />}

                  <div className="db-metrics">

                    <Metric

                      icon={Database}

                      value={tables.length}

                      label="Tables"

                      tone="green"

                    />

                    <Metric

                      icon={GitBranch}

                      value={relationships.length}

                      label="Relationships"

                      tone="purple"

                    />

                    <Metric

                      icon={ShieldCheck}

                      value={`${mapping?.coverage_percentage ?? 0}%`}

                      label="Requirement Coverage"

                      tone="blue"

                    />

                    <Metric

                      icon={Layers3}

                      value={tables.reduce(

                        (sum, table) =>

                          sum + (table.columns?.length || 0),

                        0

                      )}

                      label="Columns"

                      tone="orange"

                    />

                  </div>

                  <div className="db-quality-panel">

                    <div className="db-quality-heading">

                      <ShieldCheck size={18} />

                      <strong>Design Quality Checks</strong>

                    </div>

                    <div className="db-quality-item">

                      {validation?.valid ? (

                        <CheckCircle2 size={16} />

                      ) : (

                        <CircleAlert size={16} />

                      )}

                      <span>

                        Structural schema validation:{" "}

                        {validation?.valid ? "passed" : "failed"}

                      </span>

                    </div>

                    <div className="db-quality-item">

                      {mapping?.valid ? (

                        <CheckCircle2 size={16} />

                      ) : (

                        <CircleAlert size={16} />

                      )}

                      <span>

                        Requirement mapping validation:{" "}

                        {mapping?.valid ? "passed" : "failed"}

                      </span>

                    </div>

                    <div className="db-quality-item">

                      <CircleAlert size={16} className="db-info-icon" />

                      <span>

                        Human review is still required before approval.

                      </span>

                    </div>

                  </div>

                  <div className="db-inspector-panel">

                    <div className="db-inspector-heading">

                      <div>

                        <span className="db-small-label">TABLE PROPERTIES</span>

                        <h3>Inspect a Generated Table</h3>

                      </div>

                      <ChevronDown size={18} />

                    </div>

                    <select

                      className="db-table-picker"

                      value={selectedTableIndex}

                      onChange={(event) =>

                        setSelectedTableIndex(Number(event.target.value))

                      }

                    >

                      {tables.map((table, index) => (

                        <option key={index} value={index}>

                          {table.table_name}

                        </option>

                      ))}

                    </select>

                    <TableInspector

                      table={selectedTable}

                      onUpdate={updateSelectedTable}

                    />

                  </div>

                </>

              )}

              {activeTab === "schema" && (

                <div className="db-tab-panel">

                  <div className="db-tab-heading">

                    <div>

                      <h3>Generated Tables</h3>

                      <p>Explore the logical relational schema.</p>

                    </div>

                    <div className="db-search">

                      <Search size={16} />

                      <input

                        value={search}

                        onChange={(event) =>

                          setSearch(event.target.value)

                        }

                        placeholder="Search tables"

                      />

                    </div>

                  </div>

                  <div className="db-schema-grid">

                    {filteredTables.map((table) => {

                      const index = tables.indexOf(table);

                      return (

                        <SchemaTable

                          key={index}

                          table={table}

                          selected={index === selectedTableIndex}

                          onSelect={() => {

                            setSelectedTableIndex(index);

                            setActiveTab("diagram");

                          }}

                        />

                      );

                    })}

                  </div>

                </div>

              )}

              {activeTab === "relationships" && (

                <div className="db-tab-panel">

                  <div className="db-tab-heading">

                    <div>

                      <h3>Database Relationships</h3>

                      <p>Foreign key connections between tables.</p>

                    </div>

                  </div>

                  {relationships.length === 0 && (

                    <p>No relationships were generated.</p>

                  )}

                  {relationships.map((relationship, index) => (

                    <div className="db-relationship-row" key={index}>

                      <div className="db-relationship-symbol">

                        <GitBranch size={18} />

                      </div>

                      <div className="db-relationship-info">

                        <strong>

                          {relationship.from_table}

                          <ArrowRight size={15} />

                          {relationship.to_table}

                        </strong>

                        <small>{relationship.foreign_key}</small>

                      </div>

                      <span>{relationship.relationship_type}</span>

                    </div>

                  ))}

                </div>

              )}

              {activeTab === "traceability" && (

                <div className="db-tab-panel">

                  <div className="db-tab-heading">

                    <div>

                      <h3>Requirement Traceability</h3>

                      <p>

                        Mappings produced and checked by your backend.

                      </p>

                    </div>

                  </div>

                  <div className="db-coverage-highlight">

                    <strong>

                      {mapping?.coverage_percentage ?? 0}%

                    </strong>

                    <span>Reported requirement coverage</span>

                  </div>

                  {(mapping?.requirement_mappings || []).map(

                    (item, index) => (

                      <div className="db-mapping-item" key={index}>

                        <strong>{item.requirement_id}</strong>

                        <div>

                          {(item.related_tables || []).map((table) => (

                            <span key={table}>{table}</span>

                          ))}

                          {!item.related_tables?.length && (

                            <em>No related tables</em>

                          )}

                        </div>

                      </div>

                    )

                  )}

                </div>

              )}

              {activeTab === "validation" && (

                <div className="db-tab-panel">

                  <div className="db-tab-heading">

                    <div>

                      <h3>Validation Report</h3>

                      <p>

                        Deterministic checks returned by the backend.

                      </p>

                    </div>

                  </div>

                  <div className="db-validation-line">

                    <span>Schema validation</span>

                    <strong>

                      {validation?.valid ? "Passed" : "Failed"}

                    </strong>

                  </div>

                  <div className="db-validation-line">

                    <span>Mapping validation</span>

                    <strong>

                      {mapping?.valid ? "Passed" : "Failed"}

                    </strong>

                  </div>

                  <div className="db-validation-line">

                    <span>Overall validation</span>

                    <strong>

                      {result.overall_valid ? "Passed" : "Failed"}

                    </strong>

                  </div>

                  {[

                    ...(validation?.errors || []),

                    ...(mapping?.errors || []),

                  ].map((item, index) => (

                    <div className="db-error-box" key={`e-${index}`}>

                      <CircleAlert size={16} />

                      {String(item)}

                    </div>

                  ))}

                  {[

                    ...(validation?.warnings || []),

                    ...(mapping?.warnings || []),

                  ].map((item, index) => (

                    <div className="db-edit-warning" key={`w-${index}`}>

                      <CircleAlert size={16} />

                      {String(item)}

                    </div>

                  ))}

                  <div className="db-artifact-info">

                    <FileText size={19} />

                    <div>

                      <strong>Generated backend files</strong>

                      <p>

                        SQL: {result.artifacts?.sql_file || "Unavailable"}

                      </p>

                      <p>

                        ER: {result.artifacts?.er_diagram_file || "Unavailable"}

                      </p>

                      <small>

                        These are server file paths, not browser

                        download links.

                      </small>

                    </div>

                  </div>

                </div>

              )}

              {activeTab === "sql" && (
                <div className="db-tab-panel">
                  <div className="db-tab-heading">
                    <div>
                      <h3>SQL Preview</h3>
                      <p>Actual PostgreSQL SQL generated by the backend.</p>
                    </div>
                    {sqlContent && (
                      <button
                        type="button"
                        className="db-regenerate-button"
                        onClick={() =>
                          downloadFile(
                            `${result.project_id}_database_design.sql`,
                            sqlContent,
                            "application/sql"
                          )
                        }
                      >
                        <Download size={16} /> Download SQL
                      </button>
                    )}
                  </div>
                  {sqlLoading && <p>Loading generated SQL...</p>}
                  {sqlError && (
                    <div role="alert" style={{ color: "#b42318", padding: 16 }}>
                      {sqlError}
                    </div>
                  )}
                  {!sqlLoading && !sqlError && sqlContent && (
                    <pre style={{
                      overflowX: "auto",
                      padding: 20,
                      border: "1px solid #dce7df",
                      borderRadius: 10,
                      background: "#f7faf8",
                      color: "#163c30",
                      fontSize: 13,
                      lineHeight: 1.6,
                      whiteSpace: "pre",
                    }}><code>{sqlContent}</code></pre>
                  )}
                  {!sqlLoading && !sqlError && !sqlContent && (
                    <p>No SQL content was returned for this project.</p>
                  )}
                </div>
              )}

              <div className="db-output-footer">

                <div>

                  <strong>Generated design draft</strong>

                  <p>

                    {hasLocalEdits

                      ? "Modified locally — validation is no longer current."

                      : "Ready for manual review. Not Coordinator-approved."}

                  </p>

                </div>

                <button

                  className="db-regenerate-button"

                  onClick={() => {

                    setShowInputs(true);

                    window.scrollTo({

                      top: 0,

                      behavior: "smooth",

                    });

                  }}

                >

                  <RefreshCw size={15} />

                  Edit Inputs / Regenerate

                </button>

              </div>

            </div>

          )}

        </section>

      </div>

      <footer className="db-page-footer">

        <span>DesignTrace AI · Database Design Module</span>

        {/* <span>Standalone research demonstration</span> */}

      </footer>

    </div>

  );

}
