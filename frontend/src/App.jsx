import "./App.css";

import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import RequirementAnalysisPage from "./pages/RequirementAnalysis/RequirementAnalysisPage";
import RequirementAnalysisResultsPage from "./pages/RequirementAnalysis/RequirementAnalysisResultsPage";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Navigate
              to="/requirements"
              replace
            />
          }
        />

        <Route
          path="/requirements"
          element={
            <RequirementAnalysisPage />
          }
        />

        <Route
          path="/requirements/results"
          element={
            <RequirementAnalysisResultsPage />
          }
        />
      </Routes>
    </BrowserRouter>
  );
}


export default App;