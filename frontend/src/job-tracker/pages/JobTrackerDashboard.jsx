import { useMemo, useState } from "react";
import { Plus } from "lucide-react";


import { Button } from "@/components/ui/button";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";


import StatsGrid from "../components/StatsGrid";
import JobDashboardLoading from "../components/JobDashboardLoading";
import JobDashboardError from "../components/JobDashboardError";
import JobDashboardEmpty from "../components/JobDashboardEmpty";

import JobTable from "../components/JobTable";
import JobTableLoading from "../components/JobTableLoading";
import JobTableEmpty from "../components/JobTableEmpty";

import { useJob } from "@/job-tracker/hooks/useJob";
import { useJobStats } from "@/job-tracker/hooks/useJobStats";
import { useJobs } from "@/job-tracker/hooks/useJobs";
import { useUpdateJob } from "@/job-tracker/hooks/useUpdateJob";
import { useDeleteJob } from "@/job-tracker/hooks/useDeleteJob";

import CreateJobDialog from "../components/CreateJobDialog";
import JobForm, { initialValues as jobFormInitialValues } from "../components/JobForm";
import { JobStatusBadge } from "../components/JobStatusBadge";





function formatNumber(value) {
  if (value === null || value === undefined) return 0;
  const num = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(num) ? num : 0;
}

export default function JobTrackerDashboard() {
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

  const [selectedJobId, setSelectedJobId] = useState(null);
  const [viewOpen, setViewOpen] = useState(false);
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
          <JobTableEmpty />
        ) : jobs.length === 0 ? (
          <JobTableEmpty />
        ) : (
          <JobTable
            jobs={jobs}
            formatDate={formatDate}
            onView={(job) => {
              setSelectedJobId(job?.id);
              setViewOpen(true);
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
          />
        )}
      </div>

      <Dialog open={viewOpen} onOpenChange={setViewOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Job Details</DialogTitle>
            <DialogDescription>Review the selected job application.</DialogDescription>
          </DialogHeader>

          {isSelectedJobLoading ? (
            <div className="py-6">Loading...</div>
          ) : isSelectedJobError ? (
            <Alert variant="destructive">
              <AlertTitle>Unable to load job</AlertTitle>
              <AlertDescription>
                {selectedJobError?.response?.data?.detail || selectedJobError?.message || "Failed to load job."}
              </AlertDescription>
            </Alert>
          ) : selectedJobData ? (
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Company</div>
                  <div className="font-medium">{selectedJobData.company || "—"}</div>
                </div>
                <JobStatusBadge status={selectedJobData.status} />
              </div>

              <Separator />

              <div className="space-y-2 text-sm">
                <div className="flex justify-between gap-6">
                  <div className="text-muted-foreground">Job Title</div>
                  <div className="font-medium">{selectedJobData.job_title || "—"}</div>
                </div>
                <div className="flex justify-between gap-6">
                  <div className="text-muted-foreground">Location</div>
                  <div className="font-medium">{selectedJobData.location || "—"}</div>
                </div>
                <div className="flex justify-between gap-6">
                  <div className="text-muted-foreground">Source</div>
                  <div className="font-medium">{selectedJobData.source || "—"}</div>
                </div>
                <div className="flex justify-between gap-6">
                  <div className="text-muted-foreground">Job URL</div>
                  <div className="font-medium break-all">
                    {selectedJobData.job_url ? (
                      <a
                        href={selectedJobData.job_url}
                        target="_blank"
                        rel="noreferrer"
                        className="underline"
                      >
                        {selectedJobData.job_url}
                      </a>
                    ) : (
                      "—"
                    )}
                  </div>
                </div>
                <div className="flex justify-between gap-6">
                  <div className="text-muted-foreground">Applied Date</div>
                  <div className="font-medium">{formatDate(selectedJobData.applied_date)}</div>
                </div>
                <div className="flex justify-between gap-6">
                  <div className="text-muted-foreground">Deadline</div>
                  <div className="font-medium">{formatDate(selectedJobData.deadline)}</div>
                </div>
              </div>

              {selectedJobData.notes ? (
                <div>
                  <div className="text-sm text-muted-foreground">Notes</div>
                  <div className="mt-1 whitespace-pre-wrap text-sm">{selectedJobData.notes}</div>
                </div>
              ) : null}

              <DialogFooter>
                <Button type="button" variant="secondary" onClick={() => setViewOpen(false)}>
                  Close
                </Button>
              </DialogFooter>
            </div>
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
            <div className="py-6">Loading...</div>
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


