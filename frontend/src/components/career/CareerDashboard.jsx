import CareerSummary from "./CareerSummary";
import CareerPaths from "./CareerPaths";
import SkillGap from "./SkillGap";
import LearningRoadmap from "./LearningRoadmap";
import ActionPlan from "./ActionPlan";
import LearningResources from "./LearningResources";

export default function CareerDashboard({ report }) {
  if (!report) return null;

  return (
    <div className="space-y-8">
      <CareerSummary report={report} />

      <CareerPaths
        paths={report.career_paths}
      />

      <SkillGap
        skillGap={report.skill_gap}
      />

      <LearningRoadmap
        roadmap={report.roadmap}
      />

      <ActionPlan
        actionPlan={report.action_plan}
      />

      <LearningResources
        resources={report.resources}
      />
    </div>
  );
}