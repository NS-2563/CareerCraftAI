import { useMemo, useState } from "react";

import { LockKeyhole, Sparkles, Timer, Users, BriefcaseBusiness, Notebook, Target, Sparkle } from "lucide-react";


import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

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
  { value: "mixed", label: "Mixed" },
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" },
];

const COUNT_OPTIONS = [
  { value: 5, label: "5" },
  { value: 10, label: "10" },
  { value: 20, label: "20" },
  { value: 30, label: "30" },
  { value: "custom", label: "Custom" },
];

const TIMER_OPTIONS = [
  { value: "off", label: "Off" },
  { value: "per_question", label: "Per Question" },
  { value: "entire_session", label: "Entire Session" },
];

const INTERVIEW_TYPE_OPTIONS = [
  { value: PRACTICE_MODE.PRACTICE, label: "Practice" },
  { value: PRACTICE_MODE.MOCK, label: "Mock Interview" },
];

const JOB_ROLE_OPTIONS = [
  { value: "software_engineer", label: "Software Engineer" },
  { value: "frontend_developer", label: "Frontend Developer" },
  { value: "backend_developer", label: "Backend Developer" },
  { value: "full_stack_developer", label: "Full Stack Developer" },
  { value: "data_analyst", label: "Data Analyst" },
  { value: "custom", label: "Custom" },
];

function OptionButtons({
  label,
  value,
  options,
  onChange,
  icon: Icon,
  ariaLabel,
}) {
  return (
    <div className="space-y-2">
      <Label className="flex items-center gap-2">
        {Icon ? <Icon className="size-4 text-muted-foreground" aria-hidden="true" /> : null}
        <span>{label}</span>
      </Label>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2" aria-label={ariaLabel} role="radiogroup">
        {options.map((o) => {
          const selected = value === o.value;
          return (
            <button
              key={o.value}
              type="button"
              role="radio"
              aria-checked={selected}
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(o.value)}
              className={
                "w-full rounded-lg border px-3 py-2 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                (selected
                  ? "border-ring bg-muted/40"
                  : "border-border bg-background hover:bg-muted/30")
              }
            >
              <div className="text-sm font-medium">{o.label}</div>
            </button>
          );
        })}
      </div>
    </div>
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
    if (!interviewMode) return false;
    if (!difficulty) return false;
    if (!questionCountChoice) return false;

    if (questionCountChoice === "custom") {
      if (!Number.isFinite(resolvedQuestionCount) || resolvedQuestionCount <= 0) return false;
    }

    return true;
  }, [interviewMode, difficulty, questionCountChoice, resolvedQuestionCount]);

  async function handleStartInterview() {


    setError(null);
    if (!canStart || isStarting) {
      return;
    }



    setIsStarting(true);

    try {
      const config = {

        interviewMode,
        difficulty,
        questionCount: resolvedQuestionCount,
        timerMode,
        interviewType,
        company: company.trim() || undefined,
        jobRole: jobRoleFinal,
        notes: notes.trim() || undefined,
      };
      await session.createSession(config);
      session.startSession();

    } catch (e) {
      setError(e?.message || "Failed to start interview.");
    } finally {
      setIsStarting(false);
    }
  }

  return (
    <div className="w-full px-2 sm:px-0">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="space-y-1">
          <h1 className="text-xl sm:text-2xl font-semibold">Interview Setup Wizard</h1>
          <p className="text-sm text-muted-foreground">Configure your session. No interview content will appear until later phases.</p>
        </div>
        <div className="hidden md:flex items-center gap-2 text-muted-foreground">
          <Sparkles className="size-4" aria-hidden="true" />
          <span className="text-sm">Setup</span>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="size-4" aria-hidden="true" />
            Interview Configuration
          </CardTitle>
          <CardDescription>Choose the mode, difficulty, and question count.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <OptionButtons
            label="Interview Mode"
            value={interviewMode}
            options={MODE_OPTIONS}
            onChange={(v) => setInterviewMode(v)}
            icon={Users}
            ariaLabel="Interview mode"
          />

          <OptionButtons
            label="Difficulty"
            value={difficulty}
            options={DIFFICULTY_OPTIONS}
            onChange={(v) => setDifficulty(v)}
            icon={BriefcaseBusiness}
            ariaLabel="Difficulty"
          />

          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <LockKeyhole className="size-4 text-muted-foreground" aria-hidden="true" />
              Number of Questions
            </Label>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2" role="radiogroup" aria-label="Question count">
              {COUNT_OPTIONS.map((o) => {
                const selected = questionCountChoice === o.value;
                return (
                  <button
                    key={o.value}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    tabIndex={selected ? 0 : -1}
                    onClick={() => setQuestionCountChoice(o.value)}
                    className={
                      "w-full rounded-lg border px-3 py-2 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                      (selected
                        ? "border-ring bg-muted/40"
                        : "border-border bg-background hover:bg-muted/30")
                    }
                  >
                    <div className="text-sm font-medium">{o.label}</div>
                  </button>
                );
              })}
            </div>

            {questionCountChoice === "custom" ? (
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-[160px_1fr] gap-3 items-center">
                <Label htmlFor="customQuestionCount" className="text-sm font-medium">
                  Custom count
                </Label>
                <Input
                  id="customQuestionCount"
                  type="number"
                  min={1}
                  value={customQuestionCount}
                  onChange={(e) => setCustomQuestionCount(e.target.value === "" ? 0 : Number(e.target.value))}
                  aria-invalid={questionCountChoice === "custom" && resolvedQuestionCount <= 0}
                />
              </div>
            ) : null}

            {questionCountChoice === "custom" && resolvedQuestionCount <= 0 ? (
              <p className="text-sm text-destructive">Custom question count must be greater than 0.</p>
            ) : null}
          </div>

          <OptionButtons
            label="Timer Mode"
            value={timerMode}
            options={TIMER_OPTIONS}
            onChange={(v) => setTimerMode(v)}
            icon={Timer}
            ariaLabel="Timer mode"
          />

          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Sparkle className="size-4 text-muted-foreground" aria-hidden="true" />
              Interview Type
            </Label>
            <div className="grid grid-cols-2 gap-2">
              {INTERVIEW_TYPE_OPTIONS.map((o) => {
                const selected = interviewType === o.value;
                return (
                  <button
                    key={o.value}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    tabIndex={selected ? 0 : -1}
                    onClick={() => setInterviewType(o.value)}
                    className={
                      "w-full rounded-lg border px-3 py-2 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring " +
                      (selected
                        ? "border-ring bg-muted/40"
                        : "border-border bg-background hover:bg-muted/30")
                    }
                  >
                    <div className="text-sm font-medium">{o.label}</div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="jobRole" className="flex items-center gap-2">
              <BriefcaseBusiness className="size-4 text-muted-foreground" aria-hidden="true" />
              Job Role
            </Label>
            <select
              id="jobRole"
              value={jobRole ?? ""}
              onChange={(e) => setJobRole(e.target.value || null)}
              className="h-9 w-full rounded-md border border-input bg-transparent px-2.5 py-1 text-base shadow-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              <option value="" disabled>
                Select job role
              </option>
              {JOB_ROLE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>

            {jobRole === "custom" ? (
              <div className="mt-3">
                <Label htmlFor="customJobRole" className="text-sm font-medium">
                  Custom role
                </Label>
                <Input
                  id="customJobRole"
                  value={customJobRole}
                  onChange={(e) => setCustomJobRole(e.target.value)}
                  placeholder="e.g. Mobile Developer"
                />
              </div>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="company" className="flex items-center gap-2">
              <BriefcaseBusiness className="size-4 text-muted-foreground" aria-hidden="true" />
              Company <span className="text-muted-foreground text-xs">(optional)</span>
            </Label>
            <Input id="company" value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Company name" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes" className="flex items-center gap-2">
              <Notebook className="size-4 text-muted-foreground" aria-hidden="true" />
              Notes <span className="text-muted-foreground text-xs">(optional)</span>
            </Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Anything you want to practice with (topics, goals, constraints)..."
            />
          </div>

          {error ? (
            <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          ) : null}

          <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
            <div className="text-sm text-muted-foreground">
              {isStarting ? "Creating session…" : "Ready to begin when configured."}
            </div>
            <Button
              type="button"
              onClick={handleStartInterview}
              disabled={!canStart || isStarting}
              className="w-full sm:w-auto"
            >
              {isStarting ? "Starting…" : "Start Interview"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <p className="mt-4 text-xs text-muted-foreground">
        This phase only creates the interview session configuration. The interview UI, timers, scoring, AI, and results are implemented in later phases.
      </p>
    </div>
  );
}



