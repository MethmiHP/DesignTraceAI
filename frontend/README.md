# Quality Evaluation frontend

The feature lives in `src/components/qualoty-evaluation/`. `App.jsx` mounts the module.

## Run

Start the backend from `backend`:

```sh
venv/bin/python -m uvicorn app:app --reload --port 8000
```

Start the frontend from `frontend`:

```sh
npm install
npm run dev
```

Vite proxies `/quality-evaluation` to the backend on port 8000. For production, configure your web server to proxy that path to the backend.

Choose **New evaluation** to paste a complete request, or **Try the example** to load a banking scenario. Run evaluation to populate the dashboard with actual backend results. The theme switch in the sidebar toggles dark/light mode and remembers the choice locally.

The dashboard includes category pass rates, NFR coverage, severity filters, expandable evidence, recommendations, related findings, skipped checks, session history, and PDF report export. N/A values remain N/A. History holds the most recent 20 responses in memory and resets on reload. It is not server history. No numerical demo results or external standard compliance claims are fabricated.

`useQualityEvaluation.js` manages requests and state; `QualityEvaluation.jsx` renders the interface; `quality-evaluation.css` provides responsive layout and theme variables; `example.json` is the backend-compatible sample input.

Checks: `npm run lint` and `npm run build`.

PDF export downloads the selected evaluation with metrics, category results, findings, evidence, recommendations, groups, and rule outcomes. Backend output files remain JSON.

## Long-running evaluations

The frontend uses `POST /quality-evaluation/jobs` and polls `GET /quality-evaluation/jobs/{job_id}`. Individual HTTP calls have a 30-second connection deadline; the overall evaluation has no three-minute browser deadline. Progress shows completed rules and the rule being checked. The pending job ID is retained in session storage so **Resume evaluation** can reconnect after a refresh or transient polling failure without creating another job. Completed reports are still saved in `backend/output` before completion is reported.

The current job queue is process-local: run the backend with one Uvicorn worker. It permits two concurrent jobs and four active/queued jobs, retains up to 100 job records, and returns 429 when full. A backend restart discards pending job state; the frontend reports this and allows resubmission. Multi-worker/production deployments need a shared durable job queue. The existing synchronous `/evaluate` endpoint remains available for integrations.

Gemini and Groq calls each have a 60-second timeout, with SDK retries disabled. The existing configured-provider fallback still runs; if no provider succeeds, the semantic rule is marked SKIPPED. A timeout does not count as a pass.
