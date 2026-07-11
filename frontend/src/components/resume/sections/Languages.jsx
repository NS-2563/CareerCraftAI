import SectionCard from "@/components/common/SectionCard";
import SectionHeader from "@/components/common/SectionHeader";
import AddItemButton from "@/components/common/AddItemButton";
import RemoveItemButton from "@/components/common/RemoveItemButton";
import InputField from "@/components/common/InputField";

import { useResumeContext } from "@/context/ResumeContext";

function LanguageCard({
  languageItem,
  index,
  removable,
  onRemove,
  updateArrayItem,
}) {
  return (
    <SectionCard>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h4 className="font-semibold">
            Language {index + 1}
          </h4>
          <p className="text-xs text-muted-foreground mt-1">
            Add the language details below.
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
          label="Language"
          id={`languages-${index}-language`}
          value={languageItem.language || ""}
          onChange={(value) =>
            updateArrayItem("languages", index, {
              ...languageItem,
              language: value,
            })
          }
          placeholder="e.g., English"
        />

        <InputField
          label="Proficiency"
          id={`languages-${index}-proficiency`}
          value={languageItem.proficiency || ""}
          onChange={(value) =>
            updateArrayItem("languages", index, {
              ...languageItem,
              proficiency: value,
            })
          }
          placeholder="e.g., Fluent"
        />
      </div>
    </SectionCard>
  );
}

export default function Languages() {
  const {
    resumeData,
    addItem,
    removeItem,
    updateArrayItem,
  } = useResumeContext();

  const languages = resumeData?.languages || [];
  const showRemove = languages.length > 1;

  return (
    <div className="space-y-4">
      <SectionHeader title="Languages" />

      <div className="space-y-4">
        {languages.map((languageItem, index) => (
          <LanguageCard
            key={languageItem.id || index}
            languageItem={languageItem}
            index={index}
            removable={showRemove}
            onRemove={() => removeItem("languages", index)}
            updateArrayItem={updateArrayItem}
          />
        ))}
      </div>

      <div className="flex justify-end">
        <AddItemButton onClick={() => addItem("languages")}>
          Add Language
        </AddItemButton>
      </div>
    </div>
  );
}