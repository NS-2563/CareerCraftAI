import {
  LayoutDashboard,
  FolderOpen,
  FileText,
  ScanSearch,
  PenLine,
  Briefcase,
  Mic,
  Compass,
  Inbox,
  History,
  Settings,
  User,
} from "lucide-react"

/**
 * Central registry of real application modules, matching the routes defined in
 * `frontend/src/App.jsx`. Read by both the sidebar navigation and the command
 * palette so a single source of truth drives navigation.
 *
 * @typedef {{
 *   id: string
 *   name: string
 *   short: string
 *   href: string
 *   description: string
 *   icon: import("lucide-react").LucideIcon
 *   accent: string
 *   group: "overview" | "documents" | "search" | "growth"
 * }} AppModule
 */

/** @type {AppModule[]} */
export const modules = [
  {
    id: "dashboard",
    name: "Dashboard",
    short: "Home",
    href: "/",
    description: "Your career at a glance",
    icon: LayoutDashboard,
    accent: "var(--brand)",
    group: "overview",
  },
  {
    id: "resume-library",
    name: "Resume Library",
    short: "Library",
    href: "/resumes",
    description: "Every resume version, organized",
    icon: FolderOpen,
    accent: "var(--indigo)",
    group: "documents",
  },
  {
    id: "resume-studio",
    name: "Resume Studio",
    short: "Builder",
    href: "/resume-studio",
    description: "Craft resumes with live AI guidance",
    icon: FileText,
    accent: "var(--blue)",
    group: "documents",
  },
  {
    id: "resume-analysis",
    name: "Resume Analysis",
    short: "Analysis",
    href: "/resume",
    description: "Score, ATS-check, and improve",
    icon: ScanSearch,
    accent: "var(--emerald)",
    group: "documents",
  },
  {
    id: "cover-letter",
    name: "Cover Letter Studio",
    short: "Cover Letters",
    href: "/cover-letter-studio",
    description: "Tailored letters in seconds",
    icon: PenLine,
    accent: "var(--violet)",
    group: "documents",
  },
  {
    id: "cover-letter-library",
    name: "Cover Letter Library",
    short: "Letter Library",
    href: "/cover-letter-library",
    description: "Saved letters, ATS coverage, and version history",
    icon: History,
    accent: "var(--violet)",
    group: "documents",
  },
  {
    id: "jobs",
    name: "Job Tracker",
    short: "Jobs",
    href: "/jobs",
    description: "Track every application",
    icon: Briefcase,
    accent: "var(--cyan)",
    group: "search",
  },
  {
    id: "interview-prep",
    name: "Interview Prep",
    short: "Interviews",
    href: "/interview",
    description: "Practice with an AI interviewer",
    icon: Mic,
    accent: "var(--rose)",
    group: "search",
  },
  {
    id: "career-coach",
    name: "AI Career Coach",
    short: "Coach",
    href: "/career",
    description: "Personalized career strategy",
    icon: Compass,
    accent: "var(--amber)",
    group: "growth",
  },
  {
    id: "communication",
    name: "Communication",
    short: "Messages",
    href: "/communication",
    description: "Outreach, follow-ups & templates",
    icon: Inbox,
    accent: "var(--teal)",
    group: "growth",
  },
  {
    id: "activity",
    name: "Activity Timeline",
    short: "Activity",
    href: "/activity",
    description: "Your full cross-module history",
    icon: History,
    accent: "var(--slate)",
    group: "overview",
  },
]

export const accountNav = [
  { name: "Profile", href: "/profile", icon: User },
  { name: "Settings", href: "/settings", icon: Settings },
]

/**
 * True when the current pathname belongs to a module. Handles nested routes so
 * sub-pages highlight their parent module (e.g. `/interview/practice` matches
 * the Interview Prep module) while avoiding prefix collisions like `/resume`
 * vs `/resume-studio`.
 */
export function isModuleActive(pathname, href) {
  if (href === "/") return pathname === "/"
  return pathname === href || pathname.startsWith(href + "/")
}

export function getActiveModule(pathname) {
  return modules.find((m) => isModuleActive(pathname, m.href))
}

export const navGroups = [
  { label: "Overview", group: "overview" },
  { label: "Documents", group: "documents" },
  { label: "Job Search", group: "search" },
  { label: "Growth", group: "growth" },
]
