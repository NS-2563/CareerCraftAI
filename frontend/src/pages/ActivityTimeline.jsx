import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  History,
  AlertCircle,
  Filter,
  ChevronDown,
} from "lucide-react";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Timeline, Skeleton } from "@/components/ui/atoms";
import { accentFor, iconFor, moduleForEvent } from "@/features/dashboard/utils/moduleLookup";
import { formatTimeAgo, formatGroupDay } from "@/utils/dates";
import activityApi from "@/services/activityApi";
import { getJobs } from "@/modules/jobTracker/api/jobTrackerApi";

const PAGE_SIZE = 50;

const EVENT_TYPE_GROUPS = [
  {
    label: "Resume",
    options: [
      { value: "resume_created", label: "Resume created" },
      { value: "resume_updated", label: "Resume updated" },
      { value: "resume_duplicated", label: "Resume duplicated" },
      { value: "resume_deleted", label: "Resume deleted" },
      { value: "analysis_completed", label: "Resume analyzed" },
    ],
  },
  {
    label: "Cover letters",
    options: [
      { value: "cover_letter_created", label: "Cover letter created" },
      { value: "cover_letter_generated", label: "Cover letter generated" },
      { value: "cover_letter_updated", label: "Cover letter updated" },
      { value: "cover_letter_duplicated", label: "Cover letter duplicated" },
      { value: "cover_letter_deleted", label: "Cover letter deleted" },
    ],
  },
  {
    label: "Job tracker",
    options: [
      { value: "job_application_created", label: "Application created" },
      { value: "job_application_status_changed", label: "Status changed" },
      { value: "job_application_updated", label: "Application updated" },
      { value: "job_application_deleted", label: "Application deleted" },
      { value: "job_description_added", label: "Job description added" },
      { value: "job_description_updated", label: "Job description updated" },
    ],
  },
  {
    label: "Resume match",
    options: [{ value: "jd_match_analyzed", label: "JD match analyzed" }],
  },
  {
    label: "Communication",
    options: [
      { value: "communication_message_generated", label: "Message generated" },
      { value: "communication_message_created", label: "Message created" },
      { value: "communication_message_received", label: "Message received" },
    ],
  },
  {
    label: "Interviews",
    options: [
      { value: "interview_questions_generated", label: "Questions generated" },
      { value: "interview_session_created", label: "Practice started" },
      { value: "interview_session_completed", label: "Session completed" },
    ],
  },
  {
    label: "Career coach",
    options: [{ value: "career_report_generated", label: "Report generated" }],
  },
];

function groupByDay(events) {
  const groups = [];
  for (const e of events) {
    const day = formatGroupDay(e.created_at);
    const last = groups[groups.length - 1];
    if (last && last.day === day) {
      last.items.push(e);
    } else {
      groups.push({ day, items: [e] });
    }
  }
  return groups;
}

export default function ActivityTimeline() {
  const navigate = useNavigate();
  const [eventType, setEventType] = useState("");
  const [jobAppId, setJobAppId] = useState("");
  const [limit, setLimit] = useState(PAGE_SIZE);

  const applicationsQuery = useQuery({
    queryKey: ["activity-applications"],
    staleTime: 60_000,
    queryFn: () => getJobs().then((res) => (Array.isArray(res) ? res : [])),
  });
  const applications = applicationsQuery.data ?? [];

  const feedQuery = useQuery({
    queryKey: ["activity-feed", eventType || "all", jobAppId || "all", limit],
    staleTime: 30_000,
    queryFn: () =>
      activityApi
        .getFeed({
          eventType: eventType || undefined,
          jobApplicationId: jobAppId || undefined,
          limit,
          offset: 0,
        })
        .then((res) => res.data?.data ?? { items: [], total: 0, has_more: false }),
  });

  const feedData = useMemo(() => feedQuery.data ?? { items: [], total: 0, has_more: false }, [feedQuery.data]);
  const events = feedData.items;
  const total = feedData.total;
  const hasMore = Boolean(feedData.has_more);

  const groups = useMemo(() => groupByDay(events), [events]);

  const filtered = eventType !== "" || jobAppId !== "";
  const hasFilters = filtered;

  function openApplication(item) {
    if (item.jobAppId != null) {
      navigate(`/jobs?viewJob=${item.jobAppId}`);
    }
  }

  const timelineItems = useMemo(
    () =>
      events.map((e) => {
        const moduleId = moduleForEvent(e.event_type);
        const accent = moduleId ? accentFor(moduleId) : "var(--brand)";
        return {
          id: e.id,
          title: e.title,
          subtitle: e.description,
          timestamp: formatTimeAgo(e.created_at),
          accentColor: accent,
          linkable: e.related_job_application_id != null,
          jobAppId: e.related_job_application_id,
        };
      }),
    [events],
  );

  const handleFilterChange = (setter) => (e) => {
    setter(e.target.value);
    setLimit(PAGE_SIZE);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8 animate-in fade-in duration-200">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/[0.04] via-primary/[0.02] to-background border border-border/50 p-8 md:p-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,hsl(var(--primary)/0.06),transparent_70%)]" />
        <div className="relative space-y-4">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary/15 to-primary/5 ring-1 ring-primary/10">
              <History className="size-4 text-primary" />
            </div>
            <span className="text-xs font-semibold tracking-[0.15em] text-muted-foreground uppercase">
              Activity
            </span>
          </div>
          <div className="space-y-2">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Activity Timeline</h1>
            <p className="text-base text-muted-foreground max-w-xl leading-relaxed">
              Your full cross-module history — resume edits, applications, messages, interviews,
              and insights — in one chronological view.
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-4" sheen>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Filter className="size-4" />
            <span>
              {feedQuery.isSuccess ? `${total} event${total === 1 ? "" : "s"}` : "Loading…"}
            </span>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <div className="relative">
              <select
                value={eventType}
                onChange={handleFilterChange(setEventType)}
                className="h-8 rounded-lg border border-input bg-transparent px-2.5 pr-8 text-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 cursor-pointer w-full sm:w-auto"
                aria-label="Filter by event type"
              >
                <option value="">All activity</option>
                {EVENT_TYPE_GROUPS.map((group) => (
                  <optgroup key={group.label} label={group.label}>
                    {group.options.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            </div>
            <div className="relative">
              <select
                value={jobAppId}
                onChange={handleFilterChange(setJobAppId)}
                className="h-8 rounded-lg border border-input bg-transparent px-2.5 pr-8 text-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 cursor-pointer w-full sm:w-auto"
                aria-label="Filter by application"
              >
                <option value="">All applications</option>
                {applications.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.company} — {job.job_title || "Position"}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            </div>
            {hasFilters && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setEventType("");
                  setJobAppId("");
                  setLimit(PAGE_SIZE);
                }}
              >
                Clear filters
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Feed */}
      {feedQuery.isPending ? (
        <div className="space-y-4">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-14 rounded-xl" />
          ))}
        </div>
      ) : feedQuery.isError ? (
        <Card className="p-8" sheen>
          <div className="flex flex-col items-center justify-center gap-2 text-center">
            <AlertCircle className="size-6 text-muted-foreground/60" />
            <p className="text-sm font-medium">Couldn&apos;t load your activity</p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => feedQuery.refetch()}
            >
              Retry
            </Button>
          </div>
        </Card>
      ) : events.length === 0 ? (
        <Card className="p-10" sheen>
          <div className="flex flex-col items-center justify-center gap-2 text-center">
            <History className="size-7 text-muted-foreground/60" />
            <p className="text-sm font-medium">
              {hasFilters ? "No activity matches these filters" : "No activity yet"}
            </p>
            <p className="text-xs text-muted-foreground max-w-sm">
              {hasFilters
                ? "Try widening your filters to see more history."
                : "Resume edits, applications, messages, and interviews will appear here."}
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-6">
          {groups.map((group) => (
            <div key={group.day}>
              <p className="mb-3 text-xs font-medium text-muted-foreground">{group.day}</p>
              <Card className="p-5" sheen>
                <Timeline
                  items={timelineItems.filter((t) => group.items.some((e) => e.id === t.id))}
                  iconFor={(item) => {
                    const ev = events.find((e) => e.id === item.id);
                    const moduleId = ev ? moduleForEvent(ev.event_type) : null;
                    return moduleId ? iconFor(moduleId) : null;
                  }}
                  onItemClick={openApplication}
                />
              </Card>
            </div>
          ))}

          {hasMore && (
            <div className="flex justify-center">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setLimit((l) => l + PAGE_SIZE)}
              >
                Load more
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
