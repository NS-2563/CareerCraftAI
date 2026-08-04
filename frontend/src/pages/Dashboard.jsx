import { AlertTriangle, RefreshCw, FileText, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/useAuth";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { IconTile } from "@/components/ui/atoms";

import { useDashboardData } from "@/features/dashboard/hooks/useDashboardData";
import { getGreeting } from "@/features/dashboard/utils/getGreeting";
import { DashboardHero } from "@/features/dashboard/components/DashboardHero";
import { DashboardStatsGrid } from "@/features/dashboard/components/DashboardStatsGrid";
import { DashboardReadinessCard } from "@/features/dashboard/components/DashboardReadinessCard";
import { DashboardFocusCard, DashboardFocusEmpty } from "@/features/dashboard/components/DashboardFocusCard";
import { DashboardTodayFocus, DashboardTodayFocusEmpty } from "@/features/dashboard/components/DashboardTodayFocus";
import { DashboardActivityFeed, DashboardActivityEmpty } from "@/features/dashboard/components/DashboardActivityFeed";
import { DashboardUpcomingTasks, DashboardUpcomingEmpty } from "@/features/dashboard/components/DashboardUpcomingTasks";
import { DashboardHealthScore } from "@/features/dashboard/components/DashboardHealthScore";
import { DashboardMilestones } from "@/features/dashboard/components/DashboardMilestones";
import { DashboardSkeletons } from "@/features/dashboard/components/DashboardSkeletons";

export default function Dashboard() {
  const { user } = useAuth();
  const { data, isLoading, isError, error, refetch } = useDashboardData();

  if (isLoading) {
    return <DashboardSkeletons />;
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-7xl p-4 md:p-0">
        <Card className="border-red-200 p-5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 size-6 shrink-0 text-red-500" />
            <div>
              <h3 className="font-medium text-red-800">Failed to load dashboard</h3>
              <p className="mt-1 text-sm text-red-600">
                {error?.message || "Could not load your dashboard data. Please try again."}
              </p>
              <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-3 gap-1">
                <RefreshCw className="size-4" /> Retry
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (data?.is_empty) {
    return <EmptyDashboard user={user} />;
  }

  const greeting = getGreeting({ user });
  const hasFocusItems = Object.keys(data?.continueItems ?? {}).length > 0;

  return (
    <div className="mx-auto max-w-7xl animate-fade-up space-y-6">
      <div className="grid gap-4 lg:grid-cols-3">
        <DashboardHero
          greeting={greeting}
          recommendedAction={data?.recommendedAction}
          pendingFollowUps={data?.pendingFollowUps ?? 0}
        />
        <DashboardReadinessCard
          readiness={data?.careerReadiness}
          atsLatest={data?.atsLatest}
        />
      </div>

      <DashboardStatsGrid
        resume={data?.resume}
        jobStats={data?.jobStats}
        interview={data?.interview}
        careerReadiness={data?.careerReadiness}
        jobPipeline={data?.jobPipeline}
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="flex flex-col gap-4 lg:col-span-2">
          {hasFocusItems ? (
            <DashboardFocusCard items={data?.continueItems} />
          ) : (
            <DashboardFocusEmpty />
          )}
          {data?.todayFocus ? (
            <DashboardTodayFocus focus={data?.todayFocus} />
          ) : (
            <DashboardTodayFocusEmpty />
          )}
          {data?.recentActivity?.length > 0 ? (
            <DashboardActivityFeed activities={data?.recentActivity} viewAllPath="/activity" />
          ) : (
            <DashboardActivityEmpty onCreate={{ label: "Create your first resume", path: "/resume-studio" }} />
          )}
        </div>
        <div className="flex flex-col gap-4">
          <DashboardHealthScore healthScore={data?.healthScore} />
          <DashboardMilestones milestones={data?.milestones} />
          {data?.upcomingTasks?.length > 0 ? (
            <DashboardUpcomingTasks tasks={data?.upcomingTasks} />
          ) : (
            <DashboardUpcomingEmpty onCreate={{ label: "Track a job application", path: "/jobs" }} />
          )}
        </div>
      </div>
    </div>
  );
}

function EmptyDashboard({ user }) {
  const navigate = useNavigate();
  const { greeting, firstName } = getGreeting({ user });

  return (
    <div className="mx-auto flex min-h-[80vh] max-w-7xl items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <Card
          sheen
          className="relative overflow-hidden p-8 text-center sm:p-12"
          style={{
            background:
              "radial-gradient(130% 120% at 100% 0%, color-mix(in oklch, var(--brand) 20%, transparent), transparent 55%), var(--card)",
          }}
        >
          <div className="mb-6 flex justify-center">
            <IconTile icon={Sparkles} accent="var(--brand)" size="lg" />
          </div>
          <Badge accent="var(--brand)" variant="soft">
            <Sparkles className="size-3" /> Career OS
          </Badge>
          <h1 className="mt-4 font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
            {greeting}
            {firstName ? `, ${firstName}` : ""}. Let's build your{" "}
            <span className="text-primary">career story</span>.
          </h1>
          <p className="mx-auto mt-3 max-w-md text-sm text-muted-foreground">
            Build your resume, get AI-powered feedback, track applications, and prepare for
            interviews — all in one intelligent platform.
          </p>
          <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
            <Button size="lg" onClick={() => navigate("/resume-studio")} className="gap-2">
              <FileText className="size-4" /> Create Your First Resume
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate("/resume")} className="gap-2">
              <Sparkles className="size-4" /> Explore AI Analysis
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
