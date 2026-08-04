import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

import { JobStatus } from "../constants/jobStatus";
import { initialValues } from "../constants/jobFormDefaults";


function isValidUrl(url) {
  if (!url) return true;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

function normalizeOptional(value) {
  const v = (value ?? "").trim();
  return v.length ? v : undefined;
}

function normalizeDate(value) {
  const v = (value ?? "").trim();
  return v.length ? v : undefined;
}

export default function JobForm({
  initialFormValues,
  onSubmit,
  isSubmitting = false,
  apiError = null,
}) {
  const [values, setValues] = useState({
    ...initialValues,
    ...(initialFormValues || {}),
  });

  const [touched, setTouched] = useState({});

  const validation = useMemo(() => {
    const errors = {};

    const company = (values.company ?? "").trim();
    const jobTitle = (values.job_title ?? "").trim();

    if (!company) errors.company = "Company is required.";
    if (!jobTitle) errors.job_title = "Job Title is required.";

    if (values.job_url && !isValidUrl(values.job_url)) {
      errors.job_url = "Job URL must be a valid http(s) URL.";
    }

    const appliedDateRaw = (values.applied_date ?? "").trim();
    const deadlineRaw = (values.deadline ?? "").trim();

    if (appliedDateRaw && deadlineRaw) {
      const applied = new Date(appliedDateRaw);
      const deadline = new Date(deadlineRaw);

      if (!Number.isNaN(applied.getTime()) && !Number.isNaN(deadline.getTime())) {
        if (deadline < applied) {
          errors.deadline = "Deadline must be on or after the applied date.";
        }
      }
    }

    return errors;
  }, [values.company, values.job_title, values.job_url, values.applied_date, values.deadline]);


  const isValid = Object.keys(validation).length === 0;

  function setField(field) {
    return (e) => {
      const next = e?.target?.value ?? e;
      setValues((prev) => ({ ...prev, [field]: next }));
    };
  }

  function handleBlur(field) {
    setTouched((prev) => ({ ...prev, [field]: true }));
  }

  const disabled = isSubmitting || !isValid;

  function submitHandler(e) {
    e?.preventDefault?.();

    // Frontend validation gate
    if (!isValid) {
      setTouched({
        company: true,
        job_title: true,
        job_url: true,
        applied_date: true,
        deadline: true,
      });

      return;
    }

    const payload = {
      company: values.company.trim(),
      job_title: values.job_title.trim(),
      status: values.status,
      location: normalizeOptional(values.location),
      source: normalizeOptional(values.source),
      job_url: normalizeOptional(values.job_url),
      notes: normalizeOptional(values.notes),
      applied_date: normalizeDate(values.applied_date),
      deadline: normalizeDate(values.deadline),
    };

    // Remove undefined keys to keep payload clean
    Object.keys(payload).forEach((k) => payload[k] === undefined && delete payload[k]);

    onSubmit?.(payload);
  }

  return (
    <form onSubmit={submitHandler} className="space-y-4">
      {apiError ? (
        <Alert variant="destructive">
          <AlertTitle>Failed to create job</AlertTitle>
          <AlertDescription>{apiError}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="company">Company *</Label>
          <Input
            id="company"
            value={values.company}
            onChange={setField("company")}
            onBlur={() => handleBlur("company")}
            placeholder="e.g., OpenAI"
            disabled={isSubmitting}
            aria-invalid={Boolean(touched.company && validation.company)}
          />
          {touched.company && validation.company ? (
            <p className="text-sm text-destructive">{validation.company}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="job_title">Job Title *</Label>
          <Input
            id="job_title"
            value={values.job_title}
            onChange={setField("job_title")}
            onBlur={() => handleBlur("job_title")}
            placeholder="e.g., Software Engineer"
            disabled={isSubmitting}
            aria-invalid={Boolean(touched.job_title && validation.job_title)}
          />
          {touched.job_title && validation.job_title ? (
            <p className="text-sm text-destructive">{validation.job_title}</p>
          ) : null}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="status">Status</Label>
          <select
            id="status"
            className="h-9 w-full min-w-0 rounded-md border border-input bg-transparent px-2.5 shadow-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50"
            value={values.status}
            onChange={(e) => setValues((p) => ({ ...p, status: e.target.value }))}
            disabled={isSubmitting}
          >
            {Object.values(JobStatus).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="location">Location</Label>
          <Input
            id="location"
            value={values.location}
            onChange={setField("location")}
            placeholder="e.g., Remote / San Francisco"
            disabled={isSubmitting}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="source">Source</Label>
          <Input
            id="source"
            value={values.source}
            onChange={setField("source")}
            placeholder="e.g., LinkedIn"
            disabled={isSubmitting}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="job_url">Job URL</Label>
          <Input
            id="job_url"
            value={values.job_url}
            onChange={setField("job_url")}
            onBlur={() => handleBlur("job_url")}
            placeholder="https://..."
            disabled={isSubmitting}
            aria-invalid={Boolean(touched.job_url && validation.job_url)}
          />
          {touched.job_url && validation.job_url ? (
            <p className="text-sm text-destructive">{validation.job_url}</p>
          ) : null}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="notes">Notes</Label>
        <Textarea
          id="notes"
          value={values.notes}
          onChange={setField("notes")}
          placeholder="Anything you want to remember about this application..."
          rows={4}
          disabled={isSubmitting}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="applied_date">Applied Date</Label>
          <Input
            id="applied_date"
            type="date"
            value={values.applied_date}
            onChange={setField("applied_date")}
            disabled={isSubmitting}
          />

        </div>

        <div className="space-y-2">
          <Label htmlFor="deadline">Deadline</Label>
          <Input
            id="deadline"
            type="date"
            value={values.deadline}
            min={values.applied_date || undefined}
            onChange={setField("deadline")}
            disabled={isSubmitting}
            aria-invalid={Boolean(touched.deadline && validation.deadline)}
          />
          {touched.deadline && validation.deadline ? (
            <p className="text-sm text-destructive">{validation.deadline}</p>
          ) : null}
        </div>

      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        <Button type="submit" disabled={disabled}>
          {isSubmitting ? "Creating..." : "Create Job"}
        </Button>
      </div>
    </form>
  );
}



