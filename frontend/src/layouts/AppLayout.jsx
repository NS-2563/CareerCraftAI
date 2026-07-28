/* eslint react-hooks/set-state-in-effect: "off" */
import { useState, useEffect, useRef } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import {
  LayoutDashboard,
  FileText,
  FileCheck,
  Mail,
  Briefcase,
  Users,
  MessageSquare,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  Sun,
  Bell,
  BellDot,
  User,
  TrendingUp,
  X as XIcon,
  FileEdit,
  Loader2,
} from "lucide-react";
import { useSuggestions, useDismissSuggestion, useGenerateFromSuggestion } from "@/communication/hooks/useSuggestions";

// Navigation items configuration
const NAV_ITEMS = [
  { path: "/", label: "Resume Library", icon: LayoutDashboard },
  { path: "/resume-studio", label: "Resume Studio", icon: FileText },
  { path: "/resume", label: "Resume Analysis", icon: FileCheck },
  { path: "/cover-letter-studio", label: "Cover Letter Studio", icon: Mail },
  { path: "/career", label: "Career Coach", icon: TrendingUp },
  { path: "/interview", label: "Interview Prep", icon: Users },
  { path: "/jobs", label: "Job Tracker", icon: Briefcase },
  { path: "/communication", label: "Communication", icon: MessageSquare },
];

// Future placeholders
const PLACEHOLDER_ITEMS = [
  { label: "Portfolio Generator", comingSoon: true },
  { label: "LinkedIn Optimizer", comingSoon: true },
];

// Breadcrumb mapping
const BREADCRUMB_MAP = {
  "/": "Resume Library",
  "/resume-studio": "Resume Studio",
  "/resume": "Resume Analysis",
  "/cover-letter-studio": "Cover Letter Studio",
  "/career": "Career Coach",
  "/interview": "Interview Prep",
  "/jobs": "Job Tracker",
  "/communication": "Communication",
  "/settings": "Settings",
};

export default function AppLayout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Handle responsive breakpoints
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
        setMobileOpen(false);
      } else if (window.innerWidth < 1024) {
        setSidebarOpen(true);
        setSidebarCollapsed(true);
      } else {
        setSidebarOpen(true);
        setSidebarCollapsed(false);
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Generate breadcrumbs
  const getBreadcrumbs = () => {
    const path = location.pathname;
    const crumbs = [{ label: "Resume Library", path: "/" }];

    if (path !== "/") {
      const label = BREADCRUMB_MAP[path] || path.replace("/", "").replace("-", " ");

      crumbs.push({ label: label.charAt(0).toUpperCase() + label.slice(1), path });
    }

    return crumbs;
  };

  const breadcrumbs = getBreadcrumbs();


  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Top Navigation Bar - Mobile */}
      <header className="fixed top-0 left-0 right-0 h-14 bg-background border-b z-30 md:hidden">
        <div className="flex items-center h-full px-4">
          <button
            onClick={() => setMobileOpen(true)}
            className="p-2 -ml-2 rounded-md hover:bg-accent"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="flex-1 text-center font-semibold">CareerCraftAI</span>
        </div>
      </header>

      {/* Sidebar - Mobile Drawer */}
      <aside
        className={`fixed top-0 left-0 bottom-0 w-64 bg-background border-r z-50 transform transition-transform md:hidden ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between h-14 px-4 border-b">
          <span className="font-semibold">CareerCraftAI</span>
          <button
            onClick={() => setMobileOpen(false)}
            className="p-2 -mr-2 rounded-md hover:bg-accent"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <SidebarContent
          items={NAV_ITEMS}
          placeholders={PLACEHOLDER_ITEMS}
          collapsed={false}
          onItemClick={() => {}}
        />

        {user && (
          <div className="border-t mt-auto">
            <div className="px-4 py-3 border-b">
              <div className="text-sm font-medium truncate">{user?.name || user?.email || "User"}</div>
              {user?.email && (
                <div className="text-xs text-muted-foreground truncate">{user.email}</div>
              )}
            </div>
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 transition-colors ${
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                }`
              }
            >
              <Settings className="w-5 h-5 flex-shrink-0" />
              <span>Settings</span>
            </NavLink>
            <button
              onClick={() => {
                handleLogout();
                setMobileOpen(false);
              }}
              className="flex items-center gap-3 w-full px-4 py-3 text-left text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            >
              <LogOut className="w-5 h-5 flex-shrink-0" />
              <span>Logout</span>
            </button>
          </div>
        )}
      </aside>

      {/* Sidebar - Desktop */}
      <aside
        className={`hidden md:flex flex-col fixed top-0 left-0 bottom-0 bg-background border-r z-20 transition-all duration-200 ${
          sidebarCollapsed ? "w-16" : "w-64"
        } ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        {/* Logo */}
        <div className="flex items-center h-14 px-4 border-b">
          {!sidebarCollapsed && (
            <span className="font-semibold text-lg">CareerCraftAI</span>
          )}
          {sidebarCollapsed && <span className="font-semibold text-lg">CC</span>}
        </div>

        {/* Toggle Button */}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="hidden md:flex absolute -right-3 top-16 bg-background border rounded-full p-1 shadow-sm hover:bg-accent"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-3 h-3" />
          ) : (
            <ChevronLeft className="w-3 h-3" />
          )}
        </button>

        {/* Navigation */}
        <SidebarContent
          items={NAV_ITEMS}
          placeholders={PLACEHOLDER_ITEMS}
          collapsed={sidebarCollapsed}
          onItemClick={() => {}}
        />

        {/* Settings Footer */}
        <div className="mt-auto border-t">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 transition-colors ${
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              }`
            }
          >
            <Settings className="w-5 h-5 flex-shrink-0" />
            {!sidebarCollapsed && <span>Settings</span>}
          </NavLink>
        </div>
      </aside>

      {/* Main Content Area */}
      <div
        className={`flex flex-col min-h-screen transition-all duration-200 ${
          sidebarOpen ? "md:ml-64" : "md:ml-0"
        } pt-14 md:pt-0`}
      >
        {/* Top Nav - Desktop */}
        <header className="hidden md:flex items-center justify-between h-14 px-6 bg-background border-b">
          {/* Breadcrumbs */}
          <nav className="flex items-center gap-2 text-sm">
            {breadcrumbs.map((crumb, index) => (
              <span key={crumb.path} className="flex items-center gap-2">
                {index > 0 && (
                  <span className="text-muted-foreground">/</span>
                )}
                <span
                  className={
                    index === breadcrumbs.length - 1
                      ? "font-medium"
                      : "text-muted-foreground hover:text-foreground"
                  }
                >
                  {crumb.label}
                </span>
              </span>
            ))}
          </nav>

          {/* Right Side */}
          <div className="flex items-center gap-2">
            {/* Theme Toggle */}
            <button className="p-2 rounded-md hover:bg-accent" title="Toggle theme">
              <Sun className="w-5 h-5" />
            </button>

            {/* Notifications */}
            <NotificationBell />

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 p-1.5 rounded-md hover:bg-accent"
              >
                <div className="w-7 h-7 bg-primary/20 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-primary" />
                </div>
              </button>

              {/* User Dropdown */}
              {userMenuOpen && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-background border rounded-md shadow-lg py-1 z-50">
                  <div className="px-4 py-2 border-b">
                    <div className="font-medium text-sm">
                      {user?.name || user?.email || "User"}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {user?.email || ""}
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-2 w-full px-4 py-2 text-sm text-left hover:bg-accent"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}

// Notification Bell Component
function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [generateError, setGenerateError] = useState(null);
  const ref = useRef(null);
  const { data: suggestions = [] } = useSuggestions();
  const dismissMutation = useDismissSuggestion();
  const generateMutation = useGenerateFromSuggestion();
  const navigate = useNavigate();

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!open) {
      setGenerateError(null);
    }
  }, [open]);

  const count = suggestions.length;
  const Icon = count > 0 ? BellDot : Bell;

  const handleDismiss = (id) => {
    dismissMutation.mutate(id);
  };

  const handleGenerate = (id, jobAppId) => {
    setGenerateError(null);
    generateMutation.mutate(id, {
      onSuccess: () => {
        setOpen(false);
        navigate(`/communication?jobId=${jobAppId}`);
      },
      onError: (err) => {
        const status = err?.response?.status;
        const detail = err?.response?.data?.detail || err?.response?.data?.message || err?.message;
        if (status === 429) {
          setGenerateError("AI service is temporarily rate-limited. Please wait a moment and try again.");
        } else if (detail) {
          setGenerateError(detail);
        } else {
          setGenerateError("Failed to generate. Please try again.");
        }
      },
    });
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-md hover:bg-accent"
        title="Notifications"
      >
        <Icon className="w-5 h-5" />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold text-white bg-red-500 rounded-full">
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-80 bg-background border rounded-md shadow-lg z-50 max-h-96 flex flex-col">
          <div className="flex items-center justify-between px-4 py-2 border-b">
            <span className="text-sm font-semibold">Follow-up Suggestions</span>
            <button onClick={() => setOpen(false)} className="p-1 rounded hover:bg-accent">
              <XIcon className="w-4 h-4" />
            </button>
          </div>
          {generateError && (
            <div className="px-4 py-2 bg-destructive/10 border-b">
              <p className="text-xs text-destructive font-medium">{generateError}</p>
            </div>
          )}

          {count === 0 ? (
            <div className="p-4 text-sm text-muted-foreground text-center">
              No outstanding suggestions
            </div>
          ) : (
            <div className="overflow-y-auto flex-1">
              {suggestions.map((s) => (
                <div key={s.id} className="flex items-start gap-3 px-4 py-3 border-b last:border-0 hover:bg-accent/50">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{s.job_title}</p>
                    <p className="text-xs text-muted-foreground truncate">{s.job_company}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {s.days_since_update}d since last update
                    </p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={() => handleGenerate(s.id, s.job_application_id)}
                      disabled={generateMutation.isPending}
                      className="p-1.5 rounded hover:bg-primary/10 text-primary"
                      title="Generate follow-up"
                    >
                      {generateMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <FileEdit className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDismiss(s.id)}
                      className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
                      title="Dismiss"
                    >
                      <XIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Sidebar Content Component
function SidebarContent({ items, placeholders, collapsed, onItemClick }) {
  return (
    <nav className="flex-1 py-2 overflow-y-auto">
      {items.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          onClick={onItemClick}
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-2.5 transition-colors ${
              collapsed ? "justify-center" : ""
            } ${
              isActive
                ? "bg-primary/10 text-primary border-r-2 border-primary"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            }`
          }
        >
          {item.icon && (
            <item.icon className={`w-5 h-5 flex-shrink-0 ${collapsed ? "" : ""}`} />
          )}
          {!collapsed && <span>{item.label}</span>}
        </NavLink>
      ))}

      {/* Placeholders */}
      {placeholders.map((item, index) => (
        <div
          key={index}
          className={`flex items-center gap-3 px-4 py-2.5 text-muted-foreground cursor-not-allowed opacity-50 ${
            collapsed ? "justify-center" : ""
          }`}
        >
          {item.icon && <item.icon className="w-5 h-5 flex-shrink-0" />}
          {!collapsed && (
            <span className="flex items-center gap-2">
              {item.label}
              <span className="text-xs bg-muted px-1.5 py-0.5 rounded">Soon</span>
            </span>
          )}
        </div>
      ))}
    </nav>
  );
}

