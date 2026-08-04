/* eslint react-hooks/set-state-in-effect: "off" */
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Sparkles,
  Search,
  Menu,
  X,
  Command,
  Plus,
  LogOut,
} from "lucide-react";
import { modules, accountNav, navGroups, getActiveModule, isModuleActive } from "@/lib/modules";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/useAuth";
import CommandPalette from "./CommandPalette";
import NotificationBell from "./NotificationBell";

function getInitials(user) {
  if (user?.name) {
    return user.name
      .split(/\s+/)
      .map((p) => p[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  }
  return (user?.email?.[0] || "U").toUpperCase();
}

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2.5">
      <div
        className="relative flex size-9 items-center justify-center rounded-xl"
        style={{
          background:
            "linear-gradient(140deg, color-mix(in oklch, var(--brand) 90%, white 10%), color-mix(in oklch, var(--indigo) 80%, black))",
        }}
      >
        <Sparkles className="size-5 text-background" strokeWidth={2.5} />
      </div>
      <div className="leading-tight">
        <p className="font-display text-[0.95rem] font-semibold tracking-tight">
          CareerCraft
        </p>
        <p className="font-mono text-[0.6rem] tracking-[0.2em] text-muted-foreground uppercase">
          AI OS
        </p>
      </div>
    </Link>
  );
}

function NavContent({ onNavigate }) {
  const { pathname } = useLocation();
  return (
    <nav className="flex flex-1 flex-col gap-6 overflow-y-auto px-3 py-4">
      {navGroups.map((g) => {
        const items = modules.filter((m) => m.group === g.group);
        if (items.length === 0) return null;
        return (
          <div key={g.group} className="flex flex-col gap-1">
            <p className="px-3 pb-1 font-mono text-[0.62rem] font-medium tracking-[0.16em] text-muted-foreground/70 uppercase">
              {g.label}
            </p>
            {items.map((m) => {
              const active = isModuleActive(pathname, m.href);
              const Icon = m.icon;
              return (
                <Link
                  key={m.id}
                  to={m.href}
                  onClick={onNavigate}
                  className={cn(
                    "group relative flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all",
                    active
                      ? "bg-accent font-medium text-foreground"
                      : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
                  )}
                >
                  {active && (
                    <span
                      className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full"
                      style={{ backgroundColor: m.accent }}
                    />
                  )}
                  <Icon
                    className="size-4 shrink-0 transition-colors"
                    style={active ? { color: m.accent } : undefined}
                    strokeWidth={2}
                  />
                  <span className="truncate">{m.name}</span>
                </Link>
              );
            })}
          </div>
        );
      })}

      <div className="mt-auto flex flex-col gap-1">
        <p className="px-3 pb-1 font-mono text-[0.62rem] font-medium tracking-[0.16em] text-muted-foreground/70 uppercase">
          Account
        </p>
        {accountNav.map((a) => {
          const active = pathname === a.href;
          const Icon = a.icon;
          return (
            <Link
              key={a.href}
              to={a.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all",
                active
                  ? "bg-accent font-medium text-foreground"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
              )}
            >
              <Icon className="size-4 shrink-0" strokeWidth={2} />
              <span>{a.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

function SidebarFooter() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="m-3 flex flex-col gap-3 rounded-2xl border border-border p-3">
      <div className="flex items-center gap-3">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-semibold text-primary">
          {getInitials(user)}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{user?.name || user?.email || "User"}</p>
          {user?.email && <p className="truncate text-xs text-muted-foreground">{user.email}</p>}
        </div>
      </div>
      <button
        onClick={handleLogout}
        className="flex items-center justify-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <LogOut className="size-3.5" />
        Log out
      </button>
    </div>
  );
}

export default function AppShell({ children }) {
  const { user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    function onKey(e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const current = getActiveModule(pathname);
  const accountItem = accountNav.find((a) => a.href === pathname);
  const currentName = current?.name ?? accountItem?.name ?? "Dashboard";

  return (
    <div className="relative flex min-h-screen bg-background">
      {/* Ambient background */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div
          className="absolute -left-40 -top-40 size-[36rem] rounded-full opacity-20 blur-[120px]"
          style={{ background: "var(--brand)" }}
        />
        <div
          className="absolute -right-40 top-1/3 size-[32rem] rounded-full opacity-[0.12] blur-[120px]"
          style={{ background: "var(--indigo)" }}
        />
      </div>

      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
        <div className="flex h-16 items-center px-5">
          <Logo />
        </div>
        <NavContent />
        <SidebarFooter />
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-background/70 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="glass-strong absolute left-0 top-0 flex h-full w-72 flex-col animate-fade-up">
            <div className="flex h-16 items-center justify-between px-5">
              <Logo />
              <button
                onClick={() => setMobileOpen(false)}
                className="flex size-8 items-center justify-center rounded-lg hover:bg-accent"
                aria-label="Close menu"
              >
                <X className="size-4" />
              </button>
            </div>
            <NavContent onNavigate={() => setMobileOpen(false)} />
            <SidebarFooter />
          </aside>
        </div>
      )}

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 flex h-16 items-center gap-3 border-b border-border bg-background/70 px-4 backdrop-blur-xl sm:px-6">
          <button
            onClick={() => setMobileOpen(true)}
            className="flex size-9 items-center justify-center rounded-lg hover:bg-accent lg:hidden"
            aria-label="Open menu"
          >
            <Menu className="size-5" />
          </button>

          <div className="hidden items-center gap-2 text-sm text-muted-foreground sm:flex">
            <span className="font-medium text-foreground">{currentName}</span>
          </div>

          <button
            onClick={() => setPaletteOpen(true)}
            className="ml-auto flex h-9 items-center gap-2 rounded-xl border border-border bg-card/50 px-3 text-sm text-muted-foreground transition-colors hover:bg-accent sm:w-64 sm:justify-between"
          >
            <span className="flex items-center gap-2">
              <Search className="size-4" />
              <span className="hidden sm:inline">Search or jump to...</span>
            </span>
            <kbd className="hidden items-center gap-0.5 rounded-md border border-border px-1.5 py-0.5 font-mono text-[0.65rem] sm:flex">
              <Command className="size-3" />K
            </kbd>
          </button>

          <NotificationBell />

          <Link
            to="/resume-studio?create=1"
            className="hidden h-9 items-center gap-1.5 rounded-xl bg-primary px-3 text-sm font-medium text-primary-foreground transition-transform hover:scale-[1.02] sm:flex"
          >
            <Plus className="size-4" />
            New
          </Link>

          <Link to="/settings" className="ml-1 shrink-0">
            <div className="flex size-9 items-center justify-center rounded-full border border-border bg-primary/20 text-xs font-semibold text-primary">
              {getInitials(user)}
            </div>
          </Link>
        </header>

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>

      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </div>
  );
}
