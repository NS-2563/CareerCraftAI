import { motion } from "framer-motion";
import { Check } from "lucide-react";

export default function StepIndicator({ steps, currentStep }) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto py-2">
      {steps.map((step, idx) => {
        const isCompleted = idx < currentStep;
        const isCurrent = idx === currentStep;

        return (
          <div key={step.title} className="flex items-center gap-2">
            <motion.div
              className={`flex items-center justify-center rounded-full text-sm font-medium whitespace-nowrap ${
                isCurrent
                  ? "w-7 h-7 text-primary-foreground bg-primary"
                  : isCompleted
                    ? "w-6 h-6 text-primary-foreground bg-primary"
                    : "w-6 h-6 text-muted-foreground bg-muted"
              }`}
              initial={false}
              animate={{
                scale: isCurrent ? 1.15 : 1,
                backgroundColor: isCurrent
                  ? "var(--primary)"
                  : isCompleted
                    ? "var(--primary)"
                    : "var(--muted)",
                color: isCurrent || isCompleted
                  ? "var(--primary-foreground)"
                  : "var(--muted-foreground)",
              }}
              transition={{ duration: 0.2 }}
            >
              {isCompleted ? (
                <Check className="w-4 h-4" />
              ) : (
                idx + 1
              )}
            </motion.div>

            <motion.span
              className={`text-sm whitespace-nowrap ${
                isCurrent
                  ? "text-foreground font-semibold"
                  : isCompleted
                    ? "text-primary font-medium"
                    : "text-muted-foreground/70"
              }`}
              initial={false}
              animate={{
                color: isCurrent
                  ? "var(--foreground)"
                  : isCompleted
                    ? "var(--primary)"
                    : "var(--muted-foreground)",
              }}
              transition={{ duration: 0.2 }}
            >
              {step.title}
            </motion.span>

            {idx !== steps.length - 1 && (
              <motion.div
                className={`h-px w-6 ${
                  isCompleted
                    ? "bg-primary"
                    : "bg-muted-foreground/20"
                }`}
                initial={false}
                animate={{
                  backgroundColor: isCompleted
                    ? "var(--primary)"
                    : "var(--muted-foreground)",
                  opacity: isCompleted ? 1 : 0.2,
                }}
                transition={{ duration: 0.2 }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}