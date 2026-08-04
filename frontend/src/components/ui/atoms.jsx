import {
  AlertCircle,
  ArrowUpRight,
  Award,
  CalendarClock,
  Check,
  CheckCircle2,
  ChevronDown,
  Circle,
  FileText,
  Hourglass,
  Lock,
  MinusCircle,
  Reply,
  Send,
  Star,
  X,
  XCircle,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton as SkeletonPrimitive } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

import { useState } from "react";

import { cn } from "@/lib/utils"

/**
 * Small uppercase mono label used to introduce sections.
 *
 * @param {{ className?: string }} props
 */
export function SectionLabel({ className, ...props }) {
  return (
    <p
      className={cn(
        "font-mono text-[0.7rem] font-medium tracking-[0.18em] text-muted-foreground uppercase",
        className,
      )}
      {...props}
    />
  )
}

/**
 * Square tile containing an icon, tinted with a per-module accent color.
 *
 * @param {{
 *   icon: import("lucide-react").LucideIcon
 *   accent: string
 *   className?: string
 *   size?: "sm" | "md" | "lg"
 * }} props
 */
export function IconTile({ icon: Icon, accent, className, size = "md" }) {
  const dims =
    size === "sm" ? "size-8 rounded-lg" : size === "lg" ? "size-12 rounded-2xl" : "size-10 rounded-xl"
  const iconSize = size === "sm" ? "size-4" : size === "lg" ? "size-6" : "size-5"
  return (
    <div
      className={cn("flex shrink-0 items-center justify-center border", dims, className)}
      style={{
        color: accent,
        backgroundColor: `color-mix(in oklch, ${accent} 15%, transparent)`,
        borderColor: `color-mix(in oklch, ${accent} 26%, transparent)`,
      }}
    >
      <Icon className={iconSize} strokeWidth={2} />
    </div>
  )
}

/**
 * Circular progress indicator with an animated stroke.
 *
 * @param {{
 *   value: number
 *   size?: number
 *   stroke?: number
 *   accent?: string
 *   label?: string
 *   sublabel?: string
 * }} props
 */
export function ProgressRing({
  value,
  size = 88,
  stroke = 8,
  accent = "var(--brand)",
  label,
  sublabel,
}) {
  const radius = (size - stroke) / 2
  const circ = 2 * Math.PI * radius
  const offset = circ - (value / 100) * circ
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="color-mix(in oklch, var(--foreground) 10%, transparent)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={accent}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 1s cubic-bezier(0.22,1,0.36,1)" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-xl font-semibold tabular-nums">{label ?? value}</span>
        {sublabel && <span className="text-[0.65rem] text-muted-foreground">{sublabel}</span>}
      </div>
    </div>
  )
}

/**
 * Horizontal gradient progress bar.
 *
 * @param {{
 *   value: number
 *   accent?: string
 *   className?: string
 * }} props
 */
export function Bar({ value, accent = "var(--brand)", className }) {
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-muted", className)}>
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{
          width: `${value}%`,
          background: `linear-gradient(90deg, color-mix(in oklch, ${accent} 70%, transparent), ${accent})`,
        }}
      />
    </div>
  )
}

/**
 * Vertical list of dated entries, each marked by an accent-colored dot or an
 * icon chosen by the caller. Agonistic of module — the same atom renders
 * activity events, communication status, or interview history.
 *
 * Pass ``onItemClick`` (plus ``linkable: true`` on individual items) to make
 * entries clickable; the row renders as a button with a hover affordance.
 *
 * @param {{
 *   items: Array<{ id: string|number, type: string, title: string, subtitle?: string, timestamp?: string, accentColor?: string, linkable?: boolean, content?: React.ReactNode }>
 *   iconFor?: (item: object) => import("lucide-react").LucideIcon | null | undefined
 *   onItemClick?: (item: object) => void
 *   className?: string
 * }} props
 */
export function Timeline({ items = [], iconFor, onItemClick, className }) {
  const clickable = typeof onItemClick === "function";
  return (
    <ol className={cn("flex flex-col", className)}>
      {items.map((item, index) => {
        const Icon = iconFor?.(item);
        const accent = item.accentColor ?? "var(--brand)";
        const isLast = index === items.length - 1;
        const isActionable = clickable && item.linkable;
        const row = (
          <>
            <span
              className="relative mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full border"
              style={{
                color: accent,
                backgroundColor: `color-mix(in oklch, ${accent} 12%, transparent)`,
                borderColor: `color-mix(in oklch, ${accent} 26%, transparent)`,
              }}
            >
              {Icon ? (
                <Icon className="size-3.5" strokeWidth={2} />
              ) : (
                <span className="size-1.5 rounded-full" style={{ backgroundColor: accent }} />
              )}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-baseline justify-between gap-x-2">
                <p className="text-sm font-medium">{item.title}</p>
                {item.timestamp && (
                  <time className="text-xs text-muted-foreground tabular-nums">{item.timestamp}</time>
                )}
              </div>
              {item.subtitle && <p className="mt-0.5 text-xs text-muted-foreground">{item.subtitle}</p>}
              {item.content}
            </div>
            {isActionable && (
              <ArrowUpRight
                className="mt-1.5 size-4 shrink-0 text-muted-foreground/50 opacity-0 transition-opacity"
                aria-hidden
              />
            )}
          </>
        );
        return (
          <li key={item.id ?? index} className="relative flex gap-3 pb-4 last:pb-0">
            {!isLast && (
              <span aria-hidden className="absolute top-8 bottom-0 left-[13px] w-px bg-border" />
            )}
            {isActionable ? (
              <button
                type="button"
                onClick={() => onItemClick(item)}
                title={`Open ${item.title}`}
                className="group flex w-full items-start gap-3 rounded-lg px-1 -mx-1 text-left transition-colors hover:bg-accent/50"
              >
                {row}
                <span className="ml-auto" aria-hidden />
              </button>
            ) : (
              row
            )}
          </li>
        );
      })}
    </ol>
  );
}

/**
 * Explanation panel: a headline, a priority/confidence indicator slot (the
 * caller supplies whatever value — percentage, badge, stars — the atom just
 * lays it out), and a bulleted "Because" reasons list.
 *
 * Pass ``collapsible`` to render the reasons list behind an expandable
 * "Why this recommendation?" toggle (start collapsed) instead of always
 * visible.
 *
 * @param {{
 *   title: string
 *   indicator?: React.ReactNode | (() => React.ReactNode)
 *   reasons?: Array<React.ReactNode>
 *   icon?: import("lucide-react").LucideIcon
 *   accent?: string
 *   collapsible?: boolean
 *   className?: string
 *   children?: React.ReactNode
 * }} props
 */
export function InsightCard({
  title,
  indicator,
  reasons = [],
  icon: Icon,
  accent = "var(--brand)",
  collapsible = false,
  className,
  children,
}) {
  const [open, setOpen] = useState(!collapsible);
  const indicatorNode = typeof indicator === "function" ? indicator() : indicator ?? children;
  const hasReasons = reasons.length > 0;
  return (
    <Card className={cn("gap-3", className)}>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          {Icon && <IconTile icon={Icon} accent={accent} size="sm" />}
          <CardTitle>{title}</CardTitle>
        </div>
        {indicatorNode && <div className="shrink-0">{indicatorNode}</div>}
      </CardHeader>
      {hasReasons && collapsible ? (
        <CardContent>
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            Why this recommendation?
            <ChevronDown
              className={cn("size-3.5 transition-transform", open && "rotate-180")}
              aria-hidden
            />
          </button>
          {open && (
            <ul className="mt-2 space-y-1.5">
              {reasons.map((reason, i) => (
                <li key={i} className="flex gap-2 text-sm text-muted-foreground">
                  <span
                    aria-hidden
                    className="mt-[7px] size-1.5 shrink-0 rounded-full"
                    style={{ backgroundColor: accent }}
                  />
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      ) : hasReasons ? (
        <CardContent>
          <SectionLabel>Because</SectionLabel>
          <ul className="mt-2 space-y-1.5">
            {reasons.map((reason, i) => (
              <li key={i} className="flex gap-2 text-sm text-muted-foreground">
                <span
                  aria-hidden
                  className="mt-[7px] size-1.5 shrink-0 rounded-full"
                  style={{ backgroundColor: accent }}
                />
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      ) : null}
      {children != null && indicatorNode != null && (
        <CardContent className={hasReasons ? "pt-0" : undefined}>
          {children}
        </CardContent>
      )}
    </Card>
  );
}

/**
 * Fraction-of-signals badge (e.g. "3 of 4 signals") rendered as a small
 * filled/outline segmented bar. Deliberately distinct from a confidence
 * percentage: the value is a real integer count out of a known total.
 *
 * @param {{
 *   supported: number
 *   total: number
 *   label?: string
 *   accent?: string
 *   className?: string
 * }} props
 */
export function SignalStrengthBadge({
  supported = 0,
  total = 0,
  label,
  accent = "var(--brand)",
  className,
}) {
  const segments = Math.max(1, total);
  const filled = Math.min(Math.max(0, supported), segments);
  const text = label ?? `${filled} of ${segments} signals`;
  return (
    <div className={cn("inline-flex items-center gap-2", className)}>
      <span className="flex gap-0.5" role="img" aria-label={text}>
        {Array.from({ length: segments }).map((_, i) => (
          <span
            key={i}
            className="h-2 w-1 rounded-[1px]"
            style={
              i < filled
                ? { backgroundColor: accent }
                : { border: "1px solid color-mix(in oklch, var(--foreground) 25%, transparent)" }
            }
          />
        ))}
      </span>
      <span className="text-xs font-medium text-muted-foreground tabular-nums">{text}</span>
    </div>
  );
}

/**
 * A labeled progress bar plus a checklist of items, each showing a check or an
 * empty circle (e.g. the Application Readiness checklist).
 *
 * @param {{
 *   items: Array<{ label: string, done: boolean }>
 *   label?: string
 *   value?: number
 *   accent?: string
 *   className?: string
 * }} props
 */
export function ChecklistProgress({ items = [], label, value, accent = "var(--brand)", className }) {
  const total = items.length;
  const doneCount = items.filter((item) => item.done).length;
  const progress = value ?? (total === 0 ? 0 : Math.round((doneCount / total) * 100));
  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-medium">{label}</p>
        <span className="text-xs text-muted-foreground tabular-nums">
          {doneCount}/{total}
        </span>
      </div>
      <Bar value={progress} accent={accent} />
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="flex items-center gap-2 text-sm">
            {item.done ? (
              <Check className="size-4 shrink-0" style={{ color: accent }} strokeWidth={2.5} />
            ) : (
              <Circle className="size-4 shrink-0 text-muted-foreground/40" />
            )}
            <span className={item.done ? "text-muted-foreground" : undefined}>{item.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

const STATUS_META = {
  wishlist: { label: "Wishlist", icon: Star, accent: "#f59e0b" },
  applied: { label: "Applied", icon: Send, accent: "#3b82f6" },
  interview: { label: "Interview", icon: CalendarClock, accent: "#8b5cf6" },
  "interview scheduled": { label: "Interview Scheduled", icon: CalendarClock, accent: "#8b5cf6" },
  offer: { label: "Offer", icon: Award, accent: "#10b981" },
  accepted: { label: "Accepted", icon: CheckCircle2, accent: "#22c55e" },
  rejected: { label: "Rejected", icon: XCircle, accent: "#ef4444" },
  withdrawn: { label: "Withdrawn", icon: MinusCircle, accent: "#9ca3af" },
  "needs reply": { label: "Needs Reply", icon: AlertCircle, accent: "#f59e0b" },
  needs_reply: { label: "Needs Reply", icon: AlertCircle, accent: "#f59e0b" },
  waiting: { label: "Waiting", icon: Hourglass, accent: "#0ea5e9" },
  closed: { label: "Closed", icon: Lock, accent: "#6b7280" },
  replied: { label: "Replied", icon: Reply, accent: "#10b981" },
  sent: { label: "Sent", icon: Send, accent: "#3b82f6" },
  draft: { label: "Draft", icon: FileText, accent: "#9ca3af" },
};

/**
 * Single, centralized badge for known status strings so every module renders
 * the same status the same way. Unknown strings fall back to an outline badge.
 *
 * @param {{
 *   status: string
 *   className?: string
 * }} props
 */
export function StatusBadge({ status, className }) {
  const key = String(status ?? "").toLowerCase();
  const meta = STATUS_META[key] || { label: status || "Unknown", icon: Circle, accent: null };

  if (!meta.accent) {
    return (
      <Badge variant="outline" className={cn("capitalize", className)}>
        <meta.icon className="mr-1 size-3" />
        {meta.label}
      </Badge>
    );
  }
  return (
    <Badge variant="soft" accent={meta.accent} className={cn("capitalize", className)}>
      <meta.icon className="mr-1 size-3" />
      {meta.label}
    </Badge>
  );
}

const CONFIDENCE_META = {
  high: {
    label: "High",
    className: "bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:text-emerald-400 dark:border-emerald-500/40",
  },
  medium: {
    label: "Medium",
    className: "bg-amber-500/10 text-amber-600 border-amber-500/30 dark:text-amber-400 dark:border-amber-500/40",
  },
  low: {
    label: "Low",
    className: "bg-gray-500/10 text-gray-500 border-gray-500/30 dark:text-gray-400 dark:border-gray-500/40",
  },
};

/**
 * Bucket a real supported/total signal count into an honest confidence label.
 * Mirrors the backend derivation (>= 0.75 High, >= 0.4 Medium, else Low) — a
 * pure function of the stored counts, never an AI value.
 *
 * @param {{
 *   supported: number
 *   total: number
 *   level?: string
 *   className?: string
 * }} props
 */
export function ConfidenceBadge({ supported = 0, total = 0, level, className }) {
  const levelKey = level || confidenceBucket(supported, total);
  const meta = CONFIDENCE_META[levelKey] || CONFIDENCE_META.low;
  return (
    <span
      className={cn(
        "inline-flex h-5 w-fit items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        meta.className,
        className,
      )}
    >
      {meta.label}
    </span>
  );
}

/**
 * Pure derivation of the confidence bucket from a signal count.
 * @param {number} supported
 * @param {number} total
 * @returns {"high"|"medium"|"low"}
 */
function confidenceBucket(supported, total) {
  if (total <= 0 || supported <= 0) return "low";
  const ratio = supported / total;
  if (ratio >= 0.75) return "high";
  if (ratio >= 0.4) return "medium";
  return "low";
}

/**
 * Pulsing placeholder block — rectangle or circle — for loading states.
 *
 * @param {{
 *   circle?: boolean
 *   className?: string
 * }} props
 */
export function Skeleton({ circle = false, className, ...props }) {
  return (
    <SkeletonPrimitive
      className={cn(circle ? "rounded-full" : "h-4 w-full", className)}
      {...props}
    />
  );
}

/**
 * Dismissible inline banner for post-AI-action confirmations.
 *
 * @param {{
 *   children: React.ReactNode
 *   onDismiss?: () => void
 *   className?: string
 * }} props
 */
export function SuccessBanner({ children, onDismiss, className }) {
  return (
    <div
      role="status"
      className={cn(
        "flex items-start justify-between gap-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300",
        className
      )}
    >
      <div className="flex items-start gap-2.5">
        <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
        <div>{children}</div>
      </div>
      {onDismiss && (
        <Button
          variant="ghost"
          size="icon-xs"
          onClick={onDismiss}
          aria-label="Dismiss notification"
          className="text-current hover:bg-emerald-500/10"
        >
          <X />
        </Button>
      )}
    </div>
  );
}

/**
 * Hover tooltip that explains how an AI-generated score is computed. Wraps any
 * score display (badge, ring, stat) so a one-sentence, truthful explanation
 * appears on hover. Self-contained (owns its own provider) so pages can drop it
 * in without extra wiring.
 *
 * @param {{
 *   description: string
 *   children: React.ReactNode
 *   className?: string
 * }} props
 */
export function ScoreTooltip({ description, children, className }) {
  return (
    <TooltipProvider delayDuration={250}>
      <Tooltip>
        <TooltipTrigger
          type="button"
          className={cn(
            "inline-flex cursor-help items-center justify-center rounded-sm bg-transparent p-0 text-inherit outline-none focus-visible:ring-2 focus-visible:ring-ring/40",
            className
          )}
        >
          {children}
        </TooltipTrigger>
        <TooltipContent className="text-center">{description}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
