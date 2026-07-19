

import SectionCard from "@/components/common/SectionCard";

import SectionHeader from "@/components/common/SectionHeader";

import AddItemButton from "@/components/common/AddItemButton";
import RemoveItemButton from "@/components/common/RemoveItemButton";

import InputField from "@/components/common/InputField";
import DateField from "@/components/common/DateField";
import CheckboxField from "@/components/common/CheckboxField";
import TextareaField from "@/components/common/TextareaField";

import { useResumeContext } from "@/resume/context/useResumeContext";

function EducationCard({ education, index, removable, onRemove }) {
  const { updateArrayItem } = useResumeContext();

  return (
    <SectionCard>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h4 className="font-semibold">Education {index + 1}</h4>
          <p className="text-xs text-muted-foreground mt-1">Add the school details below.</p>
        </div>

        <RemoveItemButton onClick={onRemove} disabled={!removable} className="h-8 px-2" />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* Institution + Field of Study */}
        <div className="space-y-2">
          <InputField
            label="Institution"
            id={`education-${index}-institution`}
            value={education.institution}
            onChange={(value) =>
              updateArrayItem("education", index, {
                ...education,
                institution: value,
              })
            }
            placeholder="e.g., State University"
          />

          <InputField
            label="Field of Study"
            id={`education-${index}-fieldOfStudy`}
            value={education.fieldOfStudy}
            onChange={(value) =>
              updateArrayItem("education", index, { ...education, fieldOfStudy: value })
            }
            placeholder="e.g., Computer Science"
          />
        </div>

        {/* Degree + GPA (same row/column group as originally) */}
        <div className="space-y-2">
          <InputField
            label="Degree"
            id={`education-${index}-degree`}
            value={education.degree}
            onChange={(value) =>
              updateArrayItem("education", index, { ...education, degree: value })
            }
            placeholder="e.g., Bachelor of Science"
          />

          <InputField
            label="GPA"
            id={`education-${index}-gpa`}
            value={education.gpa}
            onChange={(value) =>
              updateArrayItem("education", index, { ...education, gpa: value })
            }
            placeholder="e.g., 3.8"
          />
        </div>

        {/* Location */}
        <div className="space-y-2">
          <InputField
            label="Location"
            id={`education-${index}-location`}
            value={education.location}
            onChange={(value) =>
              updateArrayItem("education", index, { ...education, location: value })
            }
            placeholder="e.g., Remote / Boston, MA"
          />
        </div>

        <div className="space-y-4 rounded-lg border p-3 md:space-y-2 md:col-span-1">
          <div className="flex items-center justify-between gap-3">
            <CheckboxField
              label="Currently Studying"
              checked={education.current}
              onCheckedChange={(checked) =>
                updateArrayItem("education", index, {
                  ...education,
                  current: Boolean(checked),
                  endDate: checked ? "" : education.endDate,
                })
              }
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-2">
              <DateField
                label="Start Date"
                id={`education-${index}-startDate`}
                value={education.startDate}
                onChange={(value) =>
                  updateArrayItem("education", index, { ...education, startDate: value })
                }
              />
            </div>

            <div className="space-y-2">
              <DateField
                label="End Date"
                id={`education-${index}-endDate`}
                value={education.endDate}
                disabled={!!education.current}
                onChange={(value) =>
                  updateArrayItem("education", index, { ...education, endDate: value })
                }
              />
            </div>
          </div>
        </div>

        {/* Description full width */}
        <div className="space-y-2 md:col-span-2">
          <TextareaField
            label="Description"
            id={`education-${index}-description`}
            value={education.description}
            onChange={(value) =>
              updateArrayItem("education", index, { ...education, description: value })
            }
            placeholder="Write a short description of your coursework, honors, or activities."
            rows={4}
          />
        </div>
      </div>
    </SectionCard>
  );
}

export default function Education() {
  const { resumeData, addItem, removeItem } = useResumeContext();

  const educations = resumeData.education ?? [];
  const showRemove = educations.length > 1;


  return (
    <div className="space-y-4">
      <SectionHeader title="Education" />

      <div className="space-y-4">
        {educations.map((education, index) => (
          <EducationCard
            key={index}
            education={education}
            index={index}
            removable={showRemove}
            onRemove={() => removeItem("education", index)}
          />
        ))}
      </div>

      <div className="flex justify-end">
        <AddItemButton onClick={() => addItem("education")}>Add Education</AddItemButton>
      </div>
    </div>
  );
}





