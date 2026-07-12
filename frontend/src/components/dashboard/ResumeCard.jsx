import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

function StatusBadge({ completed }) {
  return (
    <Badge
      className={
        completed
          ? "border-green-200 text-green-700 bg-green-50"
          : "border-yellow-200 text-yellow-700 bg-yellow-50"
      }
      variant="outline"
    >
      {completed ? "Completed" : "Draft"}
    </Badge>
  );
}

export default function ResumeCard({
  resume,
  formatDate,
  actions = [],
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* HEADER */}
      <div className="flex justify-between items-start mb-2 gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-base truncate">
            {resume.name}
          </h3>

          <div className="mt-2 flex flex-wrap items-center gap-2">
            <StatusBadge completed={resume.completed} />

            <Badge
              variant="secondary"
              className="bg-gray-100 text-gray-600 border-gray-200"
            >
              Version {resume.version}
            </Badge>
          </div>
        </div>
      </div>

      {/* META */}
      <p className="text-sm text-gray-500 mb-3">
        Last Updated: {formatDate(resume.updated_at)}
      </p>

      {/* ACTIONS */}
      <div className="flex flex-wrap gap-2">
        {/* EDIT (special case link) */}
        <Button asChild variant="ghost" size="sm">
          <a href={`/resume-studio?id=${resume.id}`}>
            Edit
          </a>
        </Button>

        {/* DYNAMIC ACTIONS */}
        {actions.map((action, idx) => {
          if (action.condition && !action.condition(resume)) {
            return null;
          }

          if (action.type === "link") return null;

          return (
            <Button
              key={idx}
              variant={action.variant || "ghost"}
              size="sm"
              onClick={() => {
                console.log("Clicked", action.label);
  if (
    action.label === "Duplicate" ||
    action.label === "Rename" ||
    action.label === "History"
  ) {
    action.action(resume);
  } else {
    action.action(resume.id);
  }
}}
            >
              {action.label}
            </Button>
          );
        })}
      </div>
    </div>
  );
}

