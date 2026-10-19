import { useEffect, useState } from "react";
import {
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  analyzeManualRequirements,
  analyzeRequirementDocument,
} from "../../services/requirementAnalysisService";


const DRAFT_STORAGE_KEY =
  "designtrace-requirement-draft";


export default function RequirementInput() {
  const navigate = useNavigate();
  const location = useLocation();


  const getInitialDraft = () => {
    // First priority:
    // draft passed directly from Results -> Edit Requirements
    if (location.state?.draft) {
      return location.state.draft;
    }

    // Second priority:
    // previously saved browser-session draft
    try {
      const savedDraft =
        sessionStorage.getItem(
          DRAFT_STORAGE_KEY
        );

      if (savedDraft) {
        return JSON.parse(
          savedDraft
        );
      }
    } catch (error) {
      console.error(
        "Unable to restore requirement draft:",
        error
      );
    }

    return {};
  };


  const initialDraft = getInitialDraft();


  const [mode, setMode] = useState(
    initialDraft.mode || "document"
  );

  const [projectId, setProjectId] = useState(
    initialDraft.projectId || ""
  );

  const [domain, setDomain] = useState(
    initialDraft.domain || ""
  );

  const [systemType, setSystemType] = useState(
    initialDraft.systemType || ""
  );

  const [manualText, setManualText] = useState(
    initialDraft.manualText || ""
  );

  const [selectedFile, setSelectedFile] = useState(
    initialDraft.selectedFile || null
  );

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");


  // SAVE CURRENT FORM DRAFT
  useEffect(() => {
    const draft = {
      mode,
      projectId,
      domain,
      systemType,
      manualText,

      // Files cannot be serialized into sessionStorage.
      // Keep the name only as useful metadata.
      selectedFileName:
        selectedFile?.name || null,
    };


    try {
      sessionStorage.setItem(
        DRAFT_STORAGE_KEY,
        JSON.stringify(draft)
      );
    } catch (error) {
      console.error(
        "Unable to save requirement draft:",
        error
      );
    }

  }, [
    mode,
    projectId,
    domain,
    systemType,
    manualText,
    selectedFile,
  ]);


  // FILE CHANGE

  const handleFileChange = (event) => {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
    setError("");
  };


  // MODE CHANGE

  const handleModeChange = (
    newMode
  ) => {
    setMode(newMode);
    setError("");
  };


  // SUBMIT

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    setError("");


    if (!projectId.trim()) {
      setError(
        "Project ID is required."
      );

      return;
    }


    if (
      mode === "manual" &&
      manualText.trim().length < 10
    ) {
      setError(
        "Please enter at least 10 characters of requirement text."
      );

      return;
    }


    if (
      mode === "document" &&
      !selectedFile
    ) {
      setError(
        "Please select a TXT, PDF, or DOCX file."
      );

      return;
    }


    try {
      setLoading(true);

      let response;


      // MANUAL ANALYSIS

      if (mode === "manual") {
        response =
          await analyzeManualRequirements({
            projectId:
              projectId.trim(),

            rawDescription:
              manualText.trim(),

            domain:
              domain.trim(),

            systemType:
              systemType.trim(),
          });
      }


      // DOCUMENT ANALYSIS

      else {
        response =
          await analyzeRequirementDocument({
            projectId:
              projectId.trim(),

            file:
              selectedFile,

            domain:
              domain.trim(),

            systemType:
              systemType.trim(),
          });
      }


      // SAVE DRAFT

      const draft = {
        mode,

        projectId:
          projectId.trim(),

        domain:
          domain.trim(),

        systemType:
          systemType.trim(),

        manualText,

        // This File object is passed through React Router
        // so clicking Edit Requirements can restore it
        // without immediately losing it.
        selectedFile,
      };


      // Store serializable version for refresh recovery.
      sessionStorage.setItem(
        DRAFT_STORAGE_KEY,
        JSON.stringify({
          mode,

          projectId:
            projectId.trim(),

          domain:
            domain.trim(),

          systemType:
            systemType.trim(),

          manualText,

          selectedFileName:
            selectedFile?.name || null,
        })
      );


      // Store result too, so refreshing the result page
      // does not immediately lose the analysis.
      sessionStorage.setItem(
        "designtrace-requirement-result",
        JSON.stringify(response)
      );


      // GO TO RESULTS PAGE

      navigate(
        "/requirements/results",
        {
          state: {
            result: response,
            draft,
          },
        }
      );

    } catch (err) {
      setError(
        err.message ||
          "Requirement analysis failed."
      );
    } finally {
      setLoading(false);
    }
  };


  return (
    <section className="requirement-card">

      {/* INPUT MODE */}

      <div className="input-tabs">

        <button
          type="button"
          className={
            mode === "document"
              ? "input-tab active"
              : "input-tab"
          }
          onClick={() =>
            handleModeChange(
              "document"
            )
          }
        >
          Upload Document
        </button>


        <button
          type="button"
          className={
            mode === "manual"
              ? "input-tab active"
              : "input-tab"
          }
          onClick={() =>
            handleModeChange(
              "manual"
            )
          }
        >
          Enter Manually
        </button>

      </div>


      {/* FORM */}

      <form
        className="requirement-form"
        onSubmit={handleSubmit}
      >

        <div className="form-grid">

          {/* PROJECT ID */}

          <div className="form-field">

            <label htmlFor="projectId">
              Project ID
            </label>

            <input
              id="projectId"
              type="text"
              value={projectId}
              onChange={(event) =>
                setProjectId(
                  event.target.value
                )
              }
              placeholder="e.g. UNIVERSITY-001"
            />

          </div>


          {/* DOMAIN */}

          <div className="form-field">

            <label htmlFor="domain">
              Domain
            </label>

            <input
              id="domain"
              type="text"
              value={domain}
              onChange={(event) =>
                setDomain(
                  event.target.value
                )
              }
              placeholder="e.g. Education"
            />

          </div>


          {/* SYSTEM TYPE */}

          <div className="form-field">

            <label htmlFor="systemType">
              System Type
            </label>

            <input
              id="systemType"
              type="text"
              value={systemType}
              onChange={(event) =>
                setSystemType(
                  event.target.value
                )
              }
              placeholder="e.g. Web Application"
            />

          </div>

        </div>


        {/* DOCUMENT MODE*/}

        {mode === "document" && (
          <div className="upload-section">

            <label
              className="upload-box"
              htmlFor="requirementFile"
            >

              <div className="upload-icon">
                ↑
              </div>


              <div>

                <strong>
                  Upload Requirement Document
                </strong>

                <p>
                  Supported formats:
                  PDF, DOCX, TXT
                </p>

                <span>
                  Click to browse your files
                </span>

              </div>


              <input
                id="requirementFile"
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={
                  handleFileChange
                }
                hidden
              />

            </label>


            {selectedFile && (
              <div className="selected-file">

                <div>

                  <strong>
                    {selectedFile.name}
                  </strong>

                  <small>
                    {(
                      selectedFile.size /
                      1024
                    ).toFixed(1)}{" "}
                    KB
                  </small>

                </div>


                <button
                  type="button"
                  onClick={() =>
                    setSelectedFile(
                      null
                    )
                  }
                >
                  Remove
                </button>

              </div>
            )}


            {!selectedFile &&
              initialDraft.selectedFileName && (

                <div className="analysis-error">

                  Previous file:{" "}
                  {
                    initialDraft
                      .selectedFileName
                  }

                  <br />

                  Please select the file
                  again before re-running
                  document analysis.

                </div>

              )}

          </div>
        )}


        {/* MANUAL MODE */}

        {mode === "manual" && (

          <div className="form-field">

            <label htmlFor="manualText">
              Requirement Description
            </label>

            <textarea
              id="manualText"
              rows="12"
              value={manualText}
              onChange={(event) =>
                setManualText(
                  event.target.value
                )
              }
              placeholder={
                "Enter the project description or software requirements here..."
              }
            />

          </div>

        )}


        {/* ERROR */}

        {error && (
          <div className="analysis-error">
            {error}
          </div>
        )}


        {/* ANALYZE */}

        <div className="requirement-form-actions">

          <button
            className="analyze-button"
            type="submit"
            disabled={loading}
          >

            {loading
              ? "Analyzing Requirements..."
              : "Analyze Requirements"}

          </button>

        </div>

      </form>

    </section>
  );
}