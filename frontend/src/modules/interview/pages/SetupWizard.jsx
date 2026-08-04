import { useMemo, useState } from "react";

import {
  Timer,
  Users,
  BriefcaseBusiness,
  Notebook,
  BrainCircuit,
  FileText,
  Loader2,
  Sparkles,
  Bot,
  BookOpen,
  SlidersHorizontal,
  ListChecks,
  GraduationCap,
  Clock,
  Target,
  Zap,
  CheckCircle2,
  Lightbulb,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

import { useInterviewContext } from "@/modules/interview/context/useInterviewContext";
import { PRACTICE_MODE } from "@/modules/interview/services/constants/interviewConstants";

const MODE_OPTIONS = [
  { value: "mixed", label: "Mixed" },
  { value: "hr", label: "HR" },
  { value: "technical", label: "Technical" },
  { value: "aptitude", label: "Aptitude" },
  { value: "behavioral", label: "Behavioral" },
  { value: "communication", label: "Communication" },
];

const DIFFICULTY_OPTIONS = [
  { value: "easy", label: "Easy", desc: "Fundamental concepts" },
  { value: "medium", label: "Medium", desc: "Applied knowledge" },
  { value: "hard", label: "Hard", desc: "Deep expertise" },
];

const COUNT_OPTIONS = [
  { value: 5, label: "5", desc: "Quick practice" },
  { value: 10, label: "10", desc: "Standard session" },
  { value: 20, label: "20", desc: "Deep dive" },
  { value: "custom", label: "Custom", desc: "Set your own" },
];

const TIMER_OPTIONS = [
  { value: "off", label: "Off", desc: "No time limit", icon: Zap },
  { value: "per_question", label: "Per Question", desc: "Time per answer", icon: Clock },
  { value: "entire_session", label: "Entire Session", desc: "Total time limit", icon: Timer },
];

const INTERVIEW_TYPE_OPTIONS = [
  { value: PRACTICE_MODE.PRACTICE, label: "Practice", desc: "Learn at your own pace" },
  { value: PRACTICE_MODE.MOCK, label: "Mock", desc: "Simulate real conditions" },
];

const JOB_ROLE_OPTIONS = [
  { value: "software_engineer", label: "Software Engineer" },
  { value: "frontend_developer", label: "Frontend Developer" },
  { value: "backend_developer", label: "Backend Developer" },
  { value: "full_stack_developer", label: "Full Stack Developer" },
  { value: "data_analyst", label: "Data Analyst" },
  { value: "custom", label: "Custom Role" },
];

const CATEGORY_OPTIONS = [
  { value: "hr", label: "HR", icon: Users, color: "from-blue-500/20 to-blue-500/5", border: "border-blue-500/30", text: "text-blue-600" },
  { value: "technical", label: "Technical", icon: BrainCircuit, color: "from-violet-500/20 to-violet-500/5", border: "border-violet-500/30", text: "text-violet-600" },
  { value: "behavioral", label: "Behavioral", icon: Target, color: "from-emerald-500/20 to-emerald-500/5", border: "border-emerald-500/30", text: "text-emerald-600" },
  { value: "communication", label: "Communication", icon: MessageSquare, color: "from-amber-500/20 to-amber-500/5", border: "border-amber-500/30", text: "text-amber-600" },
  { value: "aptitude", label: "Aptitude", icon: BrainCircuit, color: "from-rose-500/20 to-rose-500/5", border: "border-rose-500/30", text: "text-rose-600" },
];

function SegmentedControl({ value, options, onChange, label }) {
  return (
    <div className="space-y-1.5">
      {label && <p className="text-xs font-medium text-muted-foreground">{label}</p>}
      <div className="inline-flex rounded-xl border border-border/60 bg-muted/30 p-0.5" role="radiogroup">
        {options.map((o) => {
          const selected = value === o.value;
          return (
            <button
              key={o.value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange(o.value)}
              className={
                "relative rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                (selected
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground")
              }
            >
              {o.label || o}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function SegmentedControlCard({ value, options, onChange, label, icon: Icon }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5">
        {Icon && <Icon className="size-3.5 text-muted-foreground" />}
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
      </div>
      <div className="grid grid-cols-3 gap-2" role="radiogroup">
        {options.map((o) => {
          const selected = value === o.value;
          return (
            <button
              key={o.value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange(o.value)}
              className={
                "relative rounded-xl border p-3 text-left transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                (selected
                  ? "border-primary/40 bg-primary/[0.04] shadow-sm ring-1 ring-primary/10"
                  : "border-border/60 bg-background hover:bg-muted/30 hover:border-muted-foreground/30")
              }
            >
              <p className="text-sm font-semibold">{o.label}</p>
              <p className="text-[11px] text-muted-foreground mt-0.5 leading-tight">{o.desc || ""}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function MessageSquare({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

export default function InterviewSetupWizard() {
  const { session } = useInterviewContext();

  const [interviewMode, setInterviewMode] = useState(null);
  const [difficulty, setDifficulty] = useState(null);
  const [questionCountChoice, setQuestionCountChoice] = useState(null);
  const [customQuestionCount, setCustomQuestionCount] = useState(10);
  const [timerMode, setTimerMode] = useState("off");
  const [interviewType, setInterviewType] = useState(PRACTICE_MODE.PRACTICE);
  const [jobRole, setJobRole] = useState(null);
  const [customJobRole, setCustomJobRole] = useState("");
  const [company, setCompany] = useState("");
  const [notes, setNotes] = useState("");

  const [aiMode, setAiMode] = useState(false);
  const [jobTitle, setJobTitle] = useState("");
  const [skills, setSkills] = useState("");

  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState(null);

  const resolvedQuestionCount = useMemo(() => {
    if (questionCountChoice === "custom") return Number(customQuestionCount);
    return questionCountChoice;
  }, [questionCountChoice, customQuestionCount]);

  const jobRoleFinal = useMemo(() => {
    if (jobRole === "custom") return customJobRole.trim() || "custom";
    return jobRole;
  }, [jobRole, customJobRole]);

  const canStart = useMemo(() => {
    if (aiMode) {
      if (!jobTitle.trim()) return false;
    } else {
      if (!interviewMode) return false;
      if (!difficulty) return false;
    }
    if (!questionCountChoice) return false;
    if (questionCountChoice === "custom") {
      if (!Number.isFinite(resolvedQuestionCount) || resolvedQuestionCount <= 0) return false;
    }
    return true;
  }, [aiMode, jobTitle, interviewMode, difficulty, questionCountChoice, resolvedQuestionCount]);

  async function handleStartInterview() {
    setError(null);
    if (!canStart || isStarting) return;
    setIsStarting(true);
    try {
      const config = {
        interviewMode: aiMode ? undefined : interviewMode,
        difficulty: aiMode ? undefined : difficulty,
        questionCount: resolvedQuestionCount,
        timerMode,
        interviewType,
        company: company.trim() || undefined,
        jobRole: jobRoleFinal,
        notes: notes.trim() || undefined,
        jobTitle: aiMode ? jobTitle.trim() : undefined,
        skills: aiMode ? skills.split(",").map((s) => s.trim()).filter(Boolean) : undefined,
      };
      await session.createSession(config);
      session.startSession();
    } catch (e) {
      setError(e?.message || "Failed to start interview.");
    } finally {
      setIsStarting(false);
    }
  }

  const summaryItems = [];
  if (aiMode) {
    if (jobTitle.trim()) summaryItems.push({ label: "Role", value: jobTitle.trim() });
    if (skills.trim()) summaryItems.push({ label: "Skills", value: skills.trim() });
  } else {
    if (interviewMode) summaryItems.push({ label: "Category", value: MODE_OPTIONS.find(o => o.value === interviewMode)?.label ?? interviewMode });
    if (difficulty) summaryItems.push({ label: "Difficulty", value: DIFFICULTY_OPTIONS.find(o => o.value === difficulty)?.label ?? difficulty });
  }
  if (questionCountChoice) {
    const countLabel = COUNT_OPTIONS.find(o => o.value === questionCountChoice)?.label ?? questionCountChoice;
    summaryItems.push({ label: "Questions", value: countLabel === "Custom" ? String(resolvedQuestionCount) : String(countLabel) });
  }
  if (timerMode !== "off") {
    summaryItems.push({ label: "Timer", value: TIMER_OPTIONS.find(o => o.value === timerMode)?.label ?? timerMode });
  }
  if (jobRole) {
    const roleLabel = JOB_ROLE_OPTIONS.find(o => o.value === jobRole)?.label ?? jobRole;
    summaryItems.push({ label: "Job Role", value: roleLabel });
  }

  const estimatedMinutes = useMemo(() => {
    if (!questionCountChoice) return null;
    const count = questionCountChoice === "custom" ? resolvedQuestionCount : questionCountChoice;
    if (!count) return null;
    if (timerMode === "per_question") return `${count * 3}–${count * 5}m`;
    if (timerMode === "entire_session") return `~${count * 4}m`;
    return `~${count * 3}m`;
  }, [questionCountChoice, resolvedQuestionCount, timerMode]);

  return (
    <div className="mx-auto max-w-5xl animate-in fade-in duration-200">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/[0.04] via-primary/[0.02] to-background border border-border/50 mb-8 p-8 md:p-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,hsl(var(--primary)/0.06),transparent_70%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,hsl(var(--primary)/0.03),transparent_50%)]" />
        <div className="relative space-y-6">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary/15 to-primary/5 ring-1 ring-primary/10">
              <Sparkles className="size-4 text-primary" />
            </div>
            <span className="text-xs font-semibold tracking-[0.15em] text-muted-foreground uppercase">
              AI Mock Interview
            </span>
          </div>
          <div className="max-w-2xl space-y-3">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
              Configure your practice session
            </h1>
            <p className="text-base text-muted-foreground leading-relaxed">
              Generate interview questions tailored to your target role, skills, and experience level. Get AI-powered feedback after every answer.
            </p>
          </div>
          <div className="flex flex-wrap gap-4 pt-1">
            {[
              { icon: FileText, label: "Resume" },
              { icon: BriefcaseBusiness, label: "Role" },
              { icon: ListChecks, label: "Skills" },
              { icon: SlidersHorizontal, label: "Difficulty" },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-muted/50 text-xs font-medium text-muted-foreground">
                <item.icon className="size-3.5" />
                {item.label}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6 mb-32 lg:mb-0">
          {/* Job Role — moved near top */}
          <Card>
            <CardContent className="p-5 md:p-6 space-y-4">
              <div className="flex items-center gap-2.5">
                <div className="flex size-7 items-center justify-center rounded-lg bg-gradient-to-br from-primary/10 to-primary/5">
                  <BriefcaseBusiness className="size-3.5 text-primary" />
                </div>
                <span className="text-sm font-semibold">Target Role</span>
              </div>
              <div className="space-y-2.5">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2" role="radiogroup" aria-label="Job role">
                  {JOB_ROLE_OPTIONS.map((o) => {
                    const selected = jobRole === o.value;
                    return (
                      <button
                        key={o.value}
                        type="button"
                        role="radio"
                        aria-checked={selected}
                        onClick={() => setJobRole(o.value)}
                        className={
                          "relative rounded-xl border px-3.5 py-3 text-left transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                          (selected
                            ? "border-primary/40 bg-primary/[0.04] shadow-sm ring-1 ring-primary/10"
                            : "border-border/60 bg-background hover:bg-muted/30 hover:border-muted-foreground/30")
                        }
                      >
                        <span className="text-sm font-medium">{o.label}</span>
                      </button>
                    );
                  })}
                </div>
                {jobRole === "custom" && (
                  <div>
                    <Label htmlFor="customJobRole" className="text-xs text-muted-foreground">Custom role title</Label>
                    <Input
                      id="customJobRole"
                      value={customJobRole}
                      onChange={(e) => setCustomJobRole(e.target.value)}
                      placeholder="e.g. Mobile Developer"
                      className="mt-1"
                    />
                  </div>
                )}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="company" className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                    <Building className="size-3" />
                    Company <span className="text-muted-foreground/60 font-normal">(optional)</span>
                  </Label>
                  <Input
                    id="company"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    placeholder="e.g. Google"
                  />
                </div>
                <SegmentedControl
                  label="Interview Type"
                  value={interviewType}
                  options={INTERVIEW_TYPE_OPTIONS.map(o => ({ value: o.value, label: o.label }))}
                  onChange={(v) => setInterviewType(v)}
                />
              </div>
            </CardContent>
          </Card>

          {/* Question Source */}
          <Card>
            <CardContent className="p-5 md:p-6 space-y-5">
              <div className="flex items-center gap-2.5">
                <div className="flex size-7 items-center justify-center rounded-lg bg-gradient-to-br from-primary/10 to-primary/5">
                  <BrainCircuit className="size-3.5 text-primary" />
                </div>
                <span className="text-sm font-semibold">Question Source</span>
              </div>

              <div className="grid grid-cols-2 gap-3" role="radiogroup" aria-label="Question source">
                {[
                  { value: false, label: "Question Bank", desc: "Curated questions from our library", icon: BookOpen },
                  { value: true, label: "AI Generated", desc: "Questions tailored to your role & skills", icon: Bot },
                ].map((o) => {
                  const selected = aiMode === o.value;
                  return (
                    <button
                      key={String(o.value)}
                      type="button"
                      role="radio"
                      aria-checked={selected}
                      onClick={() => setAiMode(o.value)}
                      className={
                        "relative rounded-xl border p-4 text-left transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                        (selected
                          ? "border-primary/40 bg-primary/[0.04] shadow-sm ring-1 ring-primary/10"
                          : "border-border/60 bg-background hover:bg-muted/30 hover:border-muted-foreground/30")
                      }
                    >
                      <div className="flex items-center gap-2.5">
                        <div className={`flex size-8 items-center justify-center rounded-lg transition-colors ${selected ? "bg-primary/10" : "bg-muted"}`}>
                          <o.icon className={`size-4 ${selected ? "text-primary" : "text-muted-foreground"}`} />
                        </div>
                        <div>
                          <p className="text-sm font-medium">{o.label}</p>
                          <p className="text-[11px] text-muted-foreground leading-tight">{o.desc}</p>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>

              {aiMode ? (
                <div className="space-y-4 pt-1 animate-in fade-in slide-in-from-top-1 duration-200">
                  <div className="space-y-2">
                    <Label htmlFor="jobTitle" className="text-xs font-medium text-muted-foreground">Job Title</Label>
                    <Input
                      id="jobTitle"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                      placeholder="e.g. Software Engineer"
                      className="h-10"
                    />
                    <p className="text-[11px] text-muted-foreground">Questions will be tailored to this role</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="skills" className="text-xs font-medium text-muted-foreground">
                      Skills
                      <span className="text-muted-foreground/60 font-normal ml-1">(comma-separated)</span>
                    </Label>
                    <Input
                      id="skills"
                      value={skills}
                      onChange={(e) => setSkills(e.target.value)}
                      placeholder="e.g. Python, React, SQL"
                      className="h-10"
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-5 pt-1 animate-in fade-in slide-in-from-top-1 duration-200">
                  {/* Categories as chips */}
                  <div className="space-y-2.5">
                    <div className="flex items-center gap-1.5">
                      <ListChecks className="size-3.5 text-muted-foreground" />
                      <p className="text-xs font-medium text-muted-foreground">Categories</p>
                    </div>
                    <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Category">
                      {CATEGORY_OPTIONS.map((cat) => {
                        const selected = interviewMode === cat.value;
                        return (
                          <button
                            key={cat.value}
                            type="button"
                            role="radio"
                            aria-checked={selected}
                            onClick={() => setInterviewMode(cat.value)}
                            className={
                              "relative flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                              (selected
                                ? `${cat.border} ${cat.color} shadow-sm ${cat.text}`
                                : "border-border/60 bg-background hover:bg-muted/30 hover:border-muted-foreground/30 text-muted-foreground hover:text-foreground")
                            }
                          >
                            <cat.icon className="size-4" />
                            {cat.label}
                            {selected && <CheckCircle2 className="size-3.5 ml-0.5" />}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Difficulty as segmented cards */}
                  <SegmentedControlCard
                    label="Difficulty"
                    icon={SlidersHorizontal}
                    value={difficulty}
                    options={DIFFICULTY_OPTIONS}
                    onChange={(v) => setDifficulty(v)}
                  />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Session Settings */}
          <Card>
            <CardContent className="p-5 md:p-6 space-y-5">
              <div className="flex items-center gap-2.5">
                <div className="flex size-7 items-center justify-center rounded-lg bg-gradient-to-br from-primary/10 to-primary/5">
                  <FileText className="size-3.5 text-primary" />
                </div>
                <span className="text-sm font-semibold">Session Settings</span>
              </div>

              {/* Question Count */}
              <div className="space-y-2.5">
                <div className="flex items-center gap-1.5">
                  <ListChecks className="size-3.5 text-muted-foreground" />
                  <p className="text-xs font-medium text-muted-foreground">Question Count</p>
                </div>
                <div className="grid grid-cols-4 gap-2" role="radiogroup" aria-label="Question count">
                  {COUNT_OPTIONS.map((o) => {
                    const selected = questionCountChoice === o.value;
                    return (
                      <button
                        key={o.value}
                        type="button"
                        role="radio"
                        aria-checked={selected}
                        onClick={() => setQuestionCountChoice(o.value)}
                        className={
                          "relative rounded-xl border p-3 text-center transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                          (selected
                            ? "border-primary/40 bg-primary/[0.04] shadow-sm ring-1 ring-primary/10"
                            : "border-border/60 bg-background hover:bg-muted/30 hover:border-muted-foreground/30")
                        }
                      >
                        <p className="text-base font-bold">{o.label}</p>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{o.desc}</p>
                      </button>
                    );
                  })}
                </div>
                {questionCountChoice === "custom" && (
                  <div className="flex items-center gap-3 pt-1">
                    <Label htmlFor="customQuestionCount" className="text-xs text-muted-foreground shrink-0">
                      Number of questions
                    </Label>
                    <Input
                      id="customQuestionCount"
                      type="number"
                      min={1}
                      value={customQuestionCount}
                      onChange={(e) => setCustomQuestionCount(e.target.value === "" ? 0 : Number(e.target.value))}
                      className="w-24 h-9"
                      aria-invalid={resolvedQuestionCount <= 0}
                    />
                    {resolvedQuestionCount <= 0 && (
                      <p className="text-xs text-destructive">Must be greater than 0</p>
                    )}
                  </div>
                )}
              </div>

              {/* Timer */}
              <SegmentedControlCard
                label="Timer"
                icon={Timer}
                value={timerMode}
                options={TIMER_OPTIONS}
                onChange={(v) => setTimerMode(v)}
              />
            </CardContent>
          </Card>

          {/* Context & Notes */}
          <Card>
            <CardContent className="p-5 md:p-6 space-y-4">
              <div className="flex items-center gap-2.5">
                <div className="flex size-7 items-center justify-center rounded-lg bg-gradient-to-br from-primary/10 to-primary/5">
                  <Notebook className="size-3.5 text-primary" />
                </div>
                <span className="text-sm font-semibold">Notes & Context</span>
              </div>
              <div className="space-y-2">
                <Label htmlFor="notes" className="text-xs font-medium text-muted-foreground">
                  Topics, goals, or constraints
                  <span className="text-muted-foreground/60 font-normal ml-1">(optional)</span>
                </Label>
                <Textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Focus on system design questions, I have a Google interview next week..."
                  className="min-h-20 resize-none"
                />
              </div>

              {error && (
                <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Summary - desktop */}
        <div className="hidden lg:block">
          <div className="sticky top-24 space-y-4">
            <div className="space-y-3">
              <p className="text-xs font-semibold tracking-wider text-muted-foreground uppercase flex items-center gap-1.5">
                <GraduationCap className="size-3.5" />
                Session Summary
              </p>
              <Card>
                <CardContent className="p-5 space-y-4">
                  {summaryItems.length === 0 ? (
                    <div className="text-center py-4">
                      <div className="flex items-center justify-center mb-2">
                        <BrainCircuit className="size-8 text-muted-foreground/30" />
                      </div>
                      <p className="text-xs text-muted-foreground">Configure your session above to see a summary.</p>
                    </div>
                  ) : (
                    <>
                      <div className="space-y-3">
                        {summaryItems.map((item) => (
                          <div key={item.label} className="flex items-center justify-between gap-2">
                            <span className="text-xs text-muted-foreground">{item.label}</span>
                            <span className="text-xs font-semibold truncate max-w-[140px]">{item.value}</span>
                          </div>
                        ))}
                      </div>
                      <div className="border-t border-border/50 pt-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-muted-foreground">Est. Duration</span>
                          <span className="text-xs font-semibold">{estimatedMinutes || "\u2014"}</span>
                        </div>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </div>

            <Button
              type="button"
              onClick={handleStartInterview}
              disabled={!canStart || isStarting}
              size="lg"
              className="w-full gap-2.5 h-12 shadow-lg shadow-primary/20 active:scale-[0.97] text-base"
            >
              {isStarting ? (
                <><Loader2 className="size-5 animate-spin" />Starting interview\u2026</>
              ) : (
                <><Zap className="size-5" />Start AI Interview</>
              )}
            </Button>

            <div className="rounded-xl bg-gradient-to-br from-primary/[0.03] to-transparent border border-primary/10 p-4 space-y-2">
              <div className="flex items-center gap-1.5">
                <Lightbulb className="size-3.5 text-amber-500" />
                <p className="text-xs font-medium text-muted-foreground">Pro Tips</p>
              </div>
              <ul className="space-y-1.5 text-xs text-muted-foreground">
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="size-3 mt-0.5 shrink-0 text-emerald-500" />
                  AI mode generates questions based on your job title and skills
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="size-3 mt-0.5 shrink-0 text-emerald-500" />
                  Each answer receives detailed AI evaluation and scoring
                </li>
                <li className="flex items-start gap-1.5">
                  <CheckCircle2 className="size-3 mt-0.5 shrink-0 text-emerald-500" />
                  Practice mode lets you pause anytime; Mock mode simulates real conditions
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Sticky Bottom Bar - mobile */}
      <div className="fixed bottom-0 left-0 right-0 z-50 lg:hidden">
        <div className="bg-background border-t border-border/80 shadow-2xl shadow-black/10 px-4 py-3">
          <div className="max-w-5xl mx-auto flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              {summaryItems.length > 0 && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground truncate">
                  {summaryItems.slice(0, 3).map((item, i) => (
                    <span key={item.label} className="flex items-center gap-1">
                      <span className="font-medium text-foreground/80">{item.label}:</span>
                      <span className="font-semibold text-foreground truncate max-w-20">{item.value}</span>
                      {i < Math.min(summaryItems.length, 3) - 1 && <span className="text-border mx-0.5">|</span>}
                    </span>
                  ))}
                </div>
              )}
              {estimatedMinutes && (
                <Badge variant="outline" className="text-[10px] shrink-0 gap-1">
                  <Clock className="size-3" />
                  {estimatedMinutes}
                </Badge>
              )}
            </div>
            <Button
              type="button"
              onClick={handleStartInterview}
              disabled={!canStart || isStarting}
              size="lg"
              className="gap-2 shrink-0 shadow-lg shadow-primary/20 active:scale-[0.97]"
            >
              {isStarting ? (
                <><Loader2 className="size-4 animate-spin" />Starting</>
              ) : (
                <><Zap className="size-4" />Start Interview</>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Building({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="2" width="16" height="20" rx="2" ry="2" />
      <path d="M9 22v-4h6v4" />
      <path d="M8 6h.01" />
      <path d="M16 6h.01" />
      <path d="M12 6h.01" />
      <path d="M12 10h.01" />
      <path d="M12 14h.01" />
      <path d="M16 10h.01" />
      <path d="M16 14h.01" />
      <path d="M8 10h.01" />
      <path d="M8 14h.01" />
    </svg>
  );
}
