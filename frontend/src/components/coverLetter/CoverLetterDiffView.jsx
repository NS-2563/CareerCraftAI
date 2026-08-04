import { GitCompare, Minus, Plus } from "lucide-react";

import { SectionLabel } from "@/components/ui/atoms";
import { cn } from "@/lib/utils";

/**
 * Real before/after diff between two versions of a cover letter.
 *
 * Renders the deterministic line-level changes returned by the backend diff
 * endpoint: added lines in green, removed lines in red. No AI narration.
 */
export default function CoverLetterDiffView({ diff }) {
  if (!diff) return null;

  const changes = diff.changes || [];
  const hasChanges = changes.length > 0;

  return (
    <div className="rounded-xl border p-5">
      <div className="flex items-center justify-between gap-2">
        <SectionLabel>
          What changed on regeneration
        </SectionLabel>
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground tabular-nums">
          <GitCompare className="size-3.5" />
          v{diff.from_version} → v{diff.to_version}
        </span>
      </div>

      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1 text-emerald-700 dark:text-emerald-300">
          <Plus className="size-3.5" /> {diff.lines_added} line{diff.lines_added === 1 ? "" : "s"} added
        </span>
        <span className="inline-flex items-center gap-1 text-red-600 dark:text-red-400">
          <Minus className="size-3.5" /> {diff.lines_removed} line{diff.lines_removed === 1 ? "" : "s"} removed
        </span>
        <span className="tabular-nums">
          Word count {diff.word_count_delta >= 0 ? "+" : ""}
          {diff.word_count_delta}
        </span>
      </div>

      {!hasChanges && (
        <p className="mt-3 text-sm text-muted-foreground">
          No text changes were detected between these versions.
        </p>
      )}

      {hasChanges && (
        <div className="mt-3 max-h-80 overflow-auto rounded-lg border bg-muted/30">
          <table className="w-full text-sm font-mono">
            <tbody>
              {changes.map((change, i) => (
                <tr key={i} className="align-top">
                  <td className="w-px border-r border-border px-1 text-center text-xs text-muted-foreground select-none">
                    {change.type === "replace" ? "~" : change.type === "insert" ? "+" : "-"}
                  </td>
                  <td className="min-w-0 p-0">
                    {(change.removed || []).map((line, j) => (
                      <div
                        key={`r${j}`}
                        className={cn(
                          "whitespace-pre-wrap break-words px-3 py-0.5 text-red-700 line-through dark:text-red-400",
                          change.type === "insert" && "hidden",
                        )}
                      >
                        {line}
                      </div>
                    ))}
                    {(change.added || []).map((line, j) => (
                      <div
                        key={`a${j}`}
                        className={cn(
                          "whitespace-pre-wrap break-words px-3 py-0.5 text-emerald-700 dark:text-emerald-300",
                          change.type === "delete" && "hidden",
                        )}
                      >
                        {line}
                      </div>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
