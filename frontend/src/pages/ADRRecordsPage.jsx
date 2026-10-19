import { useEffect, useState } from 'react'

import ADRDetails from '../components/adr/ADRDetails'
import ADRList from '../components/adr/ADRList'
import ADREvaluationDemo from '../components/adr/ADREvaluationDemo'

import {
  getProjectADRs,
  updateADRStatus,
} from '../services/adrService'

import './ADRRecordsPage.css'


const DEFAULT_PROJECT_ID = 'ADR-VIVA-001'


function ADRRecordsPage() {
  const [projectId, setProjectId] = useState(
    DEFAULT_PROJECT_ID
  )

  // Default page for viva
  const [view, setView] = useState('demo')

  const [adrs, setAdrs] = useState([])
  const [selectedADR, setSelectedADR] = useState(null)

  const [search, setSearch] = useState('')

  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)

  const [error, setError] = useState('')

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('adr-theme') || 'dark'
  })


  useEffect(() => {
    localStorage.setItem(
      'adr-theme',
      theme
    )
  }, [theme])


  useEffect(() => {
    loadADRs()
  }, [])


  async function loadADRs(id = projectId) {
    try {
      setLoading(true)
      setError('')

      const data = await getProjectADRs(id)

      setAdrs(data)

      setSelectedADR((current) => {
        if (!data.length) {
          return null
        }

        if (!current) {
          return data[0]
        }

        return (
          data.find(
            (item) =>
              item.adr_id === current.adr_id
          ) || data[0]
        )
      })
    } catch (err) {
      setError(
        err.message ||
          'Unable to load ADR records.'
      )

      setAdrs([])
      setSelectedADR(null)
    } finally {
      setLoading(false)
    }
  }


  async function handleProjectSubmit(event) {
    event.preventDefault()

    if (!projectId.trim()) {
      return
    }

    await loadADRs(
      projectId.trim()
    )

    setView('records')
  }


  async function handleStatusChange(status) {
    if (!selectedADR) {
      return
    }

    try {
      setUpdating(true)
      setError('')

      const updated =
        await updateADRStatus(
          selectedADR.adr_id,
          status
        )

      setSelectedADR(updated)

      setAdrs((current) =>
        current.map((adr) =>
          adr.adr_id === updated.adr_id
            ? updated
            : adr
        )
      )
    } catch (err) {
      setError(
        err.message ||
          'Unable to update ADR status.'
      )
    } finally {
      setUpdating(false)
    }
  }


  function toggleTheme() {
    setTheme((current) =>
      current === 'dark'
        ? 'light'
        : 'dark'
    )
  }


  return (
    <div
      className={`adr-page adr-theme-${theme}`}
    >
      {/* SIDEBAR */}
      <aside className="adr-sidebar">

        <div className="adr-brand">
          <div className="adr-brand-icon">
            ◈
          </div>

          <span>
            DesignTrace <strong>AI</strong>
          </span>
        </div>


        <div className="adr-project-box">
          <span>CURRENT PROJECT</span>

          <strong>{projectId}</strong>

          <small>
            ● In Progress
          </small>
        </div>


        <nav className="adr-nav">
          <span>
            Dashboard
          </span>

          <span>
            Projects
          </span>

          <span>
            Requirements
          </span>


          <div className="adr-nav-group">

            <strong>
              Design Workspace
            </strong>

            <span>
              Architecture Design
            </span>

            <span>
              Database Design
            </span>

            <span>
              API & Component Design
            </span>

            <span>
              Traceability
            </span>

            <span>
              Quality Evaluation
            </span>

            <span className="active">
              ADR Records
            </span>

          </div>


          <span>
            Reports
          </span>

          <span>
            Settings
          </span>
        </nav>


        <div className="adr-sidebar-footer">

          <div>
            <strong>
              Demo User
            </strong>

            <small>
              demo@designtrace.ai
            </small>
          </div>


          <button
            type="button"
            className="adr-theme-toggle"
            onClick={toggleTheme}
          >
            <span>
              {theme === 'dark'
                ? '☾ Dark Mode'
                : '☀ Light Mode'}
            </span>

            <span
              className={`adr-toggle-switch ${
                theme === 'light'
                  ? 'light'
                  : ''
              }`}
            >
              <span />
            </span>
          </button>

        </div>
      </aside>


      {/* MAIN WORKSPACE */}
      <section className="adr-workspace">

        {/* TOP BAR */}
        <header className="adr-topbar">

          <div>
            <h1>
              Architecture Decision Records
            </h1>

            <p>
              Capture, track and manage important
              architectural decisions.
            </p>
          </div>


          <div className="adr-topbar-actions">

            {/* DEMO / REPOSITORY SWITCH */}
            <div className="adr-view-switch">

              <button
                type="button"
                className={
                  view === 'demo'
                    ? 'active'
                    : ''
                }
                onClick={() =>
                  setView('demo')
                }
              >
                Integration Preview
              </button>


              <button
                type="button"
                className={
                  view === 'records'
                    ? 'active'
                    : ''
                }
                onClick={() =>
                  setView('records')
                }
              >
                ADR Repository
              </button>

            </div>


            {/* THEME BUTTON */}
            <button
              type="button"
              className="adr-mobile-theme-button"
              onClick={toggleTheme}
              title="Toggle light/dark mode"
            >
              {theme === 'dark'
                ? '☀'
                : '☾'}
            </button>


            {/* PROJECT SEARCH ONLY SHOW IN REPOSITORY */}
            {view === 'records' && (
              <form
                className="adr-project-form"
                onSubmit={handleProjectSubmit}
              >

                <input
                  value={projectId}
                  onChange={(event) =>
                    setProjectId(
                      event.target.value
                    )
                  }
                  placeholder="Project ID"
                />

                <button type="submit">
                  Load Project
                </button>

              </form>
            )}

          </div>
        </header>


        {/* ERROR */}
        {error && (
          <div className="adr-error">

            <span>
              {error}
            </span>

            <button
              type="button"
              onClick={() =>
                setError('')
              }
            >
              ×
            </button>

          </div>
        )}


        {/* ========================= */}
        {/* EVALUATION DEMO VIEW */}
        {/* ========================= */}

        {view === 'demo' ? (

          <ADREvaluationDemo
            onGenerated={(generatedProjectId) => {
            setProjectId(generatedProjectId)
            loadADRs(generatedProjectId)
        }}
          />

        ) : loading ? (

          /* ========================= */
          /* LOADING REPOSITORY */
          /* ========================= */

          <div className="adr-loading">
            Loading ADR records...
          </div>

        ) : (

          /* ========================= */
          /* ADR REPOSITORY VIEW */
          /* ========================= */

          <div className="adr-content">

            <ADRList
              adrs={adrs}
              selectedADR={selectedADR}
              onSelect={setSelectedADR}
              search={search}
              onSearchChange={setSearch}
            />


            <ADRDetails
              adr={selectedADR}
              onStatusChange={
                handleStatusChange
              }
              updating={updating}
            />

          </div>

        )}

      </section>
    </div>
  )
}


export default ADRRecordsPage