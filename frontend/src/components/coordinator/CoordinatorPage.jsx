import { useState } from 'react'
import { coordinatorApi } from '../../services/coordinatorApi'

const MODULES = [
  ['requirement_analysis', 'Requirement Analysis'],
  ['architecture_design', 'Architecture Design'],
  ['database_design', 'Database Design'],
  ['api_component_design', 'API & Component Design'],
  ['traceability', 'Traceability'],
  ['quality_evaluation', 'Quality Evaluation'],
  ['adr', 'Architecture Decision Records'],
]

const initialProject = {
  project_id: '',
  project_name: '',
  project_description: '',
  project_domain: 'Healthcare',
  system_type: 'Web Application',
  expected_users: '',
  constraints: '',
  database: 'PostgreSQL',
  backend: 'Python (FastAPI)',
  frontend: 'React',
  deployment: 'Cloud',
  cloud_provider: 'AWS',
  region: 'ap-south-1',
  notes: '',
}

const examples = {
  hospital: {
    project_id: 'HOSPITAL-001',
    project_name: 'Hospital Management System',
    project_description:
      'A web-based hospital management system for patients, appointments, doctors, staff, and billing.',
    project_domain: 'Healthcare',
    system_type: 'Web Application',
    expected_users: 'Patients, Doctors, Administrators, Receptionists',
    constraints:
      'Only authorized staff can access sensitive patient information.\nPatient records must be protected.\nThe system should support future growth.\nThe system should be available 24/7.',
    database: 'PostgreSQL',
    backend: 'Python (FastAPI)',
    frontend: 'React',
    deployment: 'Cloud',
    cloud_provider: 'AWS',
    region: 'ap-south-1',
    notes: 'Support appointment scheduling and patient history.',
    requirements: [
      'The system shall store patient details.',
      'Patients shall book appointments with doctors.',
      'Doctors shall view their scheduled appointments.',
      'Only authorized staff shall access patient records.',
      'The system shall record appointment status.',
    ],
  },
  library: {
    project_id: 'MOCK-LIBRARY-001',
    project_name: 'Library Management System',
    project_description:
      'A system for managing books, members and borrowing records.',
    project_domain: 'Education',
    system_type: 'Web Application',
    expected_users: 'Librarians, Members, Administrators',
    constraints:
      'Each borrowing record must reference an existing book and member.\nBooks must have unique identifiers.\nOnly authorized librarians can manage borrowing records.',
    database: 'PostgreSQL',
    backend: 'Python (FastAPI)',
    frontend: 'React',
    deployment: 'Cloud',
    cloud_provider: 'AWS',
    region: 'ap-south-1',
    notes: 'PP1 Coordinator demonstration project.',
    requirements: [
      'The system shall store book details.',
      'Members shall borrow books.',
      'Each borrowing record shall reference a book and a member.',
    ],
  },
  banking: {
    project_id: 'BANKING-001',
    project_name: 'Bank Account Management System',
    project_description:
      'A secure banking application for customer accounts and transfers.',
    project_domain: 'Finance',
    system_type: 'Web Application',
    expected_users: 'Customers, Bank Staff, Administrators',
    constraints:
      'Account balances must not become negative.\nEvery transfer must be recorded.\nCustomers must authenticate before accessing their accounts.',
    database: 'PostgreSQL',
    backend: 'Python (FastAPI)',
    frontend: 'React',
    deployment: 'Cloud',
    cloud_provider: 'AWS',
    region: 'ap-south-1',
    notes: 'Example for testing requirement traceability.',
    requirements: [
      'A customer shall create a bank account.',
      'A customer shall view their bank account.',
      'A customer shall transfer money between accounts.',
      'The system shall record every transaction.',
    ],
  },
}

function Field({ label, required, children }) {
  return (
    <label className="dt-field">
      <span className="dt-field-label">
        {label} {required && <span className="dt-required">*</span>}
      </span>
      {children}
    </label>
  )
}

function StatusPill({ status }) {
  const normalized = String(status || 'PENDING').toUpperCase()

  return (
    <span className={`dt-status dt-status-${normalized.toLowerCase()}`}>
      {normalized.replaceAll('_', ' ')}
    </span>
  )
}

function prettyJson(value) {
  return JSON.stringify(value, null, 2)
}

function getInterrupt(data) {
  if (!data) return null

  if (data.interrupt) return data.interrupt
  if (data.pending_review) return data.pending_review
  if (data.review_required) {
    return typeof data.review_required === 'object'
      ? data.review_required
      : data
  }

  if (Array.isArray(data.__interrupt__) && data.__interrupt__.length) {
    return data.__interrupt__[0].value || data.__interrupt__[0]
  }

  return null
}

function getThreadId(data) {
  return data?.thread_id || data?.threadId || data?.configurable?.thread_id
}

function getWorkflowStatus(data) {
  return (
    data?.workflow_status ||
    data?.status ||
    data?.report?.workflow_status ||
    'PENDING'
  )
}

function extractModules(data) {
  return (
    data?.module_statuses ||
    data?.module_states ||
    data?.report?.module_statuses ||
    data?.report?.module_states ||
    {}
  )
}

export default function CoordinatorPage() {
  const [theme, setTheme] = useState(
    () => localStorage.getItem('designtrace-theme') || 'dark'
  )
  const [section, setSection] = useState('create')
  const [step, setStep] = useState(1)
  const [project, setProject] = useState(initialProject)
  const [requirements, setRequirements] = useState([''])
  const [example, setExample] = useState('hospital')
  const [threadId, setThreadId] = useState('')
  const [workflow, setWorkflow] = useState(null)
  const [pendingReview, setPendingReview] = useState(null)
  const [feedback, setFeedback] = useState('')
  const [finalReport, setFinalReport] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const isDark = theme === 'dark'

  function toggleTheme() {
    const next = isDark ? 'light' : 'dark'
    setTheme(next)
    localStorage.setItem('designtrace-theme', next)
  }

  function updateProject(key, value) {
    setProject((current) => ({ ...current, [key]: value }))
  }

  function loadExample(name = example) {
    const selected = examples[name]
    if (!selected) return

    const { requirements: sampleRequirements, ...projectFields } = selected
    setProject(projectFields)
    setRequirements(sampleRequirements)
    setExample(name)
    setStep(1)
    setSection('create')
    setError('')
    setNotice(`${selected.project_name} example loaded.`)
  }

  function saveDraft() {
    localStorage.setItem(
      'designtrace-project-draft',
      JSON.stringify({ project, requirements })
    )
    setNotice('Project draft saved in this browser.')
  }

  function loadDraft() {
    const raw = localStorage.getItem('designtrace-project-draft')
    if (!raw) {
      setNotice('No saved draft found.')
      return
    }

    try {
      const saved = JSON.parse(raw)
      setProject(saved.project || initialProject)
      setRequirements(saved.requirements || [''])
      setNotice('Saved draft restored.')
    } catch {
      setError('The saved draft could not be read.')
    }
  }

  function validateStep() {
    if (step === 1) {
      if (
        !project.project_name.trim() ||
        !project.project_description.trim() ||
        !project.project_id.trim()
      ) {
        setError('Enter the project ID, name and description.')
        return false
      }
    }

    if (step === 2 && !requirements.some((r) => r.trim())) {
      setError('Enter at least one functional requirement.')
      return false
    }

    setError('')
    return true
  }

  function nextStep() {
    if (validateStep()) setStep((current) => Math.min(3, current + 1))
  }

  function buildProjectPayload() {
    return {
      project_id: project.project_id,
      project_name: project.project_name,
      project_description: project.project_description,
      requirements: requirements
        .filter((text) => text.trim())
        .map((text, index) => ({
          requirement_id: `REQ-${String(index + 1).padStart(3, '0')}`,
          requirement_text: text.trim(),
        })),
    }
  }

  // The Coordinator's PP1 mock start endpoint may accept only
  // a fixed demo project. This payload is prepared for the
  // future real-project API contract.
  async function startWorkflow() {
    if (!validateStep()) return

    setBusy(true)
    setError('')
    setNotice('')

    try {
      const data = await coordinatorApi.start(buildProjectPayload())
      const id = getThreadId(data)

      if (!id) {
        throw new Error(
          'The start endpoint did not return a thread_id. Check its response schema.'
        )
      }

      setThreadId(id)
      setWorkflow(data)
      setPendingReview(getInterrupt(data))
      setFinalReport(null)
      setSection('workspace')
      setNotice('Coordinator workflow started.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function refreshWorkflow() {
    if (!threadId) return

    setBusy(true)
    setError('')

    try {
      const data = await coordinatorApi.status(threadId)
      setWorkflow(data)
      setPendingReview(getInterrupt(data))

      if (getWorkflowStatus(data).toUpperCase() === 'COMPLETED') {
        setNotice('Workflow completed. You can open the final report.')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function submitReview(decision) {
    if (!threadId) return

    if (decision === 'reject' && !feedback.trim()) {
      setError('Please enter feedback before rejecting this output.')
      return
    }

    setBusy(true)
    setError('')

    try {
      const data = await coordinatorApi.review(
        threadId,
        decision,
        feedback.trim()
      )

      setWorkflow(data)
      setPendingReview(getInterrupt(data))
      setFeedback('')
      setNotice(
        decision === 'approve'
          ? 'Review approved. The Coordinator has resumed.'
          : 'Review rejected. Feedback submitted to the Coordinator.'
      )

      // Read the latest checkpoint in case the review response
      // contains only an acknowledgement.
      const latest = await coordinatorApi.status(threadId)
      setWorkflow(latest)
      setPendingReview(getInterrupt(latest))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function openReport() {
    if (!threadId) {
      setError('Start a workflow before opening its report.')
      return
    }

    setBusy(true)
    setError('')

    try {
      const data = await coordinatorApi.report(threadId)
      setFinalReport(data)
      setSection('report')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function downloadReport() {
    if (!finalReport) return

    const content = prettyJson(finalReport)
    const blob = new Blob([content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')

    anchor.href = url
    anchor.download = `${project.project_id || 'designtrace'}_report.json`
    anchor.click()

    URL.revokeObjectURL(url)
  }

  const moduleStates = extractModules(workflow)
  const status = getWorkflowStatus(workflow)
  const reviewModule =
    pendingReview?.module_name ||
    pendingReview?.module ||
    pendingReview?.name ||
    'Module review'

  return (
    <div className={`dt-app ${isDark ? 'dt-dark' : 'dt-light'}`}>
      <aside className="dt-sidebar">
        <div className="dt-brand">
          <span className="dt-brand-icon">⌘</span>
          <span>DesignTrace <b>AI</b></span>
        </div>

        <div className="dt-sidebar-caption">DESIGN WORKSPACE</div>

        <nav className="dt-navigation">
          {[
            ['dashboard', '▦', 'Dashboard'],
            ['projects', '▤', 'Projects'],
            ['create', '✚', 'Create New Project'],
            ['workspace', '◇', 'Coordinator Agent'],
            ['requirements', '☷', 'Requirements'],
            ['architecture', '⬡', 'Architecture Design'],
            ['database', '▤', 'Database Design'],
            ['api', '⌘', 'API & Component Design'],
            ['traceability', '⑂', 'Traceability'],
            ['quality', '✺', 'Quality Evaluation'],
            ['adr', '▣', 'ADR Records'],
            ['report', '▥', 'Reports'],
          ].map(([key, symbol, title]) => (
            <button
              key={key}
              type="button"
              className={`dt-nav-item ${section === key ? 'active' : ''}`}
              onClick={() => {
                if (key === 'create' || key === 'workspace' || key === 'report') {
                  setSection(key)
                } else {
                  setNotice(
                    `${title} belongs to the shared DesignTrace AI frontend. Its route can be connected when that page is integrated.`
                  )
                }
              }}
            >
              <span className="dt-nav-symbol">{symbol}</span>
              {title}
            </button>
          ))}
        </nav>

        <div className="dt-sidebar-bottom">
          <div className="dt-user">
            <span className="dt-avatar">D</span>
            <div>
              <strong>Demo User</strong>
              <small>Coordinator Workspace</small>
            </div>
          </div>

          <button className="dt-theme-switch" onClick={toggleTheme}>
            <span>{isDark ? 'Dark Mode' : 'Light Mode'}</span>
            <span className="dt-switch-track">
              <span className="dt-switch-thumb" />
            </span>
          </button>
        </div>
      </aside>

      <main className="dt-main">
        {section === 'create' && (
          <>
            <header className="dt-page-header">
              <div>
                <div className="dt-breadcrumb">Design workspace / Projects / New</div>
                <h1>Create New Project</h1>
                <p>Provide basic information about your project to get started.</p>
              </div>

              <div className="dt-steps">
                {['Project Info', 'Requirements', 'Review & Start'].map(
                  (label, index) => (
                    <div
                      key={label}
                      className={`dt-step ${step === index + 1 ? 'current' : ''} ${
                        step > index + 1 ? 'done' : ''
                      }`}
                    >
                      <span>{index + 1}</span>
                      <small>{label}</small>
                    </div>
                  )
                )}
              </div>
            </header>

            <div className="dt-content">
              <div className="dt-top-tools">
                <span className="dt-eyebrow">PROJECT SETUP</span>
                <div className="dt-inline-actions">
                  <select
                    aria-label="Choose example project"
                    value={example}
                    onChange={(event) => setExample(event.target.value)}
                  >
                    <option value="hospital">Hospital example</option>
                    <option value="library">Library example</option>
                    <option value="banking">Banking example</option>
                  </select>
                  <button className="dt-button dt-button-outline" onClick={() => loadExample()}>
                    ✧ Load Example
                  </button>
                  <button className="dt-button dt-button-ghost" onClick={loadDraft}>
                    Restore Draft
                  </button>
                </div>
              </div>

              {step === 1 && (
                <section className="dt-panel">
                  <div className="dt-section-heading">
                    <span className="dt-section-icon">ⓘ</span>
                    <h2>Project Information</h2>
                  </div>

                  <div className="dt-form-grid">
                    <Field label="Project Name" required>
                      <input
                        value={project.project_name}
                        onChange={(e) => updateProject('project_name', e.target.value)}
                        placeholder="Hospital Management System"
                      />
                    </Field>

                    <Field label="Project Domain" required>
                      <select
                        value={project.project_domain}
                        onChange={(e) => updateProject('project_domain', e.target.value)}
                      >
                        {['Healthcare', 'Education', 'Finance', 'E-commerce', 'Other'].map(
                          (item) => <option key={item}>{item}</option>
                        )}
                      </select>
                    </Field>

                    <Field label="Project ID" required>
                      <input
                        value={project.project_id}
                        onChange={(e) => updateProject('project_id', e.target.value)}
                        placeholder="HOSPITAL-001"
                      />
                    </Field>

                    <Field label="System Type" required>
                      <select
                        value={project.system_type}
                        onChange={(e) => updateProject('system_type', e.target.value)}
                      >
                        {['Web Application', 'Mobile Application', 'Desktop Application', 'API Service'].map(
                          (item) => <option key={item}>{item}</option>
                        )}
                      </select>
                    </Field>

                    <Field label="Project Description" required>
                      <textarea
                        rows={3}
                        value={project.project_description}
                        onChange={(e) => updateProject('project_description', e.target.value)}
                        placeholder="Describe your software system..."
                      />
                    </Field>

                    <Field label="Expected Users">
                      <textarea
                        rows={3}
                        value={project.expected_users}
                        onChange={(e) => updateProject('expected_users', e.target.value)}
                        placeholder="Patients, Doctors, Administrators..."
                      />
                    </Field>
                  </div>

                  <div className="dt-divider" />

                  <div className="dt-section-heading">
                    <span className="dt-section-icon">⬡</span>
                    <h2>Project Constraints</h2>
                  </div>
                  <p className="dt-help">
                    Define key constraints and assumptions for the project.
                  </p>
                  <textarea
                    rows={5}
                    value={project.constraints}
                    onChange={(e) => updateProject('constraints', e.target.value)}
                    placeholder="Enter privacy, security, scalability and availability constraints..."
                  />

                  <div className="dt-divider" />

                  <div className="dt-preference-grid">
                    <div>
                      <div className="dt-section-heading">
                        <span className="dt-section-icon">⌘</span>
                        <h2>Technology Preferences</h2>
                      </div>

                      <Field label="Database">
                        <select
                          value={project.database}
                          onChange={(e) => updateProject('database', e.target.value)}
                        >
                          {['PostgreSQL', 'MySQL', 'SQLite', 'MongoDB'].map(
                            (item) => <option key={item}>{item}</option>
                          )}
                        </select>
                      </Field>

                      <Field label="Backend">
                        <select
                          value={project.backend}
                          onChange={(e) => updateProject('backend', e.target.value)}
                        >
                          {['Python (FastAPI)', 'Python (Django)', 'Node.js', 'Java (Spring Boot)'].map(
                            (item) => <option key={item}>{item}</option>
                          )}
                        </select>
                      </Field>

                      <Field label="Frontend">
                        <select
                          value={project.frontend}
                          onChange={(e) => updateProject('frontend', e.target.value)}
                        >
                          {['React', 'Vue', 'Angular', 'HTML/CSS'].map(
                            (item) => <option key={item}>{item}</option>
                          )}
                        </select>
                      </Field>
                    </div>

                    <div>
                      <div className="dt-section-heading">
                        <span className="dt-section-icon">☁</span>
                        <h2>Deployment Preference</h2>
                      </div>

                      <Field label="Deployment Type">
                        <select
                          value={project.deployment}
                          onChange={(e) => updateProject('deployment', e.target.value)}
                        >
                          {['Cloud', 'On-Premise', 'Hybrid'].map(
                            (item) => <option key={item}>{item}</option>
                          )}
                        </select>
                      </Field>

                      <Field label="Cloud Provider">
                        <select
                          value={project.cloud_provider}
                          onChange={(e) => updateProject('cloud_provider', e.target.value)}
                        >
                          {['AWS', 'Azure', 'Google Cloud', 'Other'].map(
                            (item) => <option key={item}>{item}</option>
                          )}
                        </select>
                      </Field>

                      <Field label="Region">
                        <input
                          value={project.region}
                          onChange={(e) => updateProject('region', e.target.value)}
                        />
                      </Field>
                    </div>

                    <div>
                      <div className="dt-section-heading">
                        <span className="dt-section-icon">⊙</span>
                        <h2>Additional Notes</h2>
                      </div>
                      <Field label="Optional">
                        <textarea
                          rows={10}
                          value={project.notes}
                          onChange={(e) => updateProject('notes', e.target.value)}
                          placeholder="Add any additional information or special requirements..."
                        />
                      </Field>
                    </div>
                  </div>
                </section>
              )}

              {step === 2 && (
                <section className="dt-panel">
                  <div className="dt-section-heading">
                    <span className="dt-section-icon">☷</span>
                    <h2>Functional Requirements</h2>
                  </div>
                  <p className="dt-help">
                    Enter one requirement per field. Each will receive a requirement ID.
                  </p>

                  {requirements.map((text, index) => (
                    <div className="dt-requirement" key={index}>
                      <span className="dt-requirement-id">
                        REQ-{String(index + 1).padStart(3, '0')}
                      </span>
                      <textarea
                        rows={2}
                        value={text}
                        onChange={(e) => {
                          const next = [...requirements]
                          next[index] = e.target.value
                          setRequirements(next)
                        }}
                        placeholder="The system shall..."
                      />
                      <button
                        className="dt-icon-button"
                        title="Remove requirement"
                        onClick={() =>
                          setRequirements((current) =>
                            current.length > 1
                              ? current.filter((_, i) => i !== index)
                              : ['']
                          )
                        }
                      >
                        ×
                      </button>
                    </div>
                  ))}

                  <button
                    className="dt-button dt-button-outline"
                    onClick={() => setRequirements((current) => [...current, ''])}
                  >
                    + Add Requirement
                  </button>

                  <div className="dt-info-note">
                    Your requirements will be passed to the Coordinator when the
                    backend supports dynamic project input.
                  </div>
                </section>
              )}

              {step === 3 && (
                <section className="dt-panel">
                  <div className="dt-section-heading">
                    <span className="dt-section-icon">✓</span>
                    <h2>Review Project Details</h2>
                  </div>

                  <div className="dt-review-grid">
                    <div className="dt-summary-box">
                      <small>PROJECT</small>
                      <strong>{project.project_name}</strong>
                      <span>{project.project_id}</span>
                    </div>
                    <div className="dt-summary-box">
                      <small>DOMAIN</small>
                      <strong>{project.project_domain}</strong>
                      <span>{project.system_type}</span>
                    </div>
                    <div className="dt-summary-box">
                      <small>REQUIREMENTS</small>
                      <strong>{requirements.filter((r) => r.trim()).length}</strong>
                      <span>Functional requirements</span>
                    </div>
                    <div className="dt-summary-box">
                      <small>DATABASE</small>
                      <strong>{project.database}</strong>
                      <span>{project.backend}</span>
                    </div>
                  </div>

                  <h3>Project Description</h3>
                  <p>{project.project_description}</p>

                  <h3>Requirements</h3>
                  <div className="dt-requirement-list">
                    {requirements.filter((r) => r.trim()).map((text, index) => (
                      <div key={index}>
                        <span className="dt-requirement-id">
                          REQ-{String(index + 1).padStart(3, '0')}
                        </span>
                        <span>{text}</span>
                      </div>
                    ))}
                  </div>

                  <div className="dt-info-note">
                    <strong>PP1 integration note:</strong> The current Coordinator
                    uses mock Module outputs. If the start endpoint uses the fixed
                    library demo, the resulting report may describe the library
                    example even when another project is entered here.
                  </div>
                </section>
              )}

              {error && <div className="dt-alert dt-alert-error">{error}</div>}
              {notice && <div className="dt-alert dt-alert-info">{notice}</div>}

              <div className="dt-form-footer">
                <button
                  className="dt-button dt-button-ghost"
                  onClick={() => {
                    if (step > 1) setStep(step - 1)
                    else setProject(initialProject)
                  }}
                >
                  {step === 1 ? 'Cancel / Reset' : '← Back'}
                </button>

                <div className="dt-inline-actions">
                  <button className="dt-button dt-button-outline" onClick={saveDraft}>
                    ▣ Save Draft
                  </button>

                  {step < 3 ? (
                    <button className="dt-button dt-button-primary" onClick={nextStep}>
                      Next: {step === 1 ? 'Requirements' : 'Review'} →
                    </button>
                  ) : (
                    <button
                      className="dt-button dt-button-primary"
                      disabled={busy}
                      onClick={startWorkflow}
                    >
                      {busy ? 'Starting...' : '▶ Start Coordinator'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        {section === 'workspace' && (
          <>
            <header className="dt-page-header">
              <div>
                <div className="dt-breadcrumb">Design workspace / Coordinator Agent</div>
                <h1>Coordinator Agent</h1>
                <p>LangGraph workflow orchestration and human-in-the-loop review.</p>
              </div>
              <div className="dt-inline-actions">
                <button className="dt-button dt-button-outline" onClick={refreshWorkflow} disabled={busy || !threadId}>
                  ↻ Refresh
                </button>
                <button className="dt-button dt-button-primary" onClick={openReport} disabled={busy || !threadId}>
                  View Report →
                </button>
              </div>
            </header>

            <div className="dt-content">
              <div className="dt-workspace-banner">
                <div>
                  <span className="dt-eyebrow">PP1 MOCK DEMONSTRATION</span>
                  <h2>{project.project_name || 'Coordinator Workflow'}</h2>
                  <p>
                    Thread: <code>{threadId || 'Not started'}</code>
                  </p>
                </div>
                <StatusPill status={status} />
              </div>

              {pendingReview && (
                <section className="dt-panel dt-review-panel">
                  <div className="dt-section-heading">
                    <span className="dt-section-icon">◇</span>
                    <h2>Human Review Required</h2>
                  </div>

                  <p>
                    Review the generated output from <strong>{reviewModule}</strong>
                    {' '}before the Coordinator continues.
                  </p>

                  <div className="dt-review-meta">
                    <span>Version: {pendingReview.version || 1}</span>
                    <span>Project: {pendingReview.project_id || project.project_id}</span>
                  </div>

                  <h3>Generated Module Output</h3>
                  <pre className="dt-code-block">
                    {prettyJson(
                      pendingReview.output ||
                      pendingReview.artifacts ||
                      pendingReview
                    )}
                  </pre>

                  <Field label="Rejection feedback">
                    <textarea
                      rows={3}
                      value={feedback}
                      onChange={(e) => setFeedback(e.target.value)}
                      placeholder="Explain what should be corrected if you reject this output..."
                    />
                  </Field>

                  <div className="dt-inline-actions">
                    <button
                      className="dt-button dt-button-danger"
                      disabled={busy}
                      onClick={() => submitReview('reject')}
                    >
                      ✕ Reject & Request Revision
                    </button>
                    <button
                      className="dt-button dt-button-success"
                      disabled={busy}
                      onClick={() => submitReview('approve')}
                    >
                      ✓ Approve & Continue
                    </button>
                  </div>
                </section>
              )}

              {!pendingReview && !threadId && (
                <section className="dt-panel dt-empty-state">
                  <h2>No workflow started</h2>
                  <p>Create a project and start the Coordinator workflow.</p>
                  <button
                    className="dt-button dt-button-primary"
                    onClick={() => setSection('create')}
                  >
                    Create New Project
                  </button>
                </section>
              )}

              <section className="dt-panel">
                <div className="dt-section-heading">
                  <span className="dt-section-icon">⑂</span>
                  <h2>Module Execution Pipeline</h2>
                </div>

                <div className="dt-module-grid">
                  {MODULES.map(([key, label], index) => {
                    const moduleData = moduleStates[key]
                    const moduleStatus =
                      typeof moduleData === 'string'
                        ? moduleData
                        : moduleData?.status || 'PENDING'

                    return (
                      <div className="dt-module-card" key={key}>
                        <div className="dt-module-top">
                          <span className="dt-module-number">
                            {String(index + 1).padStart(2, '0')}
                          </span>
                          <StatusPill status={moduleStatus} />
                        </div>
                        <h3>{label}</h3>
                        <p>{key}</p>
                        <small>
                          Version: {moduleData?.version ?? '—'} ·
                          Retries: {moduleData?.retry_count ?? '—'}
                        </small>
                      </div>
                    )
                  })}
                </div>
              </section>

              <section className="dt-panel">
                <div className="dt-section-heading">
                  <span className="dt-section-icon">▤</span>
                  <h2>Workflow Details</h2>
                </div>
                <pre className="dt-code-block">
                  {prettyJson(workflow || { message: 'No workflow data yet.' })}
                </pre>
              </section>

              {error && <div className="dt-alert dt-alert-error">{error}</div>}
              {notice && <div className="dt-alert dt-alert-info">{notice}</div>}
            </div>
          </>
        )}

        {section === 'report' && (
          <>
            <header className="dt-page-header">
              <div>
                <div className="dt-breadcrumb">Design workspace / Reports</div>
                <h1>Final Software Design Report</h1>
                <p>Coordinator workflow results and approved artifacts.</p>
              </div>
              <div className="dt-inline-actions">
                <button className="dt-button dt-button-outline" onClick={openReport} disabled={busy}>
                  ↻ Reload Report
                </button>
                <button className="dt-button dt-button-primary" onClick={downloadReport} disabled={!finalReport}>
                  ↓ Export JSON
                </button>
              </div>
            </header>

            <div className="dt-content">
              <section className="dt-panel">
                <div className="dt-section-heading">
                  <span className="dt-section-icon">▥</span>
                  <h2>Execution Report</h2>
                </div>

                {finalReport ? (
                  <>
                    <div className="dt-report-summary">
                      <div>
                        <small>PROJECT</small>
                        <strong>
                          {finalReport.report?.project_name ||
                            project.project_name}
                        </strong>
                      </div>
                      <div>
                        <small>WORKFLOW STATUS</small>
                        <StatusPill status={getWorkflowStatus(finalReport)} />
                      </div>
                      <div>
                        <small>THREAD ID</small>
                        <code>{threadId}</code>
                      </div>
                    </div>

                    <h3>Report Data</h3>
                    <pre className="dt-code-block">
                      {prettyJson(finalReport.report || finalReport)}
                    </pre>
                  </>
                ) : (
                  <div className="dt-empty-state">
                    <p>Open the completed workflow report to view its contents.</p>
                    <button className="dt-button dt-button-primary" onClick={openReport} disabled={!threadId || busy}>
                      Load Final Report
                    </button>
                  </div>
                )}
              </section>

              {error && <div className="dt-alert dt-alert-error">{error}</div>}
            </div>
          </>
        )}
      </main>
    </div>
  )
}