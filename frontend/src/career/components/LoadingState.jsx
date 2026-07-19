import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

export default function LoadingState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.35 }}
      className="space-y-8"
    >
      {/* Loading Header */}
      <div className="flex flex-col items-center justify-center py-6">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-3" />
        <p className="text-muted-foreground text-sm">
          Generating your personalized career report...
        </p>
      </div>

      {/* Summary */}
      <div className="rounded-xl border p-6 space-y-4 animate-pulse">
        <div className="h-7 w-60 rounded bg-muted" />

        <div className="space-y-3">
          <div className="h-4 w-full rounded bg-muted" />
          <div className="h-4 w-11/12 rounded bg-muted" />
          <div className="h-4 w-9/12 rounded bg-muted" />
        </div>
      </div>

      {/* Strengths & Weaknesses */}
      <div className="grid lg:grid-cols-2 gap-6 animate-pulse">
        {[1, 2].map((card) => (
          <div
            key={card}
            className="rounded-xl border p-6 space-y-4"
          >
            <div className="h-6 w-40 rounded bg-muted" />

            {[1, 2, 3, 4].map((line) => (
              <div
                key={line}
                className="h-4 rounded bg-muted"
              />
            ))}
          </div>
        ))}
      </div>

      {/* Career Paths */}
      <div className="rounded-xl border p-6 animate-pulse">
        <div className="h-7 w-56 rounded bg-muted mb-6" />

        <div className="grid lg:grid-cols-2 gap-5">
          {[1, 2].map((card) => (
            <div
              key={card}
              className="rounded-lg border p-5 space-y-4"
            >
              <div className="h-5 w-40 rounded bg-muted" />

              <div className="space-y-3">
                <div className="h-4 rounded bg-muted" />
                <div className="h-4 w-11/12 rounded bg-muted" />
              </div>

              <div className="flex gap-3">
                <div className="h-8 w-24 rounded-full bg-muted" />
                <div className="h-8 w-24 rounded-full bg-muted" />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Additional Sections */}
      {[1, 2, 3].map((section) => (
        <div
          key={section}
          className="rounded-xl border p-6 space-y-4 animate-pulse"
        >
          <div className="h-6 w-56 rounded bg-muted" />

          <div className="grid lg:grid-cols-3 gap-5">
            {[1, 2, 3].map((card) => (
              <div
                key={card}
                className="rounded-lg border p-5 space-y-3"
              >
                <div className="h-5 w-32 rounded bg-muted" />

                {[1, 2, 3, 4].map((line) => (
                  <div
                    key={line}
                    className="h-4 rounded bg-muted"
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      ))}
    </motion.div>
  );
}

