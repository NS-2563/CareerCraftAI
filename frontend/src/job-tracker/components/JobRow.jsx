import { Eye, Pencil, Trash2 } from "lucide-react";

import { cn } from "@/lib/utils";

import { JobStatusBadge } from "./JobStatusBadge";

export default function JobRow({
  job,
  formatDate,
  onView = () => {},
  onEdit = () => {},
  onDelete = () => {},
}) {
  return (
    <tr className={cn("border-b last:border-b-0")}> 
      <td className="px-4 py-4 align-top whitespace-nowrap">
        {job.company || "—"}
      </td>
      <td className="px-4 py-4 align-top whitespace-nowrap">
        {job.job_title || "—"}
      </td>
      <td className="px-4 py-4 align-top">{job.status || "—"}</td>
      <td className="px-4 py-4 align-top">{job.location || "—"}</td>
      <td className="px-4 py-4 align-top whitespace-nowrap">
        {formatDate(job.applied_date)}
      </td>
      <td className="px-4 py-4 align-top whitespace-nowrap">
        {formatDate(job.deadline)}
      </td>
      <td className="px-4 py-4 align-top">{job.source || "—"}</td>
      <td className="px-4 py-4 align-top">
        <div className="flex items-center gap-2">
          <button
            type="button"
            aria-label="View"
            onClick={onView}
            className="inline-flex items-center justify-center rounded-md p-1 hover:bg-muted"
          >
            <Eye className="h-4 w-4" />
          </button>
          <button
            type="button"
            aria-label="Edit"
            onClick={onEdit}
            className="inline-flex items-center justify-center rounded-md p-1 hover:bg-muted"
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button
            type="button"
            aria-label="Delete"
            onClick={onDelete}
            className="inline-flex items-center justify-center rounded-md p-1 hover:bg-muted text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </td>
      <td className="px-4 py-4 align-top">
        <JobStatusBadge status={job.status} />
      </td>
    </tr>
  );
}

