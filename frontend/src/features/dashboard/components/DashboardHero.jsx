import { useNavigate } from "react-router-dom";
import { Sparkles, ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

/**
 * Time-aware greeting hero (Feature 1).
 * @param {{
 *   greeting: { greeting: string, message: string, firstName: string|null }
 *   recommendedAction: { path: string|null, ctaLabel: string|null, description: string }
 *   pendingFollowUps: number
 * }} props
 */
export function DashboardHero({ greeting, recommendedAction, pendingFollowUps = 0 }) {
  const navigate = useNavigate();
  const todayLabel = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  let heroLine = recommendedAction?.description || greeting.message;
  if (pendingFollowUps > 0) {
    const noun =
      pendingFollowUps === 1 ? "application needs a follow-up" : "applications need follow-ups";
    heroLine = `${pendingFollowUps} ${noun}. Let's prep.`;
  }

  return (
    <Card
      sheen
      className="relative overflow-hidden p-6 lg:col-span-2"
      style={{
        background:
          "radial-gradient(130% 120% at 100% 0%, color-mix(in oklch, var(--brand) 20%, transparent), transparent 55%), var(--card)",
      }}
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge accent="var(--brand)" variant="soft">
          <Sparkles className="size-3" /> Career OS
        </Badge>
        <span className="text-xs text-muted-foreground">{todayLabel}</span>
      </div>
      <h1 className="mt-4 font-display text-2xl font-semibold tracking-tight text-balance sm:text-3xl">
        {greeting.greeting}
        {greeting.firstName ? `, ${greeting.firstName}` : ""}.
        <span className="block text-muted-foreground">{greeting.message}</span>
      </h1>
      <p className="mt-3 max-w-lg text-sm text-muted-foreground">{heroLine}</p>
      <div className="mt-5 flex flex-wrap gap-2">
        {recommendedAction?.path && (
          <Button
            onClick={() => navigate(recommendedAction.path)}
            className="h-9 gap-1.5 rounded-xl px-4 text-sm font-medium"
          >
            {recommendedAction.ctaLabel || "Continue"} <ArrowUpRight className="size-4" />
          </Button>
        )}
        <Button
          variant="outline"
          onClick={() => navigate("/career")}
          className="h-9 gap-1.5 rounded-xl border border-border bg-card/50 px-4 text-sm font-medium"
        >
          Talk to coach
        </Button>
      </div>
    </Card>
  );
}

export default DashboardHero;
