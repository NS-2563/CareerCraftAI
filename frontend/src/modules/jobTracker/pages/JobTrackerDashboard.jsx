import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Plus } from "lucide-react";
import { useSuggestions } from "@/communication/hooks/useSuggestions";
import ApplicationLinkedResources from "../components/ApplicationLinkedResources";


import { Button } from "@/components/ui/button";

import { Skeleton } from "@/components/ui/skeleton";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";


import StatsGrid from "../components/StatsGrid";
import JobDashboardLoading from "../components/JobDashboardLoading";
import JobDashboardError from "../components/JobDashboardError";
import JobDashboardEmpty from "../components/JobDashboardEmpty";

import JobTable from "../components/JobTable";
import JobTableLoading from "../components/JobTableLoading";
import JobTableEmpty from "../components/JobTableEmpty";

import { useJob } from "@/modules/jobTracker/hooks/useJob";
import { useJobStats } from "@/modules/jobTracker/hooks/useJobStats";
import { useJobs } from "@/modules/jobTracker/hooks/useJobs";
import { useUpdateJob } from "@/modules/jobTracker/hooks/useUpdateJob";
import { useDeleteJob } from "@/modules/jobTracker/hooks/useDeleteJob";

import CreateJobDialog from "../components/CreateJobDialog";
import JobForm from "../components/JobForm";
import { initialValues as jobFormInitialValues } from "../constants/jobFormDefaults";





function formatNumber(value) {
  if (value === null || value === undefined) return 0;
  const num = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(num) ? num : 0;
}

export default function JobTrackerDashboard() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const {
    data: statsData,
    isLoading: isStatsLoading,
    isError: isStatsError,
    error: statsError,
  } = useJobStats();

  const {
    data: jobsData,
    isLoading: isJobsLoading,
    isError: isJobsError,
  } = useJobs();

  const [selectedJobId, setSelectedJobId] = useState(() => {
    const viewJob = searchParams.get("viewJob");
    return viewJob ? Number(viewJob) : null;
  });
  const [createOpen, setCreateOpen] = useState(false);
  const [viewOpen, setViewOpen] = useState(() => searchParams.has("viewJob"));
  const [viewTab, setViewTab] = useState(() =>
    searchParams.get("tab") === "communication" ? "communication" : "details"
  );
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const selectedJobNumericId =
    selectedJobId === null || selectedJobId === undefined
      ? undefined
      : Number(selectedJobId);

  const {
    data: selectedJobData,
    isLoading: isSelectedJobLoading,
    isError: isSelectedJobError,
    error: selectedJobError,
  } = useJob(selectedJobNumericId, { enabled: selectedJobNumericId !== undefined });

  const [formKey, setFormKey] = useState(0);

  const jobs = Array.isArray(jobsData) ? jobsData : [];

  const { data: suggestions = [] } = useSuggestions();
  const suggestionJobIds = useMemo(
    () => new Set(suggestions.map((s) => Number(s.job_application_id))),
    [suggestions]
  );

  const stats = useMemo(() => {
    const s = statsData || {};

    return [
      {
        key: "total_applications",
        title: "Total Applications",
        value: formatNumber(s.total_applications ?? s.totalApplications),
      },
      { key: "wishlist", title: "Wishlist", value: formatNumber(s.wishlist) },
      { key: "applied", title: "Applied", value: formatNumber(s.applied) },
      { key: "interview", title: "Interview", value: formatNumber(s.interview) },
      { key: "offer", title: "Offer", value: formatNumber(s.offer) },
      { key: "accepted", title: "Accepted", value: formatNumber(s.accepted) },
      { key: "rejected", title: "Rejected", value: formatNumber(s.rejected) },
      {
        key: "withdrawn",
        title: "Withdrawn",
        value: formatNumber(s.withdrawn),
      },
    ];
  }, [statsData]);

  const isEmpty = !isStatsLoading && !isStatsError && stats.every((s) => s.value === 0);

  const errorMessage =
    statsError?.response?.data?.detail ||
    statsError?.message ||
    "Unable to load job statistics.";

  const Header = (
    <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-xl font-semibold leading-tight">Job Tracker</h1>
        <p className="text-sm text-muted-foreground">Track your applications end-to-end.</p>
      </div>

      <CreateJobDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        trigger={
          <Button type="button" variant="secondary" disabled={isStatsLoading}>
            <Plus className="mr-2 h-4 w-4" />
            Add Job
          </Button>
        }
      />
    </header>
  );


  const formatDate = (d) => {
    if (!d) return "—";
    try {
      return new Date(d).toLocaleDateString();
    } catch {
      return "—";
    }
  };

  const {
    mutate: updateJob,
    isPending: isUpdating,
    error: updateError,
  } = useUpdateJob();



  const {
    mutate: deleteJob,
    isPending: isDeleting,
    error: deleteError,
  } = useDeleteJob();


  function getJobFormInitialValues(job) {
    if (!job) return jobFormInitialValues;

    return {
      company: job.company ?? "",
      job_title: job.job_title ?? "",
      status: job.status ?? jobFormInitialValues.status,
      location: job.location ?? "",
      source: job.source ?? "",
      job_url: job.job_url ?? "",
      notes: job.notes ?? "",
      applied_date: job.applied_date ? String(job.applied_date) : "",
      deadline: job.deadline ? String(job.deadline) : "",
    };
  }


  if (isStatsLoading) {
    return (
      <div className="space-y-4">
        {Header}
        <JobDashboardLoading />
      </div>
    );
  }

  if (isStatsError) {
    return (
      <div className="space-y-4">
        {Header}
        <JobDashboardError message={errorMessage} />
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="space-y-4">
        {Header}
        <JobDashboardEmpty />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {Header}
      <StatsGrid stats={stats} />

      <div className="pt-2">
        {isJobsLoading ? (
          <JobTableLoading />
        ) : isJobsError ? (
          <JobTableEmpty onCreate={() => setCreateOpen(true)} />
        ) : jobs.length === 0 ? (
          <JobTableEmpty onCreate={() => setCreateOpen(true)} />
        ) : (
          <JobTable
            jobs={jobs}
            formatDate={formatDate}
            suggestionJobIds={suggestionJobIds}
            onView={(job) => {
              setSelectedJobId(job?.id);
              setViewOpen(true);
              setViewTab("details");
              setEditOpen(false);
              setDeleteOpen(false);
            }}
            onEdit={(job) => {
              setSelectedJobId(job?.id);
              setEditOpen(true);
              setViewOpen(false);
              setDeleteOpen(false);
              setFormKey((k) => k + 1);
            }}
            onDelete={(job) => {
              setSelectedJobId(job?.id);
              setDeleteOpen(true);
              setViewOpen(false);
              setEditOpen(false);
            }}
            onDraftMessage={(job) => {
              navigate(`/communication?jobId=${job.id}`);
            }}
          />
        )}
      </div>

      <Dialog open={viewOpen} onOpenChange={(next) => {
        setViewOpen(next);
        if (!next) {
          if (searchParams.has("viewJob")) {
            setSearchParams({});
          }
        }
      }}>
        <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto p-0 gap-0">
          <DialogTitle className="sr-only">Job Details</DialogTitle>

          {isSelectedJobLoading ? (
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-6 w-24" />
              </div>
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          ) : isSelectedJobError ? (
            <div className="p-6">
              <Alert variant="destructive">
                <AlertTitle>Unable to load job</AlertTitle>
                <AlertDescription>
                  {selectedJobError?.response?.data?.detail || selectedJobError?.message || "Failed to load job."}
                </AlertDescription>
              </Alert>
            </div>
          ) : selectedJobData ? (
            <ApplicationLinkedResources
              job={selectedJobData}
              initialTab={viewTab === "communication" ? "communication" : "resume"}
              onTabChange={setViewTab}
            />
          ) : null}
        </DialogContent>
      </Dialog>

      <Dialog open={editOpen} onOpenChange={(next) => {
        setEditOpen(next);
        if (!next) {
          setSelectedJobId(null);
        }
      }}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Job</DialogTitle>
            <DialogDescription>Update the selected job application.</DialogDescription>
          </DialogHeader>



          {isSelectedJobError ? (
            <Alert variant="destructive">
              <AlertTitle>Unable to load job</AlertTitle>
              <AlertDescription>
                {selectedJobError?.response?.data?.detail || selectedJobError?.message || "Failed to load job."}
              </AlertDescription>
            </Alert>
          ) : null}

          {updateError ? (
            <Alert variant="destructive">
              <AlertTitle>Failed to update job</AlertTitle>
              <AlertDescription>
                {updateError?.response?.data?.detail || updateError?.message || "Unable to update job."}
              </AlertDescription>
            </Alert>
          ) : null}

          {isSelectedJobLoading ? (
            <div className="py-6 space-y-4">
              <Skeleton className="h-5 w-1/3" />
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-20 w-full" />
              <div className="flex justify-end gap-2 pt-2">
                <Skeleton className="h-9 w-24" />
                <Skeleton className="h-9 w-32" />
              </div>
            </div>
          ) : (
            <JobForm

              key={formKey}
              initialFormValues={getJobFormInitialValues(selectedJobData)}
              onSubmit={(payload) => {
                if (!selectedJobData?.id) return;
                updateJob(
                  { id: selectedJobData.id, data: payload },
                  {
                    onSuccess: () => {
                      setEditOpen(false);
                      setSelectedJobId(null);
                    },
                  }
                );
              }}
              isSubmitting={isUpdating}
            />
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete Job</DialogTitle>
            <DialogDescription>
              This action can’t be undone. Are you sure you want to delete this job application?
            </DialogDescription>
          </DialogHeader>

          {deleteError ? (
            <Alert variant="destructive">
              <AlertTitle>Delete failed</AlertTitle>
              <AlertDescription>
                {deleteError?.response?.data?.detail || deleteError?.message || "Unable to delete job."}
              </AlertDescription>
            </Alert>
          ) : null}

          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => setDeleteOpen(false)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={() => {
                if (
                  selectedJobNumericId === null ||
                  selectedJobNumericId === undefined
                )
                  return;
                deleteJob(selectedJobNumericId, {

                  onSuccess: () => {
                    setDeleteOpen(false);
                    setSelectedJobId(null);
                  },
                });
              }}
              disabled={isDeleting}
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}


