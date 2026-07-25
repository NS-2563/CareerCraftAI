import { useNavigate } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardAction,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { EllipsisVertical, Archive } from "lucide-react";

function StatusBadge({ completed, isArchived }) {
  if (isArchived) {
    return (
      <Badge
        className="border-gray-300 text-gray-500 bg-gray-50"
        variant="outline"
      >
        <Archive className="size-3 mr-1" />
        Archived
      </Badge>
    );
  }

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

function getMenuActions(actions, resume) {
  return actions.filter(
    (action) =>
      action.group === "menu" &&
      (!action.condition || action.condition(resume))
  );
}

export default function ResumeCard({
  resume,
  formatDate,
  actions = [],
  mutationStates = {},
}) {
  const navigate = useNavigate();

  const primaryAction = actions.find(
    (action) => action.group === "primary" && action.type === "link"
  );

  const menuActions = getMenuActions(actions, resume);

  const isArchived = resume.is_archived;

  const isActionDisabled = (label) => {
    switch (label) {
      case "Archive":
        return mutationStates.archivePending;
      case "Restore":
        return mutationStates.restorePending;
      case "Delete":
        return mutationStates.deletePending;
      default:
        return false;
    }
  };

  return (
    <Card
      className={
        isArchived
          ? "border-dashed border-gray-300 bg-gray-50/40 hover:shadow-md transition-shadow focus-visible:ring-2 focus-visible:ring-ring/50"
          : "hover:shadow-md transition-shadow focus-visible:ring-2 focus-visible:ring-ring/50"
      }
    >
      <CardHeader>
        <CardTitle className="truncate">{resume.name}</CardTitle>
        <CardAction>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="Resume actions"
              >
                <EllipsisVertical className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              {menuActions.map((action, idx) => {
                const items = [];

                if (action.label === "Delete" && idx > 0) {
                  items.push(
                    <DropdownMenuSeparator key={`sep-${idx}`} />
                  );
                }

                items.push(
                  <DropdownMenuItem
                    key={idx}
                    disabled={isActionDisabled(action.label)}
                    data-variant={action.destructive ? "destructive" : undefined}
                    className={
                      action.destructive
                        ? "text-destructive focus:text-destructive focus:bg-destructive/10"
                        : ""
                    }
                    onClick={() => {
                      if (action.type === "link" && action.href) {
                        navigate(action.href(resume.id));
                      } else if (
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
                  </DropdownMenuItem>
                );

                return items;
              })}
            </DropdownMenuContent>
          </DropdownMenu>
        </CardAction>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge completed={resume.completed} isArchived={isArchived} />
          <Badge
            variant="secondary"
            className="bg-gray-100 text-gray-600 border-gray-200"
          >
            Version {resume.version}
          </Badge>
        </div>

        <Separator />

        <CardDescription>
          Last updated: {formatDate(resume.updated_at)}
        </CardDescription>
      </CardContent>

      {primaryAction && (
        <CardFooter>
          <Button asChild variant="default" size="sm" className="w-full">
            <a href={primaryAction.href(resume.id)}>
              Edit Resume
            </a>
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}
