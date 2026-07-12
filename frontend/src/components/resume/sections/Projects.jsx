    
import { Sparkles, Loader2 } from "lucide-react";

import useAI from "@/hooks/useAI";
import { improveProject as improveProjectAI } from "@/services/aiService";

import SectionCard from "@/components/common/SectionCard";
import SectionHeader from "@/components/common/SectionHeader";
import AddItemButton from "@/components/common/AddItemButton";
import RemoveItemButton from "@/components/common/RemoveItemButton";
import InputField from "@/components/common/InputField";
import TextareaField from "@/components/common/TextareaField";

import { useResumeContext } from "@/context/useResumeContext";

function ProjectCard({
  project,
  index,
  removable,
  onRemove,
  updateArrayItem,
}) {
  const { loading, execute } = useAI();

  async function handleImprove() {
    if (!project.description?.trim()) {
  return;
}
    const result = await execute(
      improveProjectAI,
      project.description || ""
    );

    if (typeof result === "string" && result.trim()) {
      updateArrayItem("projects", index, {
        ...project,
        description: result,
      });
    }
  }

  return (
    <SectionCard>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h4 className="font-semibold">Project {index + 1}</h4>
          <p className="text-xs text-muted-foreground mt-1">
            Add the project details below.
          </p>
        </div>

        <RemoveItemButton
          onClick={onRemove}
          disabled={!removable}
          className="h-8 px-2"
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <InputField
          label="Project Title"
          id={`projects-${index}-title`}
          value={project.title || ""}
          onChange={(value) =>
            updateArrayItem("projects", index, {
              ...project,
              title: value,
            })
          }
          placeholder="e.g., Resume Studio"
        />

        <InputField
          label="Tech Stack"
          id={`projects-${index}-techStack`}
          value={project.techStack || ""}
          onChange={(value) =>
            updateArrayItem("projects", index, {
              ...project,
              techStack: value,
            })
          }
          placeholder="e.g., React, Node.js, PostgreSQL"
        />

        <InputField
          label="GitHub URL"
          id={`projects-${index}-github`}
          value={project.github || ""}
          onChange={(value) =>
            updateArrayItem("projects", index, {
              ...project,
              github: value,
            })
          }
          placeholder="https://github.com/username/repo"
        />

        <InputField
          label="Live Demo URL"
          id={`projects-${index}-liveDemo`}
          value={project.liveDemo || ""}
          onChange={(value) =>
            updateArrayItem("projects", index, {
              ...project,
              liveDemo: value,
            })
          }
          placeholder="https://yourapp.com"
        />
      </div>

      <div className="mt-4 space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">Description</label>

          <button
            onClick={handleImprove}
            disabled={loading || !project.description?.trim()}
            className="flex items-center gap-1.5 px-2 py-1 text-xs rounded-lg border hover:bg-muted disabled:opacity-50 transition-colors"
          >
            {loading ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Sparkles className="w-3 h-3" />
            )}
            <span>Improve</span>
          </button>
        </div>

        <TextareaField
          id={`projects-${index}-description`}
          value={project.description || ""}
          onChange={(value) =>
            updateArrayItem("projects", index, {
              ...project,
              description: value,
            })
          }
          placeholder="Write a short description of what you built and the impact."
          rows={4}
        />
      </div>
    </SectionCard>
  );
}

export default function Projects() {
  const {
    resumeData,
    addItem,
    removeItem,
    updateArrayItem,
  } = useResumeContext();

  const projects = resumeData.projects ?? [];
  const showRemove = projects.length > 1;

  return (
    <div className="space-y-4">
      <SectionHeader title="Projects" />

      <div className="space-y-4">
        {projects.map((project, index) => (
          <ProjectCard
            key={project.id || index}
            project={project}
            index={index}
            removable={showRemove}
            onRemove={() => removeItem("projects", index)}
            updateArrayItem={updateArrayItem}
          />
        ))}
      </div>

      <div className="flex justify-end">
        <AddItemButton onClick={() => addItem("projects")}>
          Add Project
        </AddItemButton>
      </div>
    </div>
  );
}

