import { Routes, Route} from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import AppLayout from "./layouts/AppLayout";
import Dashboard from "./pages/Dashboard";
import ResumeAnalysis from "./pages/ResumeAnalysis";
import ResumeStudio from "./pages/ResumeStudio";
import Career from "./pages/Career";
import CareerHistory from "./pages/CareerHistory";
import Analytics from "@/pages/Analytics";
import Interview from "./pages/Interview";
import InterviewDashboardPage from "@/modules/interview/pages/Dashboard";
import InterviewPracticePage from "@/modules/interview/pages/Practice";
import InterviewResultsPage from "@/modules/interview/pages/Results";

import Jobs from "./pages/Jobs";
import Communication from "./pages/Communication";
import Settings from "./pages/Settings";
import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";
import CoverLetterStudio from "./pages/CoverLetterStudio";
import NotFound from "./pages/NotFound";

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes with AppLayout */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Dashboard />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/resume"
          element={
            <ProtectedRoute>
              <AppLayout>
                <ResumeAnalysis />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/resume-studio"
          element={
            <ProtectedRoute>
              <AppLayout>
                <ResumeStudio />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/career"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Career />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route
  path="/career/history"
  element={<CareerHistory />}
/>

<Route
  path="/career/analytics"
  element={<Analytics />}
/>

        <Route
          path="/interview"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Interview />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/practice"
          element={
            <ProtectedRoute>
              <AppLayout>
                <InterviewPracticePage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/results"
          element={
            <ProtectedRoute>
              <AppLayout>
                <InterviewResultsPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/dashboard"
          element={
            <ProtectedRoute>
              <AppLayout>
                <InterviewDashboardPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/jobs"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Jobs />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/communication"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Communication />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/cover-letter-studio"
          element={
            <ProtectedRoute>
              <AppLayout>
                <CoverLetterStudio />
              </AppLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <AppLayout>
                <Settings />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        {/* 404 Not Found */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;