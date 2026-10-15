import { useEffect, useMemo, useState } from 'react'
import { analyzeTraceability } from '../../services/traceabilityService'
import TraceabilityInput from '../../components/traceability/TraceabilityInput'
import TraceabilitySummary from '../../components/traceability/TraceabilitySummary'
import TraceabilityMatrix from '../../components/traceability/TraceabilityMatrix'
import TraceabilitySidebar from '../../components/traceability/TraceabilitySidebar'


   // DEMO INPUT

const exampleRequest = {
  project_id: 'TEST-LIB-001',

  requirements: [
    {
      requirement_id: 'REQ-LIB-001',
      statement:
        'Members shall be able to borrow available books.',
      requirement_type: 'FR',
      asr: false,
    },
    {
      requirement_id: 'REQ-LIB-002',
      statement:
        'Only authorized members shall access their borrowing history.',
      requirement_type: 'NFR',
      asr: true,
    },
    {
      requirement_id: 'REQ-LIB-003',
      statement:
        'Members shall receive a reminder before a borrowed book is due.',
      requirement_type: 'FR',
      asr: false,
    },
  ],

  architecture: {
    elements: [
      {
        artifact_id: 'ARCH-LIB-001',
        name: 'BorrowingService',
        type: 'service',
        description:
          'Handles book borrowing, book return processing, availability checks, and loan status.',
      },
      {
        artifact_id: 'ARCH-LIB-002',
        name: 'LibrarySecurityService',
        type: 'service',
        description:
          'Handles member authentication, authorization, access control, and protection of library account information.',
      },
      {
        artifact_id: 'ARCH-LIB-003',
        name: 'ReminderService',
        type: 'service',
        description:
          'Generates and sends due-date reminders to members for borrowed books.',
      },
    ],
  },

  database: {
    entities: [
      {
        artifact_id: 'DB-LIB-001',
        name: 'Member',
        description:
          'Stores member profile, contact information, and account identity.',
      },
      {
        artifact_id: 'DB-LIB-002',
        name: 'Book',
        description:
          'Stores book details, availability status, title, author, and inventory information.',
      },
      {
        artifact_id: 'DB-LIB-003',
        name: 'Loan',
        description:
          'Stores member borrowing records, borrowed book, borrow date, due date, return date, and loan status.',
      },
      {
        artifact_id: 'DB-LIB-004',
        name: 'AccessAudit',
        description:
          'Stores login attempts, access events, authorization activity, and security audit records.',
      },
    ],
  },

  api: {
    operations: [
      {
        artifact_id: 'API-LIB-001',
        method: 'POST',
        path: '/loans',
        description:
          'Creates a loan when an authorized member borrows an available book.',
      },
      {
        artifact_id: 'API-LIB-002',
        method: 'GET',
        path: '/members/{id}/borrowing-history',
        description:
          'Returns the borrowing history of the authenticated and authorized member.',
      },
      {
        artifact_id: 'API-LIB-003',
        method: 'POST',
        path: '/auth/login',
        description:
          'Authenticates library members using account credentials.',
      },
    ],
  },

  components: [
    {
      artifact_id: 'COMP-LIB-001',
      name: 'BookBorrowingComponent',
      description:
        'Provides the user-facing functionality for members to borrow available books.',
    },
    {
      artifact_id: 'COMP-LIB-002',
      name: 'BorrowingHistoryComponent',
      description:
        "Displays a member's borrowing history and loan information.",
    },
    {
      artifact_id: 'COMP-LIB-003',
      name: 'LibrarySecurityComponent',
      description:
        'Implements member authentication, authorization, access control, and protection of borrowing information.',
    },
    {
      artifact_id: 'COMP-LIB-004',
      name: 'DueDateReminderComponent',
      description:
        'Generates reminder notifications before borrowed books reach their due date.',
    },
  ],
}


/* SAVED DEMO OUTPUT

   This is used when "Load Demo Example" is clicked.
   It does NOT call FastAPI or Gemini. */

const exampleResult = {
  project_id: 'TEST-LIB-001',

  trace_links: [
    {
      requirement_id: 'REQ-LIB-001',
      artifact_id: 'API-LIB-001',
      artifact_type: 'api',
      link_valid: true,
      semantic_similarity: 0.5329,
      confidence: 0.95,
      rationale:
        'The POST /loans API directly implements the book borrowing functionality.',
    },
    {
      requirement_id: 'REQ-LIB-001',
      artifact_id: 'ARCH-LIB-001',
      artifact_type: 'architecture',
      link_valid: true,
      semantic_similarity: 0.5083,
      confidence: 0.95,
      rationale:
        'The BorrowingService directly supports borrowing and availability checks.',
    },
    {
      requirement_id: 'REQ-LIB-001',
      artifact_id: 'COMP-LIB-001',
      artifact_type: 'component',
      link_valid: true,
      semantic_similarity: 0.4086,
      confidence: 0.95,
      rationale:
        'The BookBorrowingComponent provides the user-facing borrowing functionality.',
    },
    {
      requirement_id: 'REQ-LIB-001',
      artifact_id: 'DB-LIB-002',
      artifact_type: 'database',
      link_valid: true,
      semantic_similarity: 0.4674,
      confidence: 0.9,
      rationale:
        'The Book entity stores availability status needed for borrowing.',
    },
    {
      requirement_id: 'REQ-LIB-001',
      artifact_id: 'DB-LIB-003',
      artifact_type: 'database',
      link_valid: true,
      semantic_similarity: 0.5062,
      confidence: 0.92,
      rationale:
        'The Loan entity stores borrowing records.',
    },

    {
      requirement_id: 'REQ-LIB-002',
      artifact_id: 'API-LIB-002',
      artifact_type: 'api',
      link_valid: true,
      semantic_similarity: 0.517,
      confidence: 0.95,
      rationale:
        'The endpoint provides authorized access to borrowing history.',
    },
    {
      requirement_id: 'REQ-LIB-002',
      artifact_id: 'ARCH-LIB-002',
      artifact_type: 'architecture',
      link_valid: true,
      semantic_similarity: 0.0,
      confidence: 0.9,
      rationale:
        'The security service provides authorization and access control.',
    },
    {
      requirement_id: 'REQ-LIB-002',
      artifact_id: 'COMP-LIB-002',
      artifact_type: 'component',
      link_valid: true,
      semantic_similarity: 0.4139,
      confidence: 0.9,
      rationale:
        'The borrowing history component displays member history.',
    },
    {
      requirement_id: 'REQ-LIB-002',
      artifact_id: 'COMP-LIB-003',
      artifact_type: 'component',
      link_valid: true,
      semantic_similarity: 0.0,
      confidence: 0.9,
      rationale:
        'The security component implements authentication and authorization.',
    },
    {
      requirement_id: 'REQ-LIB-002',
      artifact_id: 'DB-LIB-003',
      artifact_type: 'database',
      link_valid: true,
      semantic_similarity: 0.429,
      confidence: 0.9,
      rationale:
        'The Loan entity stores borrowing-history data.',
    },
    {
      requirement_id: 'REQ-LIB-002',
      artifact_id: 'DB-LIB-004',
      artifact_type: 'database',
      link_valid: true,
      semantic_similarity: 0.0,
      confidence: 0.85,
      rationale:
        'The AccessAudit entity stores authorization and security activity.',
    },

    {
      requirement_id: 'REQ-LIB-003',
      artifact_id: 'ARCH-LIB-003',
      artifact_type: 'architecture',
      link_valid: true,
      semantic_similarity: 0.6703,
      confidence: 0.95,
      rationale:
        'The ReminderService generates and sends due-date reminders.',
    },
    {
      requirement_id: 'REQ-LIB-003',
      artifact_id: 'COMP-LIB-004',
      artifact_type: 'component',
      link_valid: true,
      semantic_similarity: 0.6054,
      confidence: 0.95,
      rationale:
        'The DueDateReminderComponent generates reminder notifications.',
    },
    {
      requirement_id: 'REQ-LIB-003',
      artifact_id: 'DB-LIB-003',
      artifact_type: 'database',
      link_valid: true,
      semantic_similarity: 0.4445,
      confidence: 0.92,
      rationale:
        'The Loan entity stores due dates required for reminder generation.',
    },
  ],

  traceability_matrix: [
    {
      requirement_id: 'REQ-LIB-001',

      architecture_links: [
        'ARCH-LIB-001',
      ],

      database_links: [
        'DB-LIB-002',
        'DB-LIB-003',
      ],

      api_links: [
        'API-LIB-001',
      ],

      component_links: [
        'COMP-LIB-001',
      ],

      coverage_status: 'FULLY_COVERED',
    },

    {
      requirement_id: 'REQ-LIB-002',

      architecture_links: [
        'ARCH-LIB-002',
      ],

      database_links: [
        'DB-LIB-003',
        'DB-LIB-004',
      ],

      api_links: [
        'API-LIB-002',
      ],

      component_links: [
        'COMP-LIB-002',
        'COMP-LIB-003',
      ],

      coverage_status: 'FULLY_COVERED',
    },

    {
      requirement_id: 'REQ-LIB-003',

      architecture_links: [
        'ARCH-LIB-003',
      ],

      database_links: [
        'DB-LIB-003',
      ],

      api_links: [],

      component_links: [
        'COMP-LIB-004',
      ],

      coverage_status: 'PARTIALLY_COVERED',
    },
  ],

  coverage_summary: {
    total_requirements: 3,
    requirements_with_links: 3,
    requirements_without_links: 0,
    requirement_coverage_percentage: 100.0,
    fully_covered: 2,
    partially_covered: 1,
    uncovered: 0,
    average_artifact_category_coverage_percentage: 91.67,
  },

  evaluation: null,

  validation: {
    valid: true,
    issues: [],
  },
}


// PAGE 

function TraceabilityPage() {
  const [darkMode, setDarkMode] = useState(true)

  const [jsonInput, setJsonInput] = useState('')

  const [submittedRequest, setSubmittedRequest] =
    useState(null)

  const [traceabilityData, setTraceabilityData] =
    useState(null)

  const [loading, setLoading] = useState(false)

  const [error, setError] = useState('')

  const [resultMode, setResultMode] = useState('')



// DARK / LIGHT MODE

  useEffect(() => {
    document.documentElement.setAttribute(
      'data-theme',
      darkMode ? 'dark' : 'light',
    )
  }, [darkMode])



// LOAD DEMO

  function handleLoadExample() {
    setJsonInput(
      JSON.stringify(
        exampleRequest,
        null,
        2,
      ),
    )

    setSubmittedRequest(
      exampleRequest,
    )

    setTraceabilityData(
      exampleResult,
    )

    setResultMode('demo')

    setError('')
  }


  /*RUN LIVE TRACEABILITY

     This sends the JSON to FastAPI.*/

  async function handleAnalyze() {
    try {
      setLoading(true)

      setError('')

      const parsedRequest =
        JSON.parse(jsonInput)

      setSubmittedRequest(
        parsedRequest,
      )

      const result =
        await analyzeTraceability(
          parsedRequest,
        )

      setTraceabilityData(
        result,
      )

      setResultMode('live')
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError(
          'Invalid JSON. Please check commas, brackets, and quotation marks.',
        )
      } else {
        setError(
          err.message ||
            'Traceability analysis failed.',
        )
      }
    } finally {
      setLoading(false)
    }
  }



// REQUIREMENT LOOKUP

  const requirementMap =
    useMemo(() => {
      if (
        !submittedRequest?.requirements
      ) {
        return {}
      }

      return Object.fromEntries(
        submittedRequest.requirements.map(
          (requirement) => [
            requirement.requirement_id,
            requirement,
          ],
        ),
      )
    }, [submittedRequest])


// ARTIFACT LOOKUP
  const artifactMap =
    useMemo(() => {
      if (!submittedRequest) {
        return {}
      }

      const architecture =
        submittedRequest
          .architecture
          ?.elements ?? []

      const database =
        submittedRequest
          .database
          ?.entities ?? []

      const api =
        submittedRequest
          .api
          ?.operations ?? []

      const components =
        submittedRequest
          .components ?? []

      const allArtifacts = [
        ...architecture,
        ...database,
        ...api,
        ...components,
      ]

      return Object.fromEntries(
        allArtifacts.map(
          (artifact) => [
            artifact.artifact_id,
            artifact,
          ],
        ),
      )
    }, [submittedRequest])


// RESULT VALUES

  const matrix =
    traceabilityData
      ?.traceability_matrix ?? []

  const coverage =
    traceabilityData
      ?.coverage_summary

  const totalRequirements =
    coverage
      ?.total_requirements ?? 0

  const fullyCovered =
    coverage
      ?.fully_covered ?? 0

  const partiallyCovered =
    coverage
      ?.partially_covered ?? 0

  const uncovered =
    coverage
      ?.uncovered ?? 0

  const requirementCoverage =
    coverage
      ?.requirement_coverage_percentage ?? 0



//PERCENTAGE
  function percentage(value) {
    if (!totalRequirements) {
      return '0%'
    }

    return `${(
      (value /
        totalRequirements) *
      100
    ).toFixed(1)}%`
  }



  return (
    <div className="app-shell">

      {/* SIDEBAR*/}

      <TraceabilitySidebar
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        projectId={traceabilityData?.project_id}
    />


      {/* MAIN CONTENT */}

      <main className="main-content">

        <header className="page-header">

          <div>

            <h1>
              Requirement-to-Design
              Traceability
            </h1>

            <p>
              Submit structured
              requirements and design
              artifacts to generate a
              traceability matrix.
            </p>

          </div>


          <div className="header-actions">

            <button
              type="button"
              className="secondary-button"
            >
              ⇩ Export Report
            </button>

            <button
              type="button"
              className="primary-button"
            >
              ☷ Filter & Options
            </button>

          </div>

        </header>


        {/*JSON INPUT*/}

        <TraceabilityInput
            jsonInput={jsonInput}
            setJsonInput={setJsonInput}
            loading={loading}
            onLoadExample={handleLoadExample}
            onAnalyze={handleAnalyze}
        />


        {/* RESULT MODE*/}

        {resultMode && (
          <div
            style={{
              marginTop: '14px',
              fontSize: '12px',
              color:
                resultMode ===
                'demo'
                  ? 'var(--orange)'
                  : 'var(--green)',
              fontWeight: '700',
            }}
          >
            {resultMode === 'demo'
              ? '● Demo result loaded.'
              : '● Live result generated from the FastAPI backend.'}
          </div>
        )}


        {/* ERROR*/}

        {error && (
          <div className="trace-error">
            {error}
          </div>
        )}


        {/*SUMMARY*/}

        <TraceabilitySummary
            totalRequirements={totalRequirements}
            fullyCovered={fullyCovered}
            partiallyCovered={partiallyCovered}
            uncovered={uncovered}
            requirementCoverage={requirementCoverage}
        />


        {/* TABS */}

        <section className="toolbar">

          <div className="tabs">

            <button
              type="button"
              className="tab active"
            >
              Traceability Matrix
            </button>

            <button
              type="button"
              className="tab"
            >
              Coverage Analysis
            </button>

            <button
              type="button"
              className="tab"
            >
              Gaps & Issues
            </button>

            <button
              type="button"
              className="tab"
            >
              Impact Analysis
            </button>

          </div>

        </section>


        {/*  TRACEABILITY MATRIX*/}

        <TraceabilityMatrix
            matrix={matrix}
            requirementMap={requirementMap}
            artifactMap={artifactMap}
        />


        {/* FOOTER*/}

        {traceabilityData && (

          <footer className="page-footer">

            <p>
              Showing{' '}
              {matrix.length}{' '}
              of{' '}
              {totalRequirements}{' '}
              requirements
            </p>


            <div className="validation-message">
              {traceabilityData
                .validation
                ?.valid
                ? '✓ Output validated'
                : '⚠ Validation issues found'}
            </div>


            <button
              type="button"
              className="continue-button"
            >
              Continue to →
            </button>

          </footer>

        )}

      </main>

    </div>
  )
}


export default TraceabilityPage