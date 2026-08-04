/* eslint react-hooks/set-state-in-effect: "off" */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, CornerDownLeft, FilePlus, Plus } from "lucide-react";
import { modules, accountNav } from "@/lib/modules";
import { IconTile } from "@/components/ui/atoms";
import { cn } from "@/lib/utils";

const quickActions = [
  {
    label: "Create new resume",
    sub: "Start a fresh resume in the studio",
    href: "/resume-studio?create=1",
    icon: FilePlus,
    accent: "var(--blue)",
  },
  {
    label: "Track new application",
    sub: "Add a job application to your tracker",
    href: "/jobs",
    icon: Plus,
    accent: "var(--cyan)",
  },
];

export default function CommandPalette({ open, onOpenChange }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);

  const items = [
    ...quickActions.map((a) => ({
      label: a.label,
      sub: a.sub,
      href: a.href,
      icon: a.icon,
      accent: a.accent,
    })),
    ...modules.map((m) => ({
      label: m.name,
      sub: m.description,
      href: m.href,
      icon: m.icon,
      accent: m.accent,
    })),
    ...accountNav.map((a) => ({
      label: a.name,
      sub: "Account",
      href: a.href,
      icon: a.icon,
      accent: "var(--muted-foreground)",
    })),
  ].filter((i) => i.label.toLowerCase().includes(query.toLowerCase()));

  useEffect(() => {
    if (!open) {
      setQuery("");
      setActive(0);
    }
  }, [open]);

  useEffect(() => {
    setActive(0);
  }, [query]);

  function go(href) {
    onOpenChange(false);
    navigate(href);
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-100 flex items-start justify-center px-4 pt-[12vh]"
      onClick={() => onOpenChange(false)}
    >
      <div className="absolute inset-0 bg-background/70 backdrop-blur-sm" />
      <div
        className="glass-strong relative w-full max-w-xl overflow-hidden rounded-2xl shadow-2xl animate-fade-up"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Command palette"
      >
        <div className="flex items-center gap-3 border-b border-border px-4">
          <Search className="size-4 text-muted-foreground" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setActive((a) => Math.min(a + 1, items.length - 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setActive((a) => Math.max(a - 1, 0));
              } else if (e.key === "Enter" && items[active]) {
                go(items[active].href);
              } else if (e.key === "Escape") {
                onOpenChange(false);
              }
            }}
            placeholder="Jump to a module or action..."
            className="h-14 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          <kbd className="hidden rounded-md border border-border px-1.5 py-0.5 font-mono text-[0.65rem] text-muted-foreground sm:block">
            ESC
          </kbd>
        </div>
        <div className="max-h-80 overflow-y-auto p-2">
          {items.length === 0 && (
            <p className="px-3 py-8 text-center text-sm text-muted-foreground">
              No results for &ldquo;{query}&rdquo;
            </p>
          )}
          {items.map((item, i) => (
            <button
              key={item.href}
              onMouseEnter={() => setActive(i)}
              onClick={() => go(item.href)}
              className={cn(
                "flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left transition-colors",
                active === i ? "bg-accent" : "hover:bg-accent/60",
              )}
            >
              <IconTile icon={item.icon} accent={item.accent} size="sm" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{item.label}</p>
                <p className="truncate text-xs text-muted-foreground">{item.sub}</p>
              </div>
              {active === i && (
                <CornerDownLeft className="size-3.5 text-muted-foreground" />
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
