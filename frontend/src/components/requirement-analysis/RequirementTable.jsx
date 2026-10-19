function formatConfidence(value) {
  if (value === null || value === undefined) {
    return "-";
  }

  return `${(Number(value) * 100).toFixed(1)}%`;
}


function getIssueCount(requirement) {
  const issues = requirement?.quality_issues || {};

  return [
    issues.ambiguous,
    issues.incomplete,
    issues.conflicting,
    issues.potentially_missing,
  ].filter(Boolean).length;
}


export default function RequirementTable({
  requirements = [],
}) {
  if (!requirements.length) {
    return null;
  }

  return (
    <section className="requirements-table-section">

      <div className="section-heading">

        <div>
          <h2>
            Requirements List
          </h2>

          <p>
            Extracted atomic requirements with
            classification and quality information.
          </p>
        </div>

        <span className="requirement-count">
          {requirements.length} requirements
        </span>

      </div>


      <div className="requirements-table-wrapper">

        <table className="requirements-table">

          <thead>
            <tr>
              <th>ID</th>
              <th>Requirement</th>
              <th>Type</th>
              <th>Category</th>
              <th>ASR</th>
              <th>Confidence</th>
              <th>Status</th>
            </tr>
          </thead>


          <tbody>

            {requirements.map(
              (requirement) => {

                const issueCount =
                  getIssueCount(
                    requirement
                  );


                return (
                  <tr
                    key={
                      requirement
                        .requirement_id
                    }
                  >

                    <td className="requirement-id-cell">
                      {
                        requirement
                          .requirement_id
                      }
                    </td>


                    <td className="requirement-text-cell">

                      <strong>
                        {
                          requirement
                            .normalized_statement
                        }
                      </strong>


                      {requirement.original_text &&
                        requirement.original_text !==
                          requirement.normalized_statement && (

                          <small>
                            Original:{" "}
                            {
                              requirement
                                .original_text
                            }
                          </small>

                        )}

                    </td>


                    <td>

                      <span
                        className={
                          requirement
                            .requirement_type ===
                          "FR"
                            ? "requirement-type-badge fr"
                            : "requirement-type-badge nfr"
                        }
                      >
                        {
                          requirement
                            .requirement_type
                        }
                      </span>

                    </td>


                    <td>

                      {requirement
                        .quality_attribute ? (

                        <span className="quality-attribute-badge">
                          {
                            requirement
                              .quality_attribute
                          }
                        </span>

                      ) : (

                        <span className="table-muted">
                          -
                        </span>

                      )}

                    </td>


                    <td>

                      <span
                        className={
                          requirement.asr
                            ? "asr-badge yes"
                            : "asr-badge no"
                        }
                      >
                        {
                          requirement.asr
                            ? "Yes"
                            : "No"
                        }
                      </span>

                    </td>


                    <td>

                      <div className="confidence-cell">

                        <span>
                          {
                            formatConfidence(
                              requirement
                                .confidence
                            )
                          }
                        </span>


                        <div className="confidence-track">

                          <div
                            className="confidence-fill"
                            style={{
                              width: `${Math.max(
                                0,
                                Math.min(
                                  100,
                                  Number(
                                    requirement
                                      .confidence ||
                                      0
                                  ) * 100
                                )
                              )}%`,
                            }}
                          />

                        </div>

                      </div>

                    </td>


                    <td>

                      <span
                        className={
                          issueCount > 0
                            ? "issue-count-badge warning"
                            : "issue-count-badge clear"
                        }
                      >
                        {issueCount > 0
                          ? `${issueCount} issue${
                              issueCount > 1
                                ? "s"
                                : ""
                            }`
                          : "Good"}
                      </span>

                    </td>

                  </tr>
                );
              }
            )}

          </tbody>

        </table>

      </div>

    </section>
  );
}