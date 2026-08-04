import { Link } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { modules } from "@/lib/modules";

function BrandMark() {
  return (
    <Link to="/" className="flex w-fit items-center gap-2.5">
      <div
        className="relative flex size-9 items-center justify-center rounded-xl"
        style={{
          background:
            "linear-gradient(140deg, color-mix(in oklch, var(--brand) 90%, white 10%), color-mix(in oklch, var(--indigo) 80%, black))",
        }}
      >
        <Sparkles className="size-5 text-background" strokeWidth={2.5} />
      </div>
      <p className="font-display text-xl font-semibold tracking-tight">CareerCraft</p>
    </Link>
  );
}

export function AuthLayout({ children }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Left: brand panel */}
      <aside className="relative hidden overflow-hidden border-r border-border/60 bg-card/30 lg:flex lg:flex-col lg:p-12">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute top-1/4 left-1/4 h-80 w-80 rounded-full bg-[var(--emerald)]/20 blur-[120px]" />
          <div className="absolute right-1/4 bottom-1/4 h-72 w-72 rounded-full bg-[var(--teal)]/15 blur-[120px]" />
          <div className="absolute inset-0 bg-[linear-gradient(to_right,color-mix(in_oklch,var(--border)_30%,transparent)_1px,transparent_1px),linear-gradient(to_bottom,color-mix(in_oklch,var(--border)_30%,transparent)_1px,transparent_1px)] bg-[size:48px_48px]" />
        </div>

        <BrandMark />

        <div className="flex flex-1 flex-col justify-center">
          <h2 className="max-w-md text-balance font-display text-4xl font-semibold leading-tight tracking-tight">
            Your career, crafted with intelligence.
          </h2>
          <p className="mt-4 max-w-sm text-pretty leading-relaxed text-muted-foreground">
            {modules.length} tools in one workspace — build resumes, score ATS readiness, generate
            cover letters, track applications, draft outreach, and practice interviews with AI
            guidance.
          </p>
          <div className="mt-8 flex flex-wrap gap-2">
            {modules.map((m) => (
              <span
                key={m.id}
                className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/40 px-3 py-1.5 text-xs font-medium backdrop-blur"
              >
                <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: m.accent }} />
                {m.name}
              </span>
            ))}
          </div>
        </div>
      </aside>

      {/* Right: form */}
      <main className="flex items-center justify-center px-5 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <BrandMark />
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}

export default AuthLayout;
