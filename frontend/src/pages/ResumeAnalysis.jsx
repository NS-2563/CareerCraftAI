import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sparkles, FileText, CheckCircle2, AlertTriangle, TrendingUp, BarChart3, RefreshCw, Brain, Lightbulb, XCircle, ChevronDown, ChevronUp, Target, Award, ArrowRight, Wrench, Database } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { SuccessBanner, ScoreTooltip } from "@/components/ui/atoms";
import { Separator } from "@/components/ui/separator";
import AILoading from "@/components/ai/AILoading";
import { useResumeContext } from "@/context/useResumeContext";
import resumeApi from "@/services/resumeApi";
import { analyzeResume, getCachedAnalysis, reAnalyzeResume, getScoreHistory, getScoreHistoryDiff } from "@/services/analysisApi";

function ScoreBadge({ score, size = "md", ...props }) {
  const color = score >= 80 ? "bg-green-100 text-green-700 border-green-200" :
    score >= 60 ? "bg-yellow-100 text-yellow-700 border-yellow-200" :
    "bg-red-100 text-red-700 border-red-200";
  return (
    <span {...props} className={`inline-flex items-center justify-center font-bold rounded-full border ${color} ${size === "lg" ? "text-3xl w-20 h-20" : "text-lg w-12 h-12"}`}>
      {score}
    </span>
  );
}

function ScoreCard({ icon: Icon, label, score, sublabel, color = "primary", tooltip }) {
  const scoreDisplay = (
    <div className="text-2xl font-bold mt-0.5">{score}<span className="text-sm font-normal text-muted-foreground">/100</span></div>
  );
  return (
    <Card className="h-full">
      <CardContent className="p-4 flex items-start gap-3">
        <div className={`p-2 rounded-lg bg-${color}/10 shrink-0`}>
          <Icon className={`w-5 h-5 text-${color}`} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm text-muted-foreground truncate">{label}</div>
          {tooltip ? (
            <ScoreTooltip description={tooltip}>{scoreDisplay}</ScoreTooltip>
          ) : (
            scoreDisplay
          )}
          {sublabel && <div className="text-xs text-muted-foreground mt-1">{sublabel}</div>}
        </div>
      </CardContent>
    </Card>
  );
}

function ExpandableSection({ title, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Card>
      <button onClick={() => setOpen(!open)} className="w-full text-left">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">{title}</CardTitle>
          {open ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
        </CardHeader>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}>
            <CardContent className="pt-0">{children}</CardContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

function StrengthItem({ item }) {
  return (
    <div className="p-3 rounded-lg bg-green-50 border border-green-200">
      <div className="flex items-start gap-2">
        <Award className="w-4 h-4 text-green-600 mt-0.5 shrink-0" />
        <div>
          <div className="font-medium text-sm text-green-800">{item.title}</div>
          <div className="text-xs text-green-700 mt-1">{item.description}</div>
          {item.category && <Badge variant="outline" className="mt-1.5 text-green-600 border-green-300 bg-green-50">{item.category}</Badge>}
        </div>
      </div>
    </div>
  );
}

function WeaknessItem({ item }) {
  const severityColor = item.severity === "high" ? "red" : item.severity === "medium" ? "yellow" : "blue";
  return (
    <div className={`p-3 rounded-lg border bg-${severityColor}-50 border-${severityColor}-200`}>
      <div className="flex items-start gap-2">
        <AlertTriangle className={`w-4 h-4 text-${severityColor}-600 mt-0.5 shrink-0`} />
        <div>
          <div className="font-medium text-sm">{item.title}</div>
          <div className="text-xs text-muted-foreground mt-1">{item.description}</div>
          <div className="flex gap-2 mt-1.5">
            {item.category && <Badge variant="outline">{item.category}</Badge>}
            <Badge variant={item.severity === "high" ? "destructive" : "secondary"}>{item.severity}</Badge>
          </div>
        </div>
      </div>
    </div>
  );
}

function QualityFindingItem({ finding, type }) {
  const iconMap = { issue: <XCircle className="w-4 h-4 text-red-500" />, warning: <AlertTriangle className="w-4 h-4 text-yellow-500" />, strength: <CheckCircle2 className="w-4 h-4 text-green-500" /> };
  const bgMap = { issue: "bg-red-50 border-red-200", warning: "bg-yellow-50 border-yellow-200", strength: "bg-green-50 border-green-200" };
  return (
    <div className={`p-2.5 rounded-lg border ${bgMap[finding.type] || bgMap[type]}`}>
      <div className="flex items-start gap-2">
        {iconMap[finding.type] || iconMap[type]}
        <div>
          <div className="text-sm">{finding.message}</div>
          {finding.section && <Badge variant="outline" className="mt-1 text-xs">{finding.section}</Badge>}
        </div>
      </div>
    </div>
  );
}

function ActionableRecCard({ recommendation, resumeId, navigate }) {
  const priorityColors = {
    high: "bg-red-50 border-red-200 text-red-800",
    medium: "bg-yellow-50 border-yellow-200 text-yellow-800",
    low: "bg-blue-50 border-blue-200 text-blue-800",
  };
  const priorityIcon = {
    high: <XCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />,
    medium: <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5 shrink-0" />,
    low: <Lightbulb className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />,
  };

  const handleFix = () => {
    navigate(recommendation.navigation_url || `/resume-studio?id=${resumeId}`);
  };

  return (
    <div className={`p-3 rounded-lg border ${priorityColors[recommendation.priority] || "bg-gray-50 border-gray-200"}`}>
      <div className="flex items-start gap-2">
        {priorityIcon[recommendation.priority] || <Lightbulb className="w-4 h-4 text-gray-500 mt-0.5 shrink-0" />}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant={recommendation.priority === "high" ? "destructive" : "secondary"} className="text-[10px] uppercase">{recommendation.priority}</Badge>
            {recommendation.category && <Badge variant="outline" className="text-[10px] capitalize">{recommendation.category.replace(/_/g, " ")}</Badge>}
          </div>
          <div className="text-sm font-medium">{recommendation.description}</div>
          {recommendation.evidence && <div className="text-xs text-muted-foreground mt-1">{recommendation.evidence}</div>}
          {recommendation.recommended_fix && (
            <div className="flex items-center gap-1 text-xs text-primary mt-2">
              <Wrench className="w-3 h-3" />
              <span>{recommendation.recommended_fix}</span>
            </div>
          )}
          {recommendation.navigation_url && (
            <Button variant="link" size="sm" className="h-auto p-0 mt-2 text-xs gap-1" onClick={handleFix}>
              Fix this section <ArrowRight className="w-3 h-3" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function SkillBadge({ skill }) {
  return (
    <Badge variant="secondary" className="text-xs">
      {skill.name}
      {skill.normalized && <span className="ml-1 text-[10px] text-muted-foreground">({skill.original_name})</span>}
    </Badge>
  );
}

function CategorizedSkillsSection({ categorized }) {
  const categories = [
    { key: "programming_languages", label: "Programming Languages" },
    { key: "frameworks", label: "Frameworks" },
    { key: "databases", label: "Databases" },
    { key: "cloud_technologies", label: "Cloud Technologies" },
    { key: "tools", label: "Tools" },
    { key: "technologies", label: "Technologies" },
    { key: "soft_skills", label: "Soft Skills" },
  ];

  return (
    <div className="space-y-3">
      {categories.map(({ key, label }) => {
        const skills = categorized?.[key];
        if (!skills || skills.length === 0) return null;
        return (
          <div key={key}>
            <div className="text-sm font-medium mb-1.5">{label}</div>
            <div className="flex flex-wrap gap-1.5">
              {skills.map((skill, i) => <SkillBadge key={`${skill.name}-${i}`} skill={skill} />)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ATSComponentCard({ name, score, maxScore = 100, issues = [], strengths = [] }) {
  return (
    <div className="p-3 rounded-lg border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{name}</span>
        <span className="text-sm font-bold">{score}/{maxScore}</span>
      </div>
      <Progress value={score} className="h-1.5" />
      {issues.length > 0 && (
        <div className="mt-2 space-y-1">
          {issues.map((issue, i) => <div key={i} className="flex items-start gap-1.5 text-xs text-red-600"><XCircle className="w-3 h-3 mt-0.5 shrink-0" />{issue}</div>)}
        </div>
      )}
      {strengths.length > 0 && (
        <div className="mt-2 space-y-1">
          {strengths.map((s, i) => <div key={i} className="flex items-start gap-1.5 text-xs text-green-600"><CheckCircle2 className="w-3 h-3 mt-0.5 shrink-0" />{s}</div>)}
        </div>
      )}
    </div>
  );
}

function DeepAnalysisSection({ deepAnalysis }) {
  if (!deepAnalysis || deepAnalysis.status !== "success" || !deepAnalysis.ai_analysis) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          <Brain className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">AI deep analysis not available.</p>
          <p className="text-xs mt-1">Run analysis with AI enabled to get deeper insights.</p>
        </CardContent>
      </Card>
    );
  }

  const ai = deepAnalysis.ai_analysis;
  const dimensions = [
    { key: "content_quality", label: "Content Quality", data: ai.content_quality },
    { key: "summary_quality", label: "Summary Quality", data: ai.summary_quality },
    { key: "achievement_impact", label: "Achievement Impact", data: ai.achievement_impact },
    { key: "experience_relevance", label: "Experience Relevance", data: ai.experience_relevance },
  ];

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">{ai.overall_assessment}</p>

      <div className="grid gap-3 sm:grid-cols-2">
        {dimensions.filter(d => d.data).map((dim) => (
          <Card key={dim.key}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">{dim.label}</span>
                <ScoreBadge score={dim.data.score} />
              </div>
              <p className="text-xs text-muted-foreground mb-2">{dim.data.analysis}</p>
              {dim.data.strengths?.length > 0 && (
                <div className="mb-2">
                  <div className="text-xs font-medium text-green-600 mb-1">Strengths</div>
                  {dim.data.strengths.map((s, i) => <div key={i} className="text-xs text-muted-foreground flex items-start gap-1"><CheckCircle2 className="w-3 h-3 text-green-500 mt-0.5 shrink-0" />{s}</div>)}
                </div>
              )}
              {dim.data.issues?.length > 0 && (
                <div>
                  <div className="text-xs font-medium text-red-600 mb-1">Issues</div>
                  {dim.data.issues.map((s, i) => <div key={i} className="text-xs text-muted-foreground flex items-start gap-1"><XCircle className="w-3 h-3 text-red-500 mt-0.5 shrink-0" />{s}</div>)}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <ExpandableSection title="AI Skill Suggestions">
        {ai.skill_suggestions?.current_strengths?.length > 0 && (
          <div className="mb-3">
            <div className="text-sm font-medium text-green-600 mb-1">Current Strengths</div>
            <div className="flex flex-wrap gap-1.5">
              {ai.skill_suggestions.current_strengths.map((s, i) => <Badge key={i} variant="secondary">{s}</Badge>)}
            </div>
          </div>
        )}
        {ai.skill_suggestions?.gaps?.length > 0 && (
          <div className="mb-3">
            <div className="text-sm font-medium text-red-600 mb-1">Skill Gaps</div>
            <div className="flex flex-wrap gap-1.5">
              {ai.skill_suggestions.gaps.map((s, i) => <Badge key={i} variant="destructive">{s}</Badge>)}
            </div>
          </div>
        )}
        {ai.skill_suggestions?.recommended?.length > 0 && (
          <div>
            <div className="text-sm font-medium text-blue-600 mb-1">Recommended</div>
            <div className="space-y-1.5">
              {ai.skill_suggestions.recommended.map((r, i) => (
                <div key={i} className="text-sm"><span className="font-medium">{r.skill}</span><span className="text-muted-foreground"> — {r.reason}</span></div>
              ))}
            </div>
          </div>
        )}
      </ExpandableSection>

      <ExpandableSection title="AI Recommendations">
        <div className="space-y-2">
          {ai.recommendations?.map((rec, i) => (
            <div key={i} className="p-3 rounded-lg border">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant={rec.priority === "high" ? "destructive" : rec.priority === "medium" ? "secondary" : "outline"} className="text-[10px]">{rec.priority}</Badge>
                <Badge variant="outline" className="text-[10px]">{rec.category}</Badge>
              </div>
              <p className="text-sm font-medium">{rec.action}</p>
              {rec.details && <p className="text-xs text-muted-foreground mt-0.5">{rec.details}</p>}
            </div>
          ))}
        </div>
      </ExpandableSection>

      {deepAnalysis.hybrid && (
        <ExpandableSection title="Combined Analysis">
          {deepAnalysis.hybrid.overall_assessment && (
            <p className="text-sm text-muted-foreground mb-3">{deepAnalysis.hybrid.overall_assessment}</p>
          )}
          {deepAnalysis.hybrid.strengths?.length > 0 && (
            <div className="mb-3">
              <div className="text-sm font-medium text-green-600 mb-2">Strengths</div>
              <div className="space-y-2">
                {deepAnalysis.hybrid.strengths.map((s, i) => <StrengthItem key={i} item={s} />)}
              </div>
            </div>
          )}
          {deepAnalysis.hybrid.weaknesses?.length > 0 && (
            <div>
              <div className="text-sm font-medium text-red-600 mb-2">Weaknesses</div>
              <div className="space-y-2">
                {deepAnalysis.hybrid.weaknesses.map((w, i) => <WeaknessItem key={i} item={w} />)}
              </div>
            </div>
          )}
        </ExpandableSection>
      )}
    </div>
  );
}

function Sparkline({ values }) {
  const width = 220;
  const height = 44;
  if (!values || values.length < 2) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = values
    .map((value, i) => {
      const x = (i / (values.length - 1)) * width;
      const y = height - 4 - ((value - min) / range) * (height - 8);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const lastX = width;
  const lastY = height - 4 - ((values[values.length - 1] - min) / range) * (height - 8);

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible" aria-hidden>
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={lastX} cy={lastY} r="3" fill="currentColor" />
    </svg>
  );
}

function DiffFact({ diff }) {
  const facts = [];

  (diff.skills_added || []).forEach((skill) =>
    facts.push({
      key: `added-${skill}`,
      icon: "+",
      tone: "text-green-600",
      text: `Added skill: ${skill}`,
    })
  );

  (diff.skills_removed || []).forEach((skill) =>
    facts.push({
      key: `removed-${skill}`,
      icon: "−",
      tone: "text-red-600",
      text: `Removed skill: ${skill}`,
    })
  );

  if (typeof diff.summary_changed === "boolean") {
    const delta = diff.summary_word_delta || 0;
    facts.push({
      key: "summary",
      icon: diff.summary_changed ? "~" : "=",
      tone: diff.summary_changed ? "text-amber-600" : "text-slate-400",
      text: diff.summary_changed
        ? `Summary text changed${delta !== 0 ? ` (${delta > 0 ? "+" : ""}${delta} words)` : ""}`
        : "Summary text unchanged",
    });
  }

  const covered = diff.jd_keywords_now_covered || [];
  if (covered.length > 0) {
    facts.push({
      key: "jd",
      icon: "+",
      tone: "text-blue-600",
      text: `Now covers: ${covered.join(", ")}`,
    });
  }

  if (facts.length === 0) {
    return <p className="text-sm text-slate-500">No content changes detected.</p>;
  }

  return (
    <ul className="space-y-1.5">
      {facts.map((fact) => (
        <li key={fact.key} className="flex items-start gap-2 text-sm">
          <span className={`w-4 shrink-0 font-bold ${fact.tone}`}>{fact.icon}</span>
          <span>{fact.text}</span>
        </li>
      ))}
    </ul>
  );
}

function ScoreTrendCard({ resumeId }) {
  const { data, isLoading } = useQuery({
    queryKey: ["score-history", resumeId],
    queryFn: () => getScoreHistory(resumeId, "ats_score", 20),
    enabled: Boolean(resumeId),
    staleTime: 60 * 1000,
  });

  const snapshots = data?.data?.snapshots || [];

  const diffFrom = snapshots.length >= 2 ? snapshots[snapshots.length - 2]?.id : null;
  const diffTo = snapshots.length >= 2 ? snapshots[snapshots.length - 1]?.id : null;

  const diffQuery = useQuery({
    queryKey: ["score-history-diff", resumeId, diffFrom, diffTo],
    queryFn: () => getScoreHistoryDiff(resumeId, diffFrom, diffTo),
    enabled: Boolean(resumeId && diffFrom && diffTo),
    retry: false,
    staleTime: 60 * 1000,
  });

  if (!resumeId || isLoading || !data?.success) return null;

  const { count, latest, previous, change } = data.data || {};

  const changeTone = change >= 0 ? "text-green-600" : "text-red-600";

  return (
    <div className="rounded-lg border bg-slate-50/70 px-4 py-3 space-y-3">
      <div className="flex items-center gap-3">
        <TrendingUp className="w-5 h-5 text-blue-600 shrink-0" />
        {count >= 2 ? (
          <p className="text-sm text-slate-700">
            ATS score went from <span className="font-semibold">{previous}</span>{" "}
            <ArrowRight className="inline w-4 h-4 text-slate-400" />{" "}
            <span className="font-semibold">{latest}</span>
            <span className={`ml-1.5 font-semibold ${changeTone}`}>
              ({change >= 0 ? "+" : ""}{change})
            </span>{" "}
            after your last edit.
          </p>
        ) : (
          <p className="text-sm text-slate-600">
            Keep editing to see your ATS score trend over time.
          </p>
        )}
      </div>

      {count >= 2 && (
        <div className="flex items-center gap-4">
          <div className="text-blue-600">
            <Sparkline values={snapshots.map((s) => s.value)} />
          </div>
          <div className="text-xs text-slate-500 tabular-nums shrink-0">
            {snapshots.length} snapshot{snapshots.length === 1 ? "" : "s"}
          </div>
        </div>
      )}

      {count >= 2 && (
        <div className="border-t pt-3">
          <p className="text-sm font-semibold text-slate-800">
            ATS Score <span className={changeTone}>{change >= 0 ? "+" : ""}{change}</span>
          </p>
          <p className="text-xs text-slate-500 mt-0.5 mb-2">What changed</p>

          {diffQuery.isLoading && (
            <Skeleton className="h-16 w-full" />
          )}

          {!diffQuery.isLoading && diffQuery.isError && (
            <p className="text-sm text-slate-500">
              Content wasn&apos;t captured for these earlier snapshots — run a fresh analysis to enable diffs.
            </p>
          )}

          {!diffQuery.isLoading && !diffQuery.isError && diffQuery.data?.success && (
            <DiffFact diff={diffQuery.data.data} />
          )}
        </div>
      )}
    </div>
  );
}

function AnalysisResults({ analysis, resumeId, navigate, isStale = false, isCached = false }) {
  const det = analysis.deterministic;
  const quality = analysis.quality_report;
  const ats = analysis.ats_analysis;
  const skills = analysis.skill_analysis;
  const sw = analysis.strengths_weaknesses;
  const deep = analysis.deep_analysis;
  const recommendations = analysis.recommendations || [];
  const highPriorityCount = analysis.high_priority_recommendations || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <p className="text-sm text-muted-foreground">Analyzed at {new Date(analysis.analyzed_at).toLocaleString()}</p>
          {isStale && (
            <Badge variant="destructive" className="text-[10px] gap-1">
              <AlertTriangle className="w-3 h-3" />
              Stale
            </Badge>
          )}
          {isCached && !isStale && (
            <Badge variant="secondary" className="text-[10px] gap-1">
              <Database className="w-3 h-3" />
              Cached
            </Badge>
          )}
          {analysis._analysis_id && (
            <Badge variant="outline" className="text-[10px]">
              #{analysis._analysis_id}
            </Badge>
          )}
        </div>
        <ScoreTooltip description="A weighted average of completeness, action verbs, quantified metrics, bullet quality, section balance, and summary quality.">
          <ScoreBadge score={det.overall_quality_score.overall_score} size="lg" />
        </ScoreTooltip>
      </div>

      <ScoreTrendCard resumeId={resumeId} />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <ScoreCard icon={FileText} label="Resume Quality" score={quality?.overall_score || det.overall_quality_score.overall_score} color="primary" tooltip="A weighted average of completeness, action verbs, quantified metrics, bullet quality, section balance, and summary quality." />
        <ScoreCard icon={CheckCircle2} label="ATS Score" score={ats?.overall_ats_score || 0} color="blue" tooltip="Weighted average of 5 deterministic checks: structure (25%), keyword coverage (20%), action verbs (20%), quantified impact (20%), and contact info (15%)." />
        <ScoreCard icon={BarChart3} label="Completeness" score={det.completeness.overall_completeness_score} color="emerald" />
        <ScoreCard icon={TrendingUp} label="Skills" sublabel={`${skills?.skill_count || 0} skills found`} score={skills ? Math.min(100, skills.skill_count * 10) : 0} color="purple" />
      </div>

      {recommendations.length > 0 && (
        <Card className="border-orange-200 bg-orange-50/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Wrench className="w-5 h-5 text-orange-600" />
              <div>
                <span className="font-semibold text-orange-800">{recommendations.length} Actionable Recommendations</span>
                {highPriorityCount > 0 && (
                  <span className="ml-2 text-sm text-orange-600">({highPriorityCount} high priority)</span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="recommendations" className="relative">
            Recommendations
            {highPriorityCount > 0 && (
              <span className="ml-1 inline-flex items-center justify-center w-5 h-5 text-[10px] font-bold text-white bg-red-500 rounded-full">
                {highPriorityCount}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="strengths">Strengths & Weaknesses</TabsTrigger>
          <TabsTrigger value="ats">ATS Analysis</TabsTrigger>
          <TabsTrigger value="quality">Quality Report</TabsTrigger>
          <TabsTrigger value="skills">Skills</TabsTrigger>
          {deep && <TabsTrigger value="deep">Deep Analysis</TabsTrigger>}
        </TabsList>

        <TabsContent value="overview" className="space-y-4 mt-4">
          <ExpandableSection title="Completeness" defaultOpen>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Overall Completeness</span>
                  <span className="font-medium">{det.completeness.overall_completeness_score}%</span>
                </div>
                <Progress value={det.completeness.overall_completeness_score} />
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {Object.entries(det.completeness.section_presence || {}).map(([section, present]) => (
                  <div key={section} className="flex items-center gap-2 text-sm">
                    {present ? <CheckCircle2 className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-red-500" />}
                    <span className="capitalize">{section.replace(/_/g, " ")}</span>
                  </div>
                ))}
              </div>
            </div>
          </ExpandableSection>

          <ExpandableSection title="Action Verbs">
            <div className="space-y-2">
              <div className="text-sm">
                <span className="font-medium">{det.action_verbs?.entries_with_verbs || 0}</span>{" "}
                of {det.action_verbs?.total_entries || 0} entries use action verbs
              </div>
              {det.action_verbs?.all_verbs?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {det.action_verbs.all_verbs.map((v, i) => <Badge key={i} variant="secondary">{v}</Badge>)}
                </div>
              )}
            </div>
          </ExpandableSection>

          <ExpandableSection title="Metrics & Quantification">
            <div className="text-sm space-y-1">
              <div>Quantifiable metrics: <span className="font-medium">{det.metrics?.total_quantifiable || 0}</span></div>
              {det.metrics?.percentages?.length > 0 && <div>Percentages: {det.metrics.percentages.join(", ")}</div>}
              {det.metrics?.numbers?.length > 0 && <div>Numbers: {det.metrics.numbers.join(", ")}</div>}
              {det.metrics?.currency_values?.length > 0 && <div>Currency: {det.metrics.currency_values.join(", ")}</div>}
            </div>
          </ExpandableSection>

          <ExpandableSection title="Section Balance">
            <div className="space-y-2">
              <div className="flex justify-between text-sm mb-1">
                <span>Balance Score</span>
                <span className="font-medium">{det.section_balance?.balance_score || 0}/100</span>
              </div>
              <Progress value={det.section_balance?.balance_score || 0} />
              {det.section_balance?.balance_issues?.length > 0 && (
                <div className="space-y-1 mt-2">
                  {det.section_balance.balance_issues.map((issue, i) => (
                    <div key={i} className="flex items-start gap-1.5 text-xs text-yellow-600"><AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />{issue}</div>
                  ))}
                </div>
              )}
            </div>
          </ExpandableSection>
        </TabsContent>

        {recommendations.length > 0 && (
          <TabsContent value="recommendations" className="space-y-4 mt-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {recommendations.length} recommendation{recommendations.length !== 1 ? "s" : ""} to improve your resume
              </p>
              <Badge variant="outline" className="text-xs">
                {highPriorityCount} high priority
              </Badge>
            </div>
            <div className="space-y-2">
              {recommendations.map((rec, i) => (
                <ActionableRecCard key={rec.id || i} recommendation={rec} resumeId={resumeId} navigate={navigate} />
              ))}
            </div>
          </TabsContent>
        )}

        <TabsContent value="strengths" className="space-y-4 mt-4">
          {sw ? (
            <>
              <div className="flex gap-4 mb-3">
                <div className="flex items-center gap-2"><Award className="w-4 h-4 text-green-600" /><span className="text-sm font-medium">{sw.strength_count} Strengths</span></div>
                <div className="flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-red-600" /><span className="text-sm font-medium">{sw.weakness_count} Weaknesses</span></div>
              </div>
              {sw.strengths?.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-green-600 mb-2">Strengths</h3>
                  <div className="space-y-2">
                    {sw.strengths.map((s, i) => <StrengthItem key={i} item={s} />)}
                  </div>
                </div>
              )}
              {sw.weaknesses?.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-red-600 mb-2">Weaknesses</h3>
                  <div className="space-y-2">
                    {sw.weaknesses.map((w, i) => <WeaknessItem key={i} item={w} />)}
                  </div>
                </div>
              )}
              {sw.top_priorities?.length > 0 && (
                <Card>
                  <CardContent className="p-4">
                    <div className="text-sm font-medium mb-2">Top Priorities</div>
                    <ol className="list-decimal list-inside space-y-1">
                      {sw.top_priorities.map((p, i) => <li key={i} className="text-sm text-muted-foreground">{p}</li>)}
                    </ol>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              <Target className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No strengths/weaknesses data available.</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="ats" className="space-y-4 mt-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-lg font-bold">Overall ATS Score</span>
                <ScoreTooltip description="Weighted average of 5 deterministic checks: structure (25%), keyword coverage (20%), action verbs (20%), quantified impact (20%), and contact info (15%).">
                  <ScoreBadge score={ats?.overall_ats_score || 0} />
                </ScoreTooltip>
              </div>
              <Progress value={ats?.overall_ats_score || 0} className="h-2" />
              {ats?.risk_level && (
                <Badge variant={ats.risk_level === "high" ? "destructive" : ats.risk_level === "medium" ? "secondary" : "outline"} className="mt-2">
                  {ats.risk_level} risk
                </Badge>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-3 sm:grid-cols-2">
            {ats?.component_details && Object.entries(ats.component_details).map(([key, comp]) => (
              <ATSComponentCard
                key={key}
                name={key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                score={comp.score}
                maxScore={comp.max_score}
                issues={comp.issues}
                strengths={comp.strengths}
              />
            ))}
          </div>

          {ats?.recommendations?.length > 0 && (
            <ExpandableSection title="ATS Recommendations">
              <ul className="space-y-1.5 list-disc list-inside">
                {ats.recommendations.map((r, i) => <li key={i} className="text-sm text-muted-foreground">{r}</li>)}
              </ul>
            </ExpandableSection>
          )}
        </TabsContent>

        <TabsContent value="quality" className="space-y-4 mt-4">
          {quality ? (
            <>
              <div className="flex flex-wrap gap-3 mb-3">
                <Badge variant="destructive">{quality.total_issues} Issues</Badge>
                <Badge variant="secondary">{quality.total_warnings} Warnings</Badge>
                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">{quality.total_strengths} Strengths</Badge>
              </div>

              {quality.resume_length && (
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Resume Length</span>
                      <Badge variant="outline">{quality.resume_length.grade || `${quality.resume_length.total_words} words`}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{quality.resume_length.recommendation}</p>
                  </CardContent>
                </Card>
              )}

              {quality.issues?.length > 0 && (
                <ExpandableSection title={`Issues (${quality.issues.length})`}>
                  <div className="space-y-2">
                    {quality.issues.map((f, i) => <QualityFindingItem key={i} finding={f} type="issue" />)}
                  </div>
                </ExpandableSection>
              )}

              {quality.warnings?.length > 0 && (
                <ExpandableSection title={`Warnings (${quality.warnings.length})`}>
                  <div className="space-y-2">
                    {quality.warnings.map((f, i) => <QualityFindingItem key={i} finding={f} type="warning" />)}
                  </div>
                </ExpandableSection>
              )}

              {quality.strengths?.length > 0 && (
                <ExpandableSection title={`Strengths (${quality.strengths.length})`}>
                  <div className="space-y-2">
                    {quality.strengths.map((f, i) => <QualityFindingItem key={i} finding={f} type="strength" />)}
                  </div>
                </ExpandableSection>
              )}
            </>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Quality report not available.</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="skills" className="space-y-4 mt-4">
          {skills ? (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <Card><CardContent className="p-3 text-center"><div className="text-2xl font-bold">{skills.skill_count}</div><div className="text-xs text-muted-foreground">Total Skills</div></CardContent></Card>
                <Card><CardContent className="p-3 text-center"><div className="text-2xl font-bold">{skills.explicit_count}</div><div className="text-xs text-muted-foreground">Explicit</div></CardContent></Card>
                <Card><CardContent className="p-3 text-center"><div className="text-2xl font-bold">{skills.implicit_count}</div><div className="text-xs text-muted-foreground">Implicit</div></CardContent></Card>
                <Card><CardContent className="p-3 text-center"><div className="text-2xl font-bold">{skills.certification_count}</div><div className="text-xs text-muted-foreground">Cert-derived</div></CardContent></Card>
              </div>
              <CategorizedSkillsSection categorized={skills.categorized} />
              {skills.uncategorized?.length > 0 && (
                <ExpandableSection title={`Uncategorized (${skills.uncategorized.length})`}>
                  <div className="flex flex-wrap gap-1.5">
                    {skills.uncategorized.map((s, i) => <Badge key={i} variant="outline">{s}</Badge>)}
                  </div>
                </ExpandableSection>
              )}
            </>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Skill analysis not available.</p>
            </div>
          )}
        </TabsContent>

        {deep && (
          <TabsContent value="deep" className="space-y-4 mt-4">
            <DeepAnalysisSection deepAnalysis={deep} />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}

function ResumeSelector({ resumes, selectedId, onSelect, isLoading }) {
  if (isLoading) {
    return <Skeleton className="h-10 w-full" />;
  }

  return (
    <select
      value={selectedId || ""}
      onChange={(e) => onSelect(e.target.value ? Number(e.target.value) : null)}
      className="w-full h-10 rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <option value="">Select a resume to analyze...</option>
      {resumes?.map((r) => (
        <option key={r.id} value={r.id}>{r.name}</option>
      ))}
    </select>
  );
}

export default function ResumeAnalysis() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { resumeData, setResumeData } = useResumeContext();
  const resumeIdFromUrl = searchParams.get("id") ? Number(searchParams.get("id")) : null;

  const [selectedResumeId, setSelectedResumeId] = useState(resumeIdFromUrl);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasRun, setHasRun] = useState(false);
  const [isStale, setIsStale] = useState(false);
  const [isCached, setIsCached] = useState(false);
  const [loadingCached, setLoadingCached] = useState(false);
  const [analysisJustCompleted, setAnalysisJustCompleted] = useState(false);

  const { data: resumes, isLoading: resumesLoading } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => resumeApi.listResumes(false),
  });

  const { data: selectedResume } = useQuery({
    queryKey: ["resume", selectedResumeId],
    queryFn: () => resumeApi.loadResume(selectedResumeId),
    enabled: !!selectedResumeId,
  });

  useEffect(() => {
    if (selectedResume) {
      setResumeData(selectedResume);
    }
  }, [selectedResume, setResumeData]);

  // Check for cached analysis when resume is selected
  useEffect(() => {
    if (!selectedResumeId) return;
    let cancelled = false;

    async function checkCache() {
      setLoadingCached(true);
      try {
        const result = await getCachedAnalysis(selectedResumeId);
        if (cancelled) return;
        if (result.success && result.data.cached && result.data.analysis) {
          setAnalysisResult(result.data.analysis.analysis_json);
          setIsStale(result.data.stale);
          setIsCached(true);
          setHasRun(true);
        }
      } catch {
        // Cache miss is fine, user can run fresh analysis
      } finally {
        if (!cancelled) setLoadingCached(false);
      }
    }

    checkCache();
    return () => { cancelled = true; };
  }, [selectedResumeId]);

  const handleAnalyze = useCallback(async () => {
    if (!resumeData) return;
    setLoading(true);
    setError(null);
    setIsCached(false);
    setIsStale(false);
    try {
      const result = await analyzeResume(resumeData, false, resumeIdFromUrl);
      if (result.success) {
        setAnalysisResult(result.data);
        setHasRun(true);
        setAnalysisJustCompleted(true);
      } else {
        setError(result.error || "Analysis failed");
      }
    } catch (err) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  }, [resumeData, resumeIdFromUrl]);

  const handleReAnalyze = useCallback(async () => {
    if (!selectedResumeId) return;
    setLoading(true);
    setError(null);
    setIsCached(false);
    setIsStale(false);
    try {
      const result = await reAnalyzeResume(selectedResumeId, false);
      if (result.success) {
        setAnalysisResult(result.data);
        setHasRun(true);
        setAnalysisJustCompleted(true);
      } else {
        setError(result.error || "Re-analysis failed");
      }
    } catch (err) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  }, [selectedResumeId]);

  const handleRetry = useCallback(() => {
    handleAnalyze();
  }, [handleAnalyze]);

  const handleResumeSelect = (id) => {
    setSelectedResumeId(id);
    setAnalysisResult(null);
    setError(null);
    setHasRun(false);
    setIsStale(false);
    setIsCached(false);
    setAnalysisJustCompleted(false);
    if (id) {
      setSearchParams({ id: String(id) });
    } else {
      setSearchParams({});
    }
  };

  const showSelector = !selectedResumeId && resumes?.length > 0;
  const showNoResumes = !selectedResumeId && resumes?.length === 0 && !resumesLoading;
  const showAnalyzeReady = selectedResumeId && resumeData && !loadingCached;
  const showResults = hasRun && analysisResult && !loading;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Resume Analysis</h1>
          <p className="text-sm text-muted-foreground">Get comprehensive feedback on your resume</p>
        </div>
        <div className="flex gap-2">
          {selectedResumeId && (
            <Button variant="outline" size="sm" onClick={() => navigate(`/resume-studio?id=${selectedResumeId}`)}>
              <FileText className="w-4 h-4 mr-1" />
              Edit Resume
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={() => { setSelectedResumeId(null); setAnalysisResult(null); setError(null); setHasRun(false); setSearchParams({}); }}>
            New Analysis
          </Button>
        </div>
      </div>

      <Separator />

      {showSelector && (
        <Card>
          <CardHeader>
            <CardTitle>Select Resume</CardTitle>
            <CardDescription>Choose a resume to analyze</CardDescription>
          </CardHeader>
          <CardContent>
            <ResumeSelector
              resumes={resumes}
              selectedId={selectedResumeId}
              onSelect={handleResumeSelect}
              isLoading={resumesLoading}
            />
          </CardContent>
        </Card>
      )}

      {showNoResumes && (
        <Card>
          <CardContent className="p-8 text-center">
            <FileText className="w-12 h-12 mx-auto mb-3 text-muted-foreground/50" />
            <h3 className="text-lg font-medium mb-1">No Resumes Yet</h3>
            <p className="text-sm text-muted-foreground mb-4">Create a resume in the studio first.</p>
            <Button onClick={() => navigate("/resume-studio")}>Go to Resume Studio</Button>
          </CardContent>
        </Card>
      )}

      {loadingCached && selectedResumeId && !hasRun && (
        <Card>
          <CardContent className="p-8 space-y-3">
            <Skeleton className="h-4 w-40 mx-auto" />
            <Skeleton className="h-4 w-56 mx-auto" />
          </CardContent>
        </Card>
      )}

      {showAnalyzeReady && !hasRun && !loading && !loadingCached && (
        <Card>
          <CardHeader>
            <CardTitle>Ready to Analyze</CardTitle>
            <CardDescription>
              {resumeData?.personal?.firstName || resumeData?.personal?.lastName
                ? `Analyzing resume for ${resumeData.personal.firstName || ""} ${resumeData.personal.lastName || ""}`.trim()
                : "Click analyze to get comprehensive feedback on your resume."}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center py-4">
            <Button size="lg" onClick={handleAnalyze} className="gap-2">
              <Sparkles className="w-5 h-5" />
              Analyze Resume
            </Button>
          </CardContent>
        </Card>
      )}

      {loading && (
        <Card>
          <CardContent className="p-8">
            <AILoading message="Analyzing your resume..." />
            <div className="space-y-3 mt-4">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <div className="grid grid-cols-2 gap-3 mt-4">
                <Skeleton className="h-24" />
                <Skeleton className="h-24" />
              </div>
              <Skeleton className="h-32" />
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card className="border-red-200">
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <XCircle className="w-6 h-6 text-red-500 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">Analysis Failed</h3>
                <p className="text-sm text-red-600 mt-1">{error}</p>
                <Button variant="outline" size="sm" onClick={handleRetry} className="mt-3 gap-1">
                  <RefreshCw className="w-4 h-4" />
                  Retry
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {isStale && showResults && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <span className="text-sm font-medium text-amber-800">Analysis is stale — resume has been updated since this analysis</span>
            </div>
            <Button size="sm" variant="outline" onClick={handleReAnalyze} disabled={loading} className="gap-1">
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Re-analyze
            </Button>
          </CardContent>
        </Card>
      )}

      {analysisJustCompleted && showResults && (
        <SuccessBanner onDismiss={() => setAnalysisJustCompleted(false)}>
          Analysis complete — your ATS score, quality report, and recommendations
          are ready below.
        </SuccessBanner>
      )}

      {showResults && (
        <AnalysisResults analysis={analysisResult} resumeId={resumeIdFromUrl} navigate={navigate} isStale={isStale} isCached={isCached} />
      )}

      {!showSelector && !showAnalyzeReady && !loading && !hasRun && !showNoResumes && selectedResumeId && !resumeData && (
        <Card>
          <CardContent className="p-8 space-y-3">
            <Skeleton className="h-4 w-40 mx-auto" />
            <Skeleton className="h-4 w-64 mx-auto" />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
