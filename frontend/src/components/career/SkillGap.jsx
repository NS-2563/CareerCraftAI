import { useState } from "react";
import { Target } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  ConfidenceBadge,
  InsightCard,
  SignalStrengthBadge,
} from "@/components/ui/atoms";
import careerApi from "@/services/careerApi";

const PRIORITY_ACCENT = "#f59e0b";

const STATUS_OPTIONS = [
  { value: "not_started", label: "Not started" },
  { value: "in_progress", label: "In progress" },
  { value: "done", label: "Done" },
];

function StatusSelector({ taskId, value, disabled, onChange }) {
  return (
    <div
      role="group"
      aria-label="Task status"
      className="flex items-center gap-0.5 rounded-lg border bg-muted/40 p-0.5"
    >
      {STATUS_OPTIONS.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            disabled={disabled || !taskId}
            aria-pressed={active}
            onClick={() => onChange(opt.value)}
            title={active ? `Status: ${opt.label}` : `Mark as ${opt.label.toLowerCase()}`}
            className={`rounded-md px-2 py-1 text-xs font-medium transition-colors ${
              active
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            } disabled:cursor-not-allowed disabled:opacity-50`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

function PriorityItem({ item }) {
  const isObject = Boolean(item && typeof item === "object" && item.skill);
  const taskId = isObject ? item.task_id : null;
  const [status, setStatus] = useState(
    isObject && item.task_status ? item.task_status : "not_started",
  );

  const { mutate: saveStatus, isPending: savingStatus } = useMutation({
    mutationFn: (next) =>
      careerApi.setTaskStatus(taskId, next).then((r) => r.data),
    onMutate: (next) => {
      const prev = status;
      setStatus(next);
      return { prev };
    },
    onError: (_err, _next, ctx) => {
      if (ctx?.prev) setStatus(ctx.prev);
      toast.error("Couldn't update task status.");
    },
  });

  if (typeof item === "string") {
    return (
      <li className="flex items-start gap-2 text-sm">
        <span aria-hidden>⭐</span>
        <span>{item}</span>
      </li>
    );
  }

  if (isObject) {
    const supported = Number(item.supported_signals) || 0;
    const total = Number(item.total_possible_signals) || 0;
    const reasons = Array.isArray(item.reasons) ? item.reasons : [];

    const handleStatusChange = (next) => {
      if (!taskId || savingStatus || next === status) return;
      saveStatus(next);
    };

    return (
      <InsightCard
        title={item.skill}
        icon={Target}
        accent={PRIORITY_ACCENT}
        collapsible
        reasons={reasons}
        indicator={
          <div className="flex flex-col items-end gap-1.5">
            {total > 0 && (
              <SignalStrengthBadge
                supported={supported}
                total={total}
                accent={PRIORITY_ACCENT}
              />
            )}
            <ConfidenceBadge
              supported={supported}
              total={total}
              level={item.confidence}
            />
          </div>
        }
        className="pt-3"
      >
        <StatusSelector
          taskId={taskId}
          value={status}
          disabled={savingStatus}
          onChange={handleStatusChange}
        />
      </InsightCard>
    );
  }

  return null;
}

export default function SkillGap({ skillGap }) {
  return (
    <section className="rounded-xl border p-6">

      <h2 className="text-2xl font-bold mb-6">
        Skill Gap Analysis
      </h2>

      <div className="grid lg:grid-cols-3 gap-6">

        <div className="rounded-lg border p-5">

          <h3 className="font-semibold mb-4">
            Existing Skills
          </h3>

          <ul className="space-y-2">

            {skillGap?.existing_skills?.map((skill, index) => (
              <li key={index}>✅ {skill}</li>
            ))}

          </ul>

        </div>

        <div className="rounded-lg border p-5">

          <h3 className="font-semibold mb-4">
            Missing Skills
          </h3>

          <ul className="space-y-2">

            {skillGap?.missing_skills?.map((skill, index) => (
              <li key={index}>❌ {skill}</li>
            ))}

          </ul>

        </div>

        <div className="rounded-lg border p-5">

          <h3 className="font-semibold mb-4">
            Recommended Skills
          </h3>

          <p className="text-sm text-muted-foreground mb-4">
            How many real signals support each recommendation
          </p>

          <ul className="space-y-3">
            {skillGap?.priority?.map((skill, index) => (
              <PriorityItem
                key={skill?.task_id ?? skill?.skill ?? index}
                item={skill}
              />
            ))}
          </ul>

        </div>

      </div>

    </section>
  );
}
