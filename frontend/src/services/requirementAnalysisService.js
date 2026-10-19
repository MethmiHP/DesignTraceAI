// const API_BASE_URL = "http://127.0.0.1:8000";

// export async function analyzeRequirements(payload) {
//   const response = await fetch(
//     `${API_BASE_URL}/requirements/analyze`,
//     {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify(payload),
//     }
//   );

//   if (!response.ok) {
//     const errorText = await response.text();
//     throw new Error(
//       `Request failed with status ${response.status}: ${errorText}`
//     );
//   }

//   return response.json();
// }

const API_BASE_URL = "http://127.0.0.1:8000";


export async function analyzeManualRequirements({
  projectId,
  rawDescription,
  domain,
  systemType,
}) {
  const response = await fetch(
    `${API_BASE_URL}/requirements/analyze`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        project_id: projectId,

        raw_description: rawDescription,

        project_context: {
          domain: domain || null,
          system_type: systemType || null,
          primary_users: [],
          constraints: [],
          technology_preferences: [],
        },
      }),
    }
  );


  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => null);

    throw new Error(
      errorData?.detail ||
        "Requirement analysis failed."
    );
  }


  return response.json();
}


export async function analyzeRequirementDocument({
  projectId,
  file,
  domain,
  systemType,
}) {
  const formData = new FormData();

  formData.append(
    "project_id",
    projectId
  );

  formData.append(
    "file",
    file
  );


  if (domain) {
    formData.append(
      "domain",
      domain
    );
  }


  if (systemType) {
    formData.append(
      "system_type",
      systemType
    );
  }


  const response = await fetch(
    `${API_BASE_URL}/requirements/analyze-document`,
    {
      method: "POST",
      body: formData,
    }
  );


  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => null);

    throw new Error(
      errorData?.detail ||
        "Document requirement analysis failed."
    );
  }


  return response.json();
}