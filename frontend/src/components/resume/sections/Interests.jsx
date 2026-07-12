import SectionCard from "@/components/common/SectionCard";
import SectionHeader from "@/components/common/SectionHeader";
import AddItemButton from "@/components/common/AddItemButton";
import RemoveItemButton from "@/components/common/RemoveItemButton";
import InputField from "@/components/common/InputField";

import { useResumeContext } from "@/context/useResumeContext";

function InterestCard({
  interest,
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
            Interest {index + 1}
          </h4>
          <p className="text-xs text-muted-foreground mt-1">
            Add the interest details below.
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
          label="Interest"
          id={`interests-${index}-name`}
          value={interest?.name || ""}
          onChange={(value) =>
            updateArrayItem("interests", index, {
              ...interest,
              name: value,
            })
          }
          placeholder="e.g., Open Source"
        />
      </div>
    </SectionCard>
  );
}

export default function Interests() {
  const {
    resumeData,
    addItem,
    removeItem,
    updateArrayItem,
  } = useResumeContext();

  const interests = resumeData?.interests || [];
  const showRemove = interests.length > 1;

  return (
    <div className="space-y-4">
      <SectionHeader title="Interests" />

      <div className="space-y-4">
        {interests.map((interest, index) => (
          <InterestCard
            key={interest.id || index}
            interest={interest}
            index={index}
            removable={showRemove}
            onRemove={() => removeItem("interests", index)}
            updateArrayItem={updateArrayItem}
          />
        ))}
      </div>

      <div className="flex justify-end">
        <AddItemButton onClick={() => addItem("interests")}>
          Add Interest
        </AddItemButton>
      </div>
    </div>
  );
}

