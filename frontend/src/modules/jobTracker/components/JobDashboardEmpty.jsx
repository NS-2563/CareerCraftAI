import { Briefcase } from "lucide-react";
import { Button } from "@/components/ui/button";
import CreateJobDialog from "./CreateJobDialog";

export default function JobDashboardEmpty() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-center">

      <Briefcase className="h-12 w-12 text-muted-foreground mb-4" />

      <h2 className="text-xl font-semibold">
        No job applications yet
      </h2>

      <p className="mt-2 text-muted-foreground max-w-md">
        Track internships and job applications to monitor your progress.
      </p>

      <CreateJobDialog
        trigger={
          <Button className="mt-6">
            Add Your First Job
          </Button>
        }
      />

    </div>
  );
}