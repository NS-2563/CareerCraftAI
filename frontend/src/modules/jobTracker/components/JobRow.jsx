import { Eye, Pencil, Trash2, MessageSquare, BellDot } from "lucide-react";

import { cn } from "@/lib/utils";

import { StatusBadge } from "@/components/ui/atoms";

export default function JobRow({
  job,
  formatDate,
  onView = () => {},
  onEdit = () => {},
  onDelete = () => {},
  onDraftMessage = () => {},
  hasSuggestion = false,
}) {
  return (
    <tr className={cn("border-b last:border-b-0")}> 
      <td className="px-4 py-4 align-top whitespace-nowrap">
        <div className="flex items-center gap-1.5">
          {hasSuggestion && (
            <BellDot className="w-3.5 h-3.5 text-amber-500 shrink-0" />
          )}
          <span>{job.company || "—"}</span>
        </div>
      </td>
      <td className="px-4 py-4 align-top whitespace-nowrap">
        {job.job_title || "—"}
      </td>
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
            aria-label="Draft message"
            onClick={() => onDraftMessage(job)}
            className="inline-flex items-center justify-center rounded-md p-1 hover:bg-muted"
            title="Draft a communication message for this job"
          >
            <MessageSquare className="h-4 w-4" />
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
        <StatusBadge status={job.status} />
      </td>
    </tr>
  );
}

