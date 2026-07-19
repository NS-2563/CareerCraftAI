import JobRow from "./JobRow";

export default function JobTable({
  jobs,
  formatDate,
  onView = () => {},
  onEdit = () => {},
  onDelete = () => {},
}) {
  return (
    <div className="overflow-x-auto rounded-xl border">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/30">
            {[
              "Company",
              "Job Title",
              "Status",
              "Location",
              "Applied Date",
              "Deadline",
              "Source",
              "Actions",
              "Status Badge",
            ].map((h) => (
              <th
                key={h}
                scope="col"
                className="px-4 py-3 text-left font-medium text-muted-foreground whitespace-nowrap"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <JobRow
              key={job.id}
              job={job}
              formatDate={formatDate}
              onView={() => onView(job)}
              onEdit={() => onEdit(job)}
              onDelete={() => onDelete(job)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

