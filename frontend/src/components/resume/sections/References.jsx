    

import SectionCard from "@/components/common/SectionCard";
import SectionHeader from "@/components/common/SectionHeader";
import AddItemButton from "@/components/common/AddItemButton";
import RemoveItemButton from "@/components/common/RemoveItemButton";
import InputField from "@/components/common/InputField";

import { useResumeContext } from "@/context/useResumeContext";


function ReferenceCard({ reference, index, removable, onRemove }) {
  const { updateArrayItem } = useResumeContext();

  return (
    <SectionCard>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h4 className="font-semibold">Reference {index + 1}</h4>
          <p className="text-xs text-muted-foreground mt-1">Add the reference details below.</p>
        </div>

        <RemoveItemButton
          onClick={onRemove}
          disabled={!removable}
          className="h-8 px-2"
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <InputField
            label="Reference Name"
            id={`references-${index}-name`}
            value={reference?.name ?? ""}
            onChange={(value) =>
              updateArrayItem("references", index, {
                ...reference,
                name: value,
              })
            }
            placeholder="e.g., John Smith"
          />
        </div>

        <div className="space-y-2">
          <InputField
            label="Designation"
            id={`references-${index}-designation`}
            value={reference?.designation ?? ""}
            onChange={(value) =>
              updateArrayItem("references", index, {
                ...reference,
                designation: value,
              })
            }
            placeholder="e.g., Hiring Manager"
          />
        </div>

        <div className="space-y-2">
          <InputField
            label="Organization"
            id={`references-${index}-organization`}
            value={reference?.organization ?? ""}
            onChange={(value) =>
              updateArrayItem("references", index, {
                ...reference,
                organization: value,
              })
            }
            placeholder="e.g., ABC Company"
          />
        </div>

        <div className="space-y-2">
          <InputField
            label="Email"
            id={`references-${index}-email`}
            value={reference?.email ?? ""}
            onChange={(value) =>
              updateArrayItem("references", index, {
                ...reference,
                email: value,
              })
            }
            placeholder="e.g., reference@email.com"
            type="email"
          />
        </div>

        <div className="space-y-2 md:col-span-2">
          <InputField
            label="Phone"
            id={`references-${index}-phone`}
            value={reference?.phone ?? ""}
            onChange={(value) =>
              updateArrayItem("references", index, {
                ...reference,
                phone: value,
              })
            }
            placeholder="e.g., +1 555 123 4567"
          />
        </div>
      </div>
    </SectionCard>
  );
}

export default function References() {
  const { resumeData, addItem, removeItem} = useResumeContext();

  const references = resumeData.references ?? [];

  const showRemove = references.length > 1;






  return (
    <div className="space-y-4">
      <SectionHeader title="References" />

      <div className="space-y-4">
        {references.map((reference, index) => (
          <ReferenceCard
            key={index}
            reference={reference}
            index={index}
            removable={showRemove}
            onRemove={() => removeItem("references", index)}
          />
        ))}
      </div>


      <div className="flex justify-end">
        <AddItemButton onClick={() => addItem("references")}>Add Reference</AddItemButton>
      </div>
    </div>
  );
}




