import { Sparkles, Loader2 } from "lucide-react";

import useAI from "@/hooks/useAI";

import { suggestSkills as suggestSkillsAI } from "@/services/aiService";
import SectionCard from "@/components/common/SectionCard";
import SectionHeader from "@/components/common/SectionHeader";
import AddItemButton from "@/components/common/AddItemButton";
import RemoveItemButton from "@/components/common/RemoveItemButton";
import InputField from "@/components/common/InputField";

import { useResumeContext } from "@/resume/context/useResumeContext";

function SkillCard({ skill, index, removable, onRemove, updateArrayItem }) {
  return (
    <SectionCard>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h4 className="font-semibold">Skill {index + 1}</h4>
          <p className="text-xs text-muted-foreground mt-1">
            Add the skill details below.
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
          label="Skill Name"
          id={`skills-${index}-name`}
          value={skill.name || ""}
          onChange={(value) =>
            updateArrayItem("skills", index, {
              ...skill,
              name: value,
            })
          }
          placeholder="e.g., React"
        />

        <InputField
          label="Category"
          id={`skills-${index}-category`}
          value={skill.category || ""}
          onChange={(value) =>
            updateArrayItem("skills", index, {
              ...skill,
              category: value,
            })
          }
          placeholder="e.g., Frontend (optional)"
        />
      </div>
    </SectionCard>
  );
}

export default function Skills() {
  const {
    resumeData,
    addItem,
    removeItem,
    updateArrayItem,
  } = useResumeContext();

  const { loading, execute } = useAI();

  const skills = resumeData.skills ?? [];
  const showRemove = skills.length > 1;

  async function handleSuggestSkills() {
    const result = await execute(suggestSkillsAI, resumeData.skills || []);

    if (Array.isArray(result) && result.length > 0) {
      const currentSkills = resumeData.skills || [];
      const existingNames = currentSkills
        .map((s) => s.name?.toLowerCase())
        .filter(Boolean);

      const newSkills = result.filter(
        (s) => !existingNames.includes(s.name?.toLowerCase())
      );

      newSkills.forEach((skill) => {
        addItem("skills", skill);
      });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <SectionHeader title="Skills" />

        <button
          onClick={handleSuggestSkills}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg border hover:bg-muted disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4" />
          )}
          <span>Suggest Skills</span>
        </button>
      </div>

      <div className="space-y-4">
        {skills.map((skill, index) => (
          <SkillCard
            key={skill.id || index}
            skill={skill}
            index={index}
            removable={showRemove}
            onRemove={() => removeItem("skills", index)}
            updateArrayItem={updateArrayItem}
          />
        ))}
      </div>

      <div className="flex justify-end">
        <AddItemButton onClick={() => addItem("skills")}>
          Add Skill
        </AddItemButton>
      </div>
    </div>
  );
}

