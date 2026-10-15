# DesignTrace AI frontend

A React interface for the existing API and component design backend.

## Run locally

Start the backend from the repository root (with its Python dependencies installed):

```sh
cd backend
python3 -m uvicorn app:app --reload --port 8000
```

In a second terminal:

```sh
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite. Vite proxies `/api-component` requests to `http://127.0.0.1:8000`.

Paste the complete backend request into the single **Complete request JSON** field. **Load example** loads `src/components/api-component/banking-example.json`, including requirements, architecture, database, and an authentication NFR with no security mechanism, to exercise the user choice flow. **Format JSON** indents the input. Generation submits the parsed object without dropping NFRs or per-requirement security. Invalid JSON and backend validation errors appear in the form. Results always come from the backend; the frontend does not simulate responses.

The workspace supports BERT semantic results, component responsibilities, generated endpoints, requirement traceability, validation issues, and OpenAPI export. API generation follows the backend configuration (optional Gemini generation with deterministic fallback). Fallback warnings are displayed even when overall validation passes.

Feature code lives in `src/components/api-component/`: `ApiComponentDesign.jsx` provides the workspace, `DesignContext.jsx` the input form, `DesignResults.jsx` the result views, and `useApiDesign.js` the request/state logic. Styles and the sample input are colocated there. `App.jsx` only mounts the feature.

The endpoint detail tables use actual generated fields and OpenAPI parameters. Security, approval, timestamps, or unrelated application modules are not fabricated. View validation displays the checks returned during generation; regeneration runs the complete design pipeline again.

## Production build

```sh
npm run build
```

Serve `dist/` and forward `/api-component` to the backend on the same origin. The Vite development proxy is not included in the production build.

## Missing authentication mechanism

Explicit project or requirement security policies pass through unchanged. When authentication is required but the effective mechanism is unspecified, the backend returns `SECURITY_CONFIGURATION_REQUIRED` before generation. The context form presents an unselected mechanism choice for each affected requirement. **Save choices and regenerate** writes the chosen policies into the JSON and submits the updated request, which the backend saves through its output store. Existing roles, access rules, NFRs, and other explicit policies are preserved. Editing the JSON clears pending choices so they cannot be applied to a different request. Authentication detection currently uses wording cues and structured roles/access rules; it is not a comprehensive security audit.
