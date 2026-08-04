import { Routes, Route} from "react-router-dom";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import AppShell from "@/components/app/AppShell";
import Dashboard from "./pages/Dashboard";
import ActivityTimeline from "./pages/ActivityTimeline";
import ResumeLibrary from "./pages/ResumeLibrary";
import ResumeAnalysis from "./pages/ResumeAnalysis";
import ResumeStudio from "./pages/ResumeStudio";
import Career from "./pages/Career";
import CareerHistory from "./pages/CareerHistory";
import Analytics from "@/pages/Analytics";
import Interview from "./pages/Interview";
import { InterviewProvider } from "@/modules/interview/context/InterviewContext";
import InterviewDashboardPage from "@/modules/interview/pages/Dashboard";
import InterviewPracticePage from "@/modules/interview/pages/Practice";
import InterviewResultsPage from "@/modules/interview/pages/Results";
import InterviewHistoryPage from "@/modules/interview/pages/History";
import InterviewProgressPage from "@/modules/interview/pages/Progress";

import Jobs from "./pages/Jobs";
import Communication from "./pages/Communication";
import Settings from "./pages/Settings";
import Profile from "./pages/Profile";
import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";
import CoverLetterStudio from "./pages/CoverLetterStudio";
import CoverLetterLibrary from "./pages/CoverLetterLibrary";
import NotFound from "./pages/NotFound";

function App() {
  return (
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes with AppShell */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppShell>
                <Dashboard />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/activity"
          element={
            <ProtectedRoute>
              <AppShell>
                <ActivityTimeline />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/resumes"
          element={
            <ProtectedRoute>
              <AppShell>
                <ResumeLibrary />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/resume"
          element={
            <ProtectedRoute>
              <AppShell>
                <ResumeAnalysis />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/resume-studio"
          element={
            <ProtectedRoute>
              <AppShell>
                <ResumeStudio />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/career"
          element={
            <ProtectedRoute>
              <AppShell>
                <Career />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/career/history"
          element={
            <ProtectedRoute>
              <AppShell>
                <CareerHistory />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/career/analytics"
          element={
            <ProtectedRoute>
              <AppShell>
                <Analytics />
              </AppShell>
            </ProtectedRoute>
          }
        />

        <Route
          path="/interview"
          element={
            <ProtectedRoute>
              <AppShell>
                <Interview />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/practice"
          element={
            <ProtectedRoute>
              <AppShell>
                <InterviewProvider>
                  <InterviewPracticePage />
                </InterviewProvider>
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/results"
          element={
            <ProtectedRoute>
              <AppShell>
                <InterviewProvider>
                  <InterviewResultsPage />
                </InterviewProvider>
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/dashboard"
          element={
            <ProtectedRoute>
              <AppShell>
                <InterviewProvider>
                  <InterviewDashboardPage />
                </InterviewProvider>
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/history"
          element={
            <ProtectedRoute>
              <AppShell>
                <InterviewProvider>
                  <InterviewHistoryPage />
                </InterviewProvider>
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/history/:sessionId"
          element={
            <ProtectedRoute>
              <AppShell>
                <InterviewProvider>
                  <InterviewResultsPage />
                </InterviewProvider>
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/progress"
          element={
            <ProtectedRoute>
              <AppShell>
                <InterviewProvider>
                  <InterviewProgressPage />
                </InterviewProvider>
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/jobs"
          element={
            <ProtectedRoute>
              <AppShell>
                <Jobs />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/communication"
          element={
            <ProtectedRoute>
              <AppShell>
                <Communication />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/cover-letter-studio"
          element={
            <ProtectedRoute>
              <AppShell>
                <CoverLetterStudio />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/cover-letter-library"
          element={
            <ProtectedRoute>
              <AppShell>
                <CoverLetterLibrary />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <AppShell>
                <Profile />
              </AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <AppShell>
                <Settings />
              </AppShell>
            </ProtectedRoute>
          }
        />

        {/* 404 Not Found */}
        <Route path="*" element={<NotFound />} />
      </Routes>
  );
}

export default App;

