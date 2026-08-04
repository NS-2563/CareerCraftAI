import { ScoreTooltip } from "@/components/ui/atoms";

export default function CareerSummary({ report }) {
  if (!report) return null;

  return (
    <>
      {/* Career Overview */}

      <section className="rounded-xl border bg-card p-6 space-y-5">

        <h2 className="text-2xl font-bold">
          Career Overview
        </h2>


        <div className="grid md:grid-cols-2 gap-4">

          <div>
            <h3 className="font-semibold">
              Career Goal
            </h3>

            <p className="text-muted-foreground">
              {report.career_goal}
            </p>
          </div>


          <div>
            <h3 className="font-semibold">
              Best Match
            </h3>

            <p className="text-muted-foreground">
              {report.best_match}
            </p>
          </div>


          <div>
            <h3 className="font-semibold">
              Readiness Score
            </h3>

            <p className="text-muted-foreground">
              <ScoreTooltip description="Weighted blend: 40% your ATS resume score, 30% skill match, 15% for having a Projects section, and 15% for Certifications.">
                <span className="inline-flex cursor-help">{report.readiness_score}/100</span>
              </ScoreTooltip>
            </p>
          </div>


          <div>
            <h3 className="font-semibold">
              Readiness Status
            </h3>

            <p className="text-muted-foreground">
              {report.readiness_status}
            </p>
          </div>

        </div>

      </section>


      {/* Career Summary */}

      <section className="rounded-xl border bg-card p-6">

        <h2 className="text-2xl font-bold mb-3">
          Career Summary
        </h2>

        <p className="text-muted-foreground">
          {report.career_summary}
        </p>

      </section>


      {/* Strengths & Weaknesses */}

      <div className="grid lg:grid-cols-2 gap-6">

        <section className="rounded-xl border p-6">

          <h2 className="text-xl font-bold mb-4">
            Strengths
          </h2>

          <ul className="space-y-2 list-disc pl-5">

            {report.strengths?.map((item, index) => (
              <li key={index}>
                {item}
              </li>
            ))}

          </ul>

        </section>


        <section className="rounded-xl border p-6">

          <h2 className="text-xl font-bold mb-4">
            Weaknesses
          </h2>

          <ul className="space-y-2 list-disc pl-5">

            {report.weaknesses?.map((item, index) => (
              <li key={index}>
                {item}
              </li>
            ))}

          </ul>

        </section>

      </div>
    </>
  );
}

