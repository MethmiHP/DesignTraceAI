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

The dashboard includes category pass rates, NFR coverage, severity filters, expandable evidence, recommendations, related findings, skipped checks, session history, and JSON report export. N/A values remain N/A. History holds the most recent 20 responses in memory and resets on reload. It is not server history. No numerical demo results or external standard compliance claims are fabricated.

`useQualityEvaluation.js` manages requests and state; `QualityEvaluation.jsx` renders the interface; `quality-evaluation.css` provides responsive layout and theme variables; `example.json` is the backend-compatible sample input.

Checks: `npm run lint` and `npm run build`.
