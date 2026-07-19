import { useMemo, useState } from "react";

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";

import { DialogTrigger } from "@/components/ui/dialog";
import { Alert } from "@/components/ui/alert";

import { initialValues as jobFormInitialValues } from "./JobForm";
import JobForm from "./JobForm";

import { useCreateJob } from "../hooks/useCreateJob";

export default function CreateJobDialog({
  trigger = null,
}) {
  const [open, setOpen] = useState(false);
  const [formApiError, setFormApiError] = useState(null);

  const formInitial = useMemo(() => jobFormInitialValues, []);
  const [formKey, setFormKey] = useState(0);

  const {
    mutate: create,
    isPending,
    error: mutationError,
  } = useCreateJob();

  const apiErrorMessage = mutationError?.response?.data?.detail || mutationError?.message || null;

  function reset() {
    setFormApiError(null);
    setFormKey((k) => k + 1);
  }

  function handleOpenChange(nextOpen) {
    setOpen(nextOpen);
    if (!nextOpen) {
      reset();
    }
  }

  function onSubmit(payload) {
    setFormApiError(null);

    create(payload, {
      onSuccess: () => {
        setOpen(false);
        reset();
      },
      onError: (err) => {
        const msg = err?.response?.data?.detail || err?.message || "Unable to create job.";
        setFormApiError(msg);
      },
    });
  }

  const content = (
    <>
      <DialogHeader>
        <DialogTitle>Create Job</DialogTitle>
        <DialogDescription>Track your next opportunity in the Job Tracker.</DialogDescription>
      </DialogHeader>

      {formApiError || apiErrorMessage ? (
        <Alert variant="destructive">
          {formApiError || apiErrorMessage}
        </Alert>
      ) : null}

      <JobForm
        key={formKey}
        initialFormValues={formInitial}
        onSubmit={onSubmit}
        isSubmitting={isPending}
        apiError={formApiError || apiErrorMessage}
      />

      <DialogFooter showCloseButton={false} />
    </>
  );

  if (!trigger) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-2xl">{content}</DialogContent>
    </Dialog>
  );
}

