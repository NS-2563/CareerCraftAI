import { Skeleton } from "@/components/ui/skeleton";

export default function JobTableLoading() {
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
          {Array.from({ length: 5 }).map((_, idx) => (
            <tr key={idx} className="border-b last:border-b-0">
              <td className="px-4 py-4">
                <Skeleton className="h-4 w-32" />
              </td>
              <td className="px-4 py-4">
                <Skeleton className="h-4 w-48" />
              </td>
              <td className="px-4 py-4">
                <Skeleton className="h-4 w-28" />
              </td>
              <td className="px-4 py-4">
                <Skeleton className="h-4 w-24" />
              </td>
              <td className="px-4 py-4">
                <Skeleton className="h-4 w-24" />
              </td>
              <td className="px-4 py-4">
                <Skeleton className="h-4 w-24" />
              </td>
              <td className="px-4 py-4">
                <Skeleton className="h-4 w-20" />
              </td>
              <td className="px-4 py-4">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-8 w-8" />
                  <Skeleton className="h-8 w-8" />
                  <Skeleton className="h-8 w-8" />
                </div>
              </td>
              <td className="px-4 py-4">
                <Skeleton className="h-6 w-24" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

