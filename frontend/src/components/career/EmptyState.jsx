import { GraduationCap } from "lucide-react";

export default function EmptyState() {
  return (
    <div className="rounded-xl border border-dashed p-12">

      <div className="flex flex-col items-center text-center">

        <GraduationCap className="h-16 w-16 text-primary mb-6" />

        <h2 className="text-3xl font-bold">
          Career Coach
        </h2>

        <p className="mt-4 max-w-2xl text-muted-foreground">

          Complete the assessment form to receive a personalized
          AI-powered career report including career paths,
          skill gap analysis, learning roadmap, resources,
          and an actionable career plan.

        </p>

      </div>

    </div>
  );
}