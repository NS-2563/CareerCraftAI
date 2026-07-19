

import SectionCard from "@/components/common/SectionCard";
import SectionHeader from "@/components/common/SectionHeader";
import AddItemButton from "@/components/common/AddItemButton";
import RemoveItemButton from "@/components/common/RemoveItemButton";
import InputField from "@/components/common/InputField";
import DateField from "@/components/common/DateField";

import { useResumeContext } from "@/resume/context/useResumeContext";

function CertificationCard({
  certification,
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
            Certification {index + 1}
          </h4>
          <p className="text-xs text-muted-foreground mt-1">
            Add the certification details below.
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
          label="Certification Name"
          id={`certifications-${index}-name`}
          value={certification.name || ""}
          onChange={(value) =>
            updateArrayItem("certifications", index, {
              ...certification,
              name: value,
            })
          }
          placeholder="e.g., AWS Certified Solutions Architect"
        />

        <InputField
          label="Issuing Organization"
          id={`certifications-${index}-issuer`}
          value={certification.issuer || ""}
          onChange={(value) =>
            updateArrayItem("certifications", index, {
              ...certification,
              issuer: value,
            })
          }
          placeholder="e.g., Amazon Web Services"
        />

        <DateField
          label="Issue Date"
          id={`certifications-${index}-issueDate`}
          value={certification.issueDate || ""}
          onChange={(value) =>
            updateArrayItem("certifications", index, {
              ...certification,
              issueDate: value,
            })
          }
        />

        <InputField
          label="Credential URL"
          id={`certifications-${index}-credentialUrl`}
          value={certification.credentialUrl || ""}
          onChange={(value) =>
            updateArrayItem("certifications", index, {
              ...certification,
              credentialUrl: value,
            })
          }
          placeholder="https://your-credential-link.com"
        />
      </div>
    </SectionCard>
  );
}

export default function Certifications() {
  const {
    resumeData,
    addItem,
    removeItem,
    updateArrayItem,
  } = useResumeContext();

  const certifications = resumeData?.certifications || [];
  const showRemove = certifications.length > 1;

  return (
    <div className="space-y-4">
      <SectionHeader title="Certifications" />

      <div className="space-y-4">
        {certifications.map((certification, index) => (
          <CertificationCard
            key={certification.id || index}
            certification={certification}
            index={index}
            removable={showRemove}
            onRemove={() => removeItem("certifications", index)}
            updateArrayItem={updateArrayItem}
          />
        ))}
      </div>

      <div className="flex justify-end">
        <AddItemButton onClick={() => addItem("certifications")}>
          Add Certification
        </AddItemButton>
      </div>
    </div>
  );
}

