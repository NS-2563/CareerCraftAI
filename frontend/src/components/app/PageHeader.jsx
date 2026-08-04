import { IconTile } from "@/components/ui/atoms";

/**
 * Standard page header used at the top of feature pages.
 *
 * @param {{
 *   icon: import("lucide-react").LucideIcon
 *   accent: string
 *   eyebrow: string
 *   title: string
 *   description: string
 *   actions?: import("react").ReactNode
 * }} props
 */
export default function PageHeader({
  icon,
  accent,
  eyebrow,
  title,
  description,
  actions,
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:mb-8 sm:flex-row sm:items-start sm:justify-between">
      <div className="flex items-start gap-4">
        <IconTile icon={icon} accent={accent} size="lg" className="hidden sm:flex" />
        <div className="min-w-0">
          <p
            className="font-mono text-[0.7rem] font-medium tracking-[0.18em] uppercase"
            style={{ color: accent }}
          >
            {eyebrow}
          </p>
          <h1 className="mt-1 font-display text-2xl font-semibold tracking-tight text-balance sm:text-[1.75rem]">
            {title}
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm text-muted-foreground text-pretty">
            {description}
          </p>
        </div>
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
