import { useCallback, useEffect, useState } from 'react'
import { coordinatorApi } from '../../services/coordinatorApi'
import './CoordinatorPage.css'
import ModuleResultViewer from './ModuleResultViewer'
import './ModuleResultViewer.css'
import FinalReportViewer from './FinalReportViewer'

const MODULES = [
  ['requirement_analysis', 'Requirement Analysis'],
  ['architecture_design', 'Architecture Design'],
  ['database_design', 'Database Design'],
  ['api_component_design', 'API & Component Design'],
  ['traceability', 'Traceability'],
  ['quality_evaluation', 'Quality Evaluation'],
  ['adr', 'Architecture Decision Records'],
]

const STORAGE_KEY = 'designtrace_coordinator_thread'

function moduleLabel(name) {
  return MODULES.find(([id]) => id === name)?.[1] || name || '—'
}

function pretty(value) {
  if (value === undefined || value === null) {
    return 'No data available.'
  }
  return JSON.stringify(value, null, 2)
}

function statusClass(value) {
  const status = String(value || '').toUpperCase()

  if (status === 'APPROVED' || status === 'COMPLETED') {
    return 'dt2-success'
  }

  if (status === 'REJECTED' || status === 'FAILED') {
    return 'dt2-danger'
  }

  if (
    status === 'WAITING_FOR_REVIEW' ||
    status === 'REVIEW_REQUIRED'
  ) {
    return 'dt2-warning'
  }

  return 'dt2-neutral'
}

function StatusBadge({ value }) {
  return (
    <span className={`dt2-badge ${statusClass(value)}`}>
      {String(value || 'NOT STARTED').replaceAll('_', ' ')}
    </span>
  )
}

function JsonPanel({ title, value }) {
  return (
    <section className="dt2-json-panel">
      <div className="dt2-json-title">{title}</div>
      <pre>{pretty(value)}</pre>
    </section>
  )
}

function EmptyState({ children }) {
  return <div className="dt2-empty">{children}</div>
}

export default function CoordinatorPage() {
  const [threadId, setThreadId] = useState(
    () => localStorage.getItem(STORAGE_KEY) || ''
  )
  const [threadInput, setThreadInput] = useState(
    () => localStorage.getItem(STORAGE_KEY) || ''
  )

  
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDescription, setNewProjectDescription] = useState('')


  const [workflow, setWorkflow] = useState(null)
  const [history, setHistory] = useState(null)
  const [report, setReport] = useState(null)

  const [selectedModule, setSelectedModule] = useState(
    'requirement_analysis'
  )
  const [selectedAttempt, setSelectedAttempt] = useState('')
  const [activeTab, setActiveTab] = useState('overview')

  const [feedback, setFeedback] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const refreshData = useCallback(async (id) => {
    if (!id) return

    const [statusResult, historyResult] =
      await Promise.allSettled([
        coordinatorApi.status(id),
        coordinatorApi.history(id),
      ])

    if (statusResult.status === 'rejected') {
      throw statusResult.reason
    }

    const status = statusResult.value
    setWorkflow(status)

    if (historyResult.status === 'fulfilled') {
      setHistory(historyResult.value)
    } else {
      setHistory(null)
      setNotice(
        'Workflow loaded, but execution history could not be loaded.'
      )
    }

    if (status.workflow_status === 'COMPLETED') {
      try {
        const finalReport = await coordinatorApi.report(id)
        setReport(finalReport)
      } catch {
        setReport(null)
      }
    } else {
      setReport(null)
    }

    return status
  }, [])

  // Automatically restore the most recently used workflow.
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) return

    let cancelled = false

    async function restore() {
      try {
        const [status, savedHistory] = await Promise.all([
          coordinatorApi.status(saved),
          coordinatorApi.history(saved),
        ])

        if (cancelled) return

        setWorkflow(status)
        setHistory(savedHistory)

        if (status.workflow_status === 'COMPLETED') {
          const finalReport = await coordinatorApi.report(saved)
          if (!cancelled) setReport(finalReport)
        }
      } catch {
        if (!cancelled) {
          setError(
            'Could not restore the saved workflow. You can load another thread ID.'
          )
        }
      }
    }

    restore()

    return () => {
      cancelled = true
    }
  }, [])

  
const loadProjects = useCallback(async () => {
  const result = await coordinatorApi.listProjects()
  setProjects(result.projects || [])
}, [])

useEffect(() => {
  loadProjects().catch(() => {
    // Existing mock workflow remains usable
    // even if project listing fails.
  })
}, [loadProjects])

async function createProject(event) {
  event.preventDefault()

  if (newProjectName.trim().length < 2) {
    setError(
      'Enter a project name with at least two characters.'
    )
    return
  }

  setBusy(true)
  setError('')
  setNotice('')

  try {
    const created = await coordinatorApi.createProject(
      newProjectName.trim(),
      newProjectDescription.trim()
    )

    await loadProjects()

    setSelectedProjectId(created.project_id)
    setNewProjectName('')
    setNewProjectDescription('')

    setNotice(
      'Project saved to Neon. Select Start Mock Workflow to run the predefined demo outputs.'
    )

  } catch (err) {
    setError(err.message)

  } finally {
    setBusy(false)
  }
}


  async function startWorkflow() {
    setBusy(true)
    setError('')
    setNotice('')

    try {
      const data = await coordinatorApi.start(selectedProjectId)
      const id = data.thread_id

      if (!id) {
        throw new Error('Backend did not return a thread ID.')
      }

      localStorage.setItem(STORAGE_KEY, id)
      setThreadId(id)
      setThreadInput(id)
      setSelectedModule('requirement_analysis')
      setSelectedAttempt('')
      setActiveTab('overview')
      setFeedback('')
      setReport(null)

      await refreshData(id)
      setNotice('PP1 mock workflow started. Module inputs and outputs use the predefined Library demo data.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function loadWorkflow() {
    const id = threadInput.trim()

    if (!id) {
      setError('Enter a workflow thread ID.')
      return
    }

    setBusy(true)
    setError('')
    setNotice('')

    try {
      await refreshData(id)

      setThreadId(id)
      localStorage.setItem(STORAGE_KEY, id)
      setSelectedAttempt('')
      setFeedback('')
      setNotice('Workflow recovered successfully.')
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
    setNotice('')

    try {
      await refreshData(threadId)
      setNotice('Workflow and Neon history refreshed.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function submitReview(decision) {
    if (!threadId || !workflow?.pending_review) {
      setError('There is no Module waiting for review.')
      return
    }

    if (decision === 'reject' && !feedback.trim()) {
      setError('Rejection feedback is required.')
      return
    }

    setBusy(true)
    setError('')
    setNotice('')

    try {
      await coordinatorApi.review(
        threadId,
        decision,
        decision === 'reject' ? feedback.trim() : ''
      )

      await refreshData(threadId)
      setSelectedAttempt('')
      setFeedback('')

      setNotice(
        decision === 'approve'
          ? 'Module approved. Workflow advanced.'
          : 'Module rejected. Feedback submitted and retry processed.'
      )
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function clearCurrentWorkflow() {
    localStorage.removeItem(STORAGE_KEY)
    setThreadId('')
    setThreadInput('')
    setWorkflow(null)
    setHistory(null)
    setReport(null)
    setSelectedAttempt('')
    setFeedback('')
    setError('')
    setNotice('')
    setActiveTab('overview')
  }

  function downloadReport() {
    if (!report?.report) return

    const blob = new Blob(
      [JSON.stringify(report.report, null, 2)],
      { type: 'application/json' }
    )

    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `DesignTraceAI_${threadId}_report.json`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  const pending = workflow?.pending_review || null
  const statuses = workflow?.module_statuses || {}

  const executions = (history?.executions || [])
    .filter((item) => item.module === selectedModule)
    .sort((a, b) => b.attempt - a.attempt)

  const artifacts = (history?.artifacts || [])
    .filter((item) => item.module === selectedModule)
    .sort((a, b) => b.version - a.version)

  const reviews = (history?.reviews || [])
    .filter((item) => item.module === selectedModule)

  const chosenExecution =
    executions.find(
      (item) => String(item.attempt) === selectedAttempt
    ) || executions[0]

  const selectedStatus = statuses[selectedModule]
  const approvedCount = Object.values(statuses)
    .filter((item) => item.status === 'APPROVED').length

  return (
    <div className="dt2-app">
      <aside className="dt2-sidebar">
        <div className="dt2-brand">
          <span className="dt2-brand-mark">D</span>
          <div>
            <strong>DesignTrace AI</strong>
            <small>Coordinator Agent</small>
          </div>
        </div>

        <div className="dt2-sidebar-caption">WORKFLOW</div>

        <button
          className={`dt2-nav ${
            activeTab === 'overview' ? 'active' : ''
          }`}
          onClick={() => setActiveTab('overview')}
        >
          ◈ Workflow Overview
        </button>

        <button
          className={`dt2-nav ${
            activeTab === 'modules' ? 'active' : ''
          }`}
          onClick={() => setActiveTab('modules')}
        >
          ▦ Module Inputs & Outputs
        </button>

        <button
          className={`dt2-nav ${
            activeTab === 'history' ? 'active' : ''
          }`}
          onClick={() => setActiveTab('history')}
        >
          ◷ Review & Version History
        </button>

        <button
          className={`dt2-nav ${
            activeTab === 'report' ? 'active' : ''
          }`}
          onClick={() => setActiveTab('report')}
        >
          ▤ Final Report
        </button>

        <div className="dt2-sidebar-caption">MODULES</div>

        <div className="dt2-module-nav">
          {MODULES.map(([id, label], index) => (
            <button
              key={id}
              className={
                selectedModule === id
                  ? 'dt2-module-link selected'
                  : 'dt2-module-link'
              }
              onClick={() => {
                setSelectedModule(id)
                setSelectedAttempt('')
                setActiveTab('modules')
              }}
            >
              <span>{index + 1}. {label}</span>
              <span className={
                statuses[id]?.status === 'APPROVED'
                  ? 'dt2-module-check'
                  : ''
              }>
                {statuses[id]?.status === 'APPROVED' ? '✓' : '○'}
              </span>
            </button>
          ))}
        </div>

        <div className="dt2-sidebar-footer">
          <strong>PP1 Demonstration</strong>
          <p>Module outputs are simulated. Coordinator workflow and Neon persistence are real.</p>
        </div>
      </aside>

      <main className="dt2-main">
        <header className="dt2-header">
          <div>
            <div className="dt2-eyebrow">
              DESIGNTRACE AI / COORDINATOR
            </div>
            <h1>Workflow Dashboard</h1>
            <p>
              Orchestration, human review, version tracking and
              persistent Module artifacts
            </p>
          </div>

          <div className="dt2-header-actions">
            <button
              className="dt2-btn"
              onClick={refreshWorkflow}
              disabled={busy || !threadId}
            >
              ↻ Refresh
            </button>
            <button
              className="dt2-btn dt2-primary"
              onClick={startWorkflow}
              disabled={busy}
            >
              {busy ? 'Please wait...' : '+ Start Mock Workflow'}
            </button>
          </div>
        </header>

        <section className="dt2-card">
          <div className="dt2-card-heading">
            <div>
              <h2>Workflow Recovery</h2>
              <p>
                Enter an existing thread ID to recover a workflow
                from Neon after a backend restart.
              </p>
            </div>
          </div>

          
<section className="dt2-card">

  <div className="dt2-card-heading">
    <div>
      <h2>Create Project</h2>

      <p>
        Project details are saved in Neon PostgreSQL.
        Module outputs remain predefined Library
        Management mock data for PP1.
      </p>
    </div>
  </div>

  <form
    onSubmit={createProject}
    className="dt2-project-form"
  >

    <input
      value={newProjectName}
      onChange={(event) =>
        setNewProjectName(event.target.value)
      }
      placeholder="Project name"
      maxLength={255}
      required
      aria-label="New project name"
    />

    <textarea
      value={newProjectDescription}
      onChange={(event) =>
        setNewProjectDescription(event.target.value)
      }
      placeholder="Project description"
      maxLength={5000}
      rows={3}
      aria-label="New project description"
    />

    <button
      className="dt2-btn dt2-primary"
      type="submit"
      disabled={busy}
    >
      + Create Project
    </button>

  </form>

  <div className="dt2-project-select">

    <label htmlFor="dt2-project-picker">
      Project for next mock workflow
    </label>

    <select
      id="dt2-project-picker"
      value={selectedProjectId}
      onChange={(event) =>
        setSelectedProjectId(event.target.value)
      }
      disabled={busy}
    >

      <option value="">
        Default Library Management demo
        (original behavior)
      </option>

      {projects.map((project) => (
        <option
          key={project.project_id}
          value={project.project_id}
        >
          {project.name}
          {' '}
          ({project.project_id.slice(0, 8)})
        </option>
      ))}

    </select>

  </div>

</section>


          <div className="dt2-load-row">
            <input
              value={threadInput}
              onChange={(event) =>
                setThreadInput(event.target.value)
              }
              placeholder="Paste existing workflow thread ID"
              aria-label="Workflow thread ID"
            />

            <button
              className="dt2-btn dt2-primary"
              onClick={loadWorkflow}
              disabled={busy}
            >
              Load Workflow
            </button>

            <button
              className="dt2-btn"
              onClick={clearCurrentWorkflow}
              disabled={busy}
            >
              Clear
            </button>
          </div>

          {threadId && (
            <p className="dt2-thread">
              Active thread: <code>{threadId}</code>
            </p>
          )}
        </section>

        {error && (
          <div className="dt2-alert dt2-error">
            {error}
          </div>
        )}

        {notice && (
          <div className="dt2-alert dt2-info">
            {notice}
          </div>
        )}

        {!workflow ? (
          <section className="dt2-card">
            <EmptyState>
              Start the PP1 mock Library workflow or load an
              existing workflow using its thread ID.
            </EmptyState>
          </section>
        ) : (
          <>
            <section className="dt2-stats">
              <div className="dt2-stat">
                <span>Workflow Status</span>
                <StatusBadge value={workflow.workflow_status} />
              </div>

              <div className="dt2-stat">
                <span>Approved Modules</span>
                <strong>{approvedCount} / 7</strong>
              </div>

              <div className="dt2-stat">
                <span>Current Module</span>
                <strong>
                  {moduleLabel(workflow.current_module)}
                </strong>
              </div>

              <div className="dt2-stat">
                <span>Final Report</span>
                <strong>
                  {workflow.report_available
                    ? 'Available'
                    : 'Not available'}
                </strong>
              </div>
            </section>

            {pending && (
              <section className="dt2-card dt2-review-card">
                <div className="dt2-card-heading">
                  <div>
                    <h2>Human Review Required</h2>
                    <p>
                      Review the Module output before the
                      Coordinator proceeds.
                    </p>
                  </div>
                  <StatusBadge value="REVIEW_REQUIRED" />
                </div>

                <div className="dt2-review-meta">
                  <span>
                    Module: <strong>
                      {moduleLabel(pending.module_name)}
                    </strong>
                  </span>
                  <span>
                    Version: <strong>
                      {pending.version}
                    </strong>
                  </span>
                </div>

                <ModuleResultViewer
                  moduleName={pending.module_name}
                  output={pending.output}
                />

                <label className="dt2-field-label">
                  Review Feedback
                </label>

                <textarea
                  rows={3}
                  value={feedback}
                  onChange={(event) =>
                    setFeedback(event.target.value)
                  }
                  placeholder="Explain what must be improved if rejecting this output..."
                />

                <div className="dt2-action-row">
                  <button
                    className="dt2-btn dt2-approve"
                    disabled={busy}
                    onClick={() => submitReview('approve')}
                  >
                    ✓ Approve Module
                  </button>

                  <button
                    className="dt2-btn dt2-reject"
                    disabled={busy || !feedback.trim()}
                    onClick={() => submitReview('reject')}
                  >
                    ✕ Reject & Retry
                  </button>
                </div>

                <p className="dt2-help">
                  Rejection requires feedback. For PP1, retry
                  outputs are generated by the mock Module.
                </p>
              </section>
            )}

            {activeTab === 'overview' && (
              <section className="dt2-card">
                <div className="dt2-card-heading">
                  <div>
                    <h2>Module Progress</h2>
                    <p>
                      Current execution status for all seven Modules.
                    </p>
                  </div>
                </div>

                <div className="dt2-progress-list">
                  {MODULES.map(([id, label], index) => {
                    const item = statuses[id] || {}

                    return (
                      <button
                        className="dt2-progress-item"
                        key={id}
                        onClick={() => {
                          setSelectedModule(id)
                          setSelectedAttempt('')
                          setActiveTab('modules')
                        }}
                      >
                        <div className="dt2-step-number">
                          {index + 1}
                        </div>

                        <div className="dt2-progress-info">
                          <strong>{label}</strong>
                          <small>
                            Version {item.version || 0}
                            {' · '}
                            Retries {item.retry_count || 0}
                          </small>
                        </div>

                        <StatusBadge value={item.status} />
                      </button>
                    )
                  })}
                </div>
              </section>
            )}

            {activeTab === 'modules' && (
              <section className="dt2-card">
                <div className="dt2-card-heading">
                  <div>
                    <h2>Module Inputs & Outputs</h2>
                    <p>
                      Execution snapshots saved in Neon.
                    </p>
                  </div>
                  <StatusBadge value={selectedStatus?.status} />
                </div>

                <div className="dt2-control-row">
                  <div>
                    <label className="dt2-field-label">
                      Select Module
                    </label>

                    <select
                      value={selectedModule}
                      onChange={(event) => {
                        setSelectedModule(event.target.value)
                        setSelectedAttempt('')
                      }}
                    >
                      {MODULES.map(([id, label]) => (
                        <option key={id} value={id}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="dt2-field-label">
                      Execution Attempt
                    </label>

                    <select
                      value={
                        chosenExecution
                          ? String(chosenExecution.attempt)
                          : ''
                      }
                      onChange={(event) =>
                        setSelectedAttempt(event.target.value)
                      }
                      disabled={!executions.length}
                    >
                      {!executions.length && (
                        <option value="">No attempts</option>
                      )}

                      {executions.map((item) => (
                        <option
                          key={item.attempt}
                          value={String(item.attempt)}
                        >
                          Version {item.attempt} — {item.status}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {chosenExecution ? (
                  <>
                    <div className="dt2-execution-meta">
                      <span>
                        Attempt: {chosenExecution.attempt}
                      </span>
                      <StatusBadge
                        value={chosenExecution.status}
                      />
                    </div>

                    <div className="dt2-json-grid">
                      <JsonPanel
                        title="Module Input (Neon)"
                        value={chosenExecution.input}
                      />
                      <ModuleResultViewer
                        moduleName={selectedModule}
                        output={chosenExecution.output}
                      />
                    </div>
                  </>
                ) : (
                  <EmptyState>
                    No execution snapshot has been saved
                    for this Module yet.
                  </EmptyState>
                )}

                <h3>Saved Artifact Versions</h3>

                {artifacts.length ? (
                  <div className="dt2-artifact-list">
                    {artifacts.map((artifact, index) => (
                      <details key={`${artifact.version}-${index}`}>
                        <summary>
                          Version {artifact.version}
                          <StatusBadge value={artifact.status} />
                        </summary>
                        <pre>{pretty(artifact.content)}</pre>
                      </details>
                    ))}
                  </div>
                ) : (
                  <EmptyState>
                    No artifact versions found.
                  </EmptyState>
                )}
              </section>
            )}

            {activeTab === 'history' && (
              <section className="dt2-card">
                <div className="dt2-card-heading">
                  <div>
                    <h2>Review & Version History</h2>
                    <p>
                      Human decisions and saved execution versions.
                    </p>
                  </div>
                </div>

                <div className="dt2-control-row">
                  <div>
                    <label className="dt2-field-label">
                      Filter by Module
                    </label>
                    <select
                      value={selectedModule}
                      onChange={(event) =>
                        setSelectedModule(event.target.value)
                      }
                    >
                      {MODULES.map(([id, label]) => (
                        <option key={id} value={id}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <h3>Human Review Decisions</h3>

                {reviews.length ? (
                  <div className="dt2-history-list">
                    {reviews.map((review, index) => (
                      <div className="dt2-history-item" key={index}>
                        <div className="dt2-history-heading">
                          <strong>
                            {moduleLabel(review.module)}
                          </strong>
                          <StatusBadge value={review.decision} />
                        </div>

                        <p>
                          {review.feedback ||
                            'Approved without feedback.'}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState>
                    No human review decisions recorded
                    for this Module.
                  </EmptyState>
                )}

                <h3>Execution Version History</h3>

                {executions.length ? (
                  <div className="dt2-history-list">
                    {executions.map((execution) => (
                      <details
                        className="dt2-history-item"
                        key={execution.attempt}
                      >
                        <summary>
                          <strong>
                            Version {execution.attempt}
                          </strong>
                          <StatusBadge
                            value={execution.status}
                          />
                        </summary>

                        <JsonPanel
                          title="Saved Input"
                          value={execution.input}
                        />

                        <JsonPanel
                          title="Saved Output"
                          value={execution.output}
                        />
                      </details>
                    ))}
                  </div>
                ) : (
                  <EmptyState>
                    No execution versions available.
                  </EmptyState>
                )}
              </section>
            )}

            {activeTab === 'report' && (
              <section className="dt2-card">
                <div className="dt2-card-heading">
                  <div>
                    <h2>Final Coordinator Report</h2>
                    <p>
                      Readable report generated from approved Module
                      artifacts and saved workflow results.
                    </p>
                  </div>
                </div>

                  {report?.report ? (
                    <FinalReportViewer response={report} />
                   ) : (
                    <EmptyState>
                      The final report becomes available after
                      all seven Modules are approved.
                    </EmptyState>
                   )}
              </section>
            )}
          </>
        )}

        <footer className="dt2-footer">
          DesignTrace AI · PP1 Coordinator Demonstration ·
          Mock Module outputs · PostgreSQL persistence
        </footer>
      </main>
    </div>
  )
}
