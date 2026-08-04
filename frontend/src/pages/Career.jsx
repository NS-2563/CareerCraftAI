import { useState } from "react";
import { useLocation } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { RefreshCw } from "lucide-react";

import HamburgerMenu from "@/components/ui/HamburgerMenu";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { formatTimeAgo } from "@/utils/dates";

import CareerAssessmentForm from "@/components/career/CareerAssessmentForm";
import CareerDashboard from "@/components/career/CareerDashboard";
import SkillGapInsights from "@/components/career/SkillGapInsights";
import LoadingState from "@/components/career/LoadingState";
import EmptyState from "@/components/career/EmptyState";
import ErrorState from "@/components/career/ErrorState";

import careerApi from "@/services/careerApi";
import { SuccessBanner } from "@/components/ui/atoms";

export default function Career() {
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [justGenerated, setJustGenerated] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();

  const historyReport = location.state?.report;
  const currentReport = report || historyReport;
  const lastGenerated = currentReport?.generated_at;

  const handleSubmit = async (data) => {
    try {
      setLoading(true);
      setError("");

      const toList = (value) =>
        Array.isArray(value) ? value : value ? [value] : undefined;

      const payload = {
        goal: data.goal || undefined,
        skills: data.skills || undefined,
        education: toList(data.education),
        experience: toList(data.experience),
      };

      const res = await careerApi.generateCareerReport(payload);

      if (res.data.success === false) {
        setError(res.data.error || "Failed to generate report.");
        return;
      }

      setReport(res.data);
      setJustGenerated(true);
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
    setJustGenerated(false);

    navigate("/career", {
      replace: true,
      state: null,
    });

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      setError("");
      const res = await careerApi.refreshRoadmap();
      setReport(res.data);
      setJustGenerated(true);
    } catch (err) {
      console.error(err);
      setError("Couldn't refresh the roadmap right now.");
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-8 space-y-8">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold">Career Coach</h1>
          <p className="text-gray-500 mt-1">
            AI-powered career guidance and roadmap generation
          </p>
        </div>

        {currentReport && (
          <div className="flex items-center gap-3">
            {lastGenerated && (
              <div className="text-right text-xs text-muted-foreground">
                <div>Last updated</div>
                <div className="font-medium text-foreground/80">
                  {formatTimeAgo(lastGenerated)}
                </div>
              </div>
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing || loading}
              className="gap-1.5"
            >
              <RefreshCw className={cn("size-3.5", refreshing && "animate-spin")} />
              {refreshing ? "Refreshing..." : "Refresh with latest data"}
            </Button>
            <HamburgerMenu onNewAssessment={handleNewAssessment} />
          </div>
        )}

        {!currentReport && <HamburgerMenu onNewAssessment={handleNewAssessment} />}
      </div>

      <SkillGapInsights />

      <CareerAssessmentForm onSubmit={handleSubmit} loading={loading} />

      {loading && <LoadingState />}

      {!loading && error && (
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      )}

      {!loading && !error && !report && !historyReport && <EmptyState />}

      {!loading && !error && (report || historyReport) && (
        <>
          {justGenerated && !historyReport && (
            <SuccessBanner
              onDismiss={() => setJustGenerated(false)}
              className="mb-2"
            >
              Career report generated — built from your profile plus your own
              usage signals (saved job matches, interview practice, and real
              interview logs) when they&apos;re available.
            </SuccessBanner>
          )}
          <CareerDashboard report={report || historyReport} />
        </>
      )}
    </div>
  );
}


