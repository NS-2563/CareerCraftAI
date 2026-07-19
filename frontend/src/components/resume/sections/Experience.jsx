import { Sparkles, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

import AddItemButton from "@/components/common/AddItemButton";
import RemoveItemButton from "@/components/common/RemoveItemButton";
import SectionCard from "@/components/common/SectionCard";
import SectionHeader from "@/components/common/SectionHeader";

import { useResumeContext } from "@/resume/context/useResumeContext";
import useAI from "@/hooks/useAI";
import { improveExperience as improveExperienceAI } from "@/services/aiService";

const Label = ({ children, ...props }) => (
  <label {...props} className="text-sm font-medium">
    {children}
  </label>
);

function Checkbox({ id, checked, onCheckedChange }) {
  return (
    <input
      id={id}
      type="checkbox"
      checked={checked}
      onChange={(e) => onCheckedChange?.(e.target.checked)}
      className="h-4 w-4 rounded border"
    />
  );
}

function ExperienceCard({
  experience,
  index,
  removable,
  onRemove,
  updateArrayItem,
  useAIHook,
}) {
  const { loading, execute } = useAIHook;

  async function handleImprove() {
    if (!experience.description?.trim()) {
  return;
}
    const result = await execute(
      improveExperienceAI,
      experience.description
    );

    if (result) {
      updateArrayItem("experience", index, {
        ...experience,
        description: result,
      });
    }
  }

  return (
    <SectionCard>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h4 className="font-semibold">Experience {index + 1}</h4>
          <p className="text-xs text-muted-foreground mt-1">
            Add the role details below.
          </p>
        </div>

        <RemoveItemButton
          onClick={onRemove}
          disabled={!removable}
          className="h-8 px-2"
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label>Company</Label>
          <Input
            value={experience.company || ""}
            onChange={(e) =>
              updateArrayItem("experience", index, {
                ...experience,
                company: e.target.value,
              })
            }
          />
        </div>

        <div className="space-y-2">
          <Label>Position</Label>
          <Input
            value={experience.position || ""}
            onChange={(e) =>
              updateArrayItem("experience", index, {
                ...experience,
                position: e.target.value,
              })
            }
          />
        </div>

        <div className="space-y-2">
          <Label>Location</Label>
          <Input
            value={experience.location || ""}
            onChange={(e) =>
              updateArrayItem("experience", index, {
                ...experience,
                location: e.target.value,
              })
            }
          />
        </div>

        <div className="space-y-4 rounded-lg border p-3">
          <div className="flex items-center justify-between">
            <Label>Currently Working</Label>
            <Checkbox
              checked={!!experience.current}
              onCheckedChange={(checked) =>
                updateArrayItem("experience", index, {
                  ...experience,
                  current: Boolean(checked),
                  endDate: checked ? "" : experience.endDate,
                })
              }
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Start Date</Label>
              <Input
                type="month"
                value={experience.startDate || ""}
                onChange={(e) =>
                  updateArrayItem("experience", index, {
                    ...experience,
                    startDate: e.target.value,
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label>End Date</Label>
              <Input
                type="month"
                value={experience.endDate || ""}
                disabled={!!experience.current}
                onChange={(e) =>
                  updateArrayItem("experience", index, {
                    ...experience,
                    endDate: e.target.value,
                  })
                }
              />
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        <div className="flex items-center justify-between">
          <Label>Description</Label>

          <button
            onClick={handleImprove}
            disabled={loading || !experience.description?.trim()}
            className="flex items-center gap-1.5 px-2 py-1 text-xs rounded-lg border hover:bg-muted disabled:opacity-50 transition-colors"
          >
            {loading ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Sparkles className="w-3 h-3" />
            )}
            Improve
          </button>
        </div>

        <Textarea
          value={experience.description || ""}
          onChange={(e) =>
            updateArrayItem("experience", index, {
              ...experience,
              description: e.target.value,
            })
          }
          rows={4}
        />
      </div>
    </SectionCard>
  );
}

export default function Experience() {
  const { resumeData, addItem, removeItem, updateArrayItem } =
    useResumeContext();

  const experiences = resumeData.experience ?? [];
  const showRemove = experiences.length > 1;

  const aiHook = useAI();

  return (
    <div className="space-y-4">
      <SectionHeader title="Experience" />

      <div className="space-y-4">
        {experiences.map((experience, index) => (
          <ExperienceCard
            key={experience.id || index}
            experience={experience}
            index={index}
            removable={showRemove}
            onRemove={() => removeItem("experience", index)}
            updateArrayItem={updateArrayItem}
            useAIHook={aiHook}
          />
        ))}
      </div>

      <div className="flex justify-end">
        <AddItemButton onClick={() => addItem("experience")}>
          Add Experience
        </AddItemButton>
      </div>
    </div>
  );
}

