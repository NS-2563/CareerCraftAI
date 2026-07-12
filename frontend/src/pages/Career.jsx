import { useState } from "react";
import { useLocation } from "react-router-dom";
import { useNavigate } from "react-router-dom";

import HamburgerMenu from "@/components/ui/HamburgerMenu";

import CareerAssessmentForm from "@/components/career/CareerAssessmentForm";
import CareerDashboard from "@/components/career/CareerDashboard";
import LoadingState from "@/components/career/LoadingState";
import EmptyState from "@/components/career/EmptyState";
import ErrorState from "@/components/career/ErrorState";

import careerApi from "@/services/careerApi";

export default function Career() {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  const location = useLocation();
  const navigate = useNavigate();

  const historyReport = location.state?.report;

  const handleSubmit = async (data) => {
    try {
      setLoading(true);
      setError("");

      const res = await careerApi.generateCareerReport(data);

      if (res.data.success === false) {
        setError(res.data.error || "Failed to generate report.");
        return;
      }

      setReport(res.data);
    } catch (err) {
      console.error(err);
      setError("Failed to generate career report.");
    } finally {
      setLoading(false);
    }
  };

  const handleNewAssessment = () => {
    setReport(null);
    setError("");

    navigate("/career", {
      replace: true,
      state: null,
    });

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  return (
    <div className="max-w-7xl mx-auto p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Career Coach</h1>
          <p className="text-gray-500 mt-1">
            AI-powered career guidance and roadmap generation
          </p>
        </div>

        <HamburgerMenu onNewAssessment={handleNewAssessment} />
      </div>

      <CareerAssessmentForm onSubmit={handleSubmit} loading={loading} />

      {loading && <LoadingState />}

      {!loading && error && (
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      )}

      {!loading && !error && !report && !historyReport && <EmptyState />}

      {!loading && !error && (report || historyReport) && (
        <CareerDashboard report={report || historyReport} />
      )}
    </div>
  );
}


