import { Plus, Trash2 } from "lucide-react";

const fieldMeta = {
  experience: [
    { key: "company", label: "Company", type: "text" },
    { key: "position", label: "Position", type: "text" },
    { key: "location", label: "Location", type: "text" },
    { key: "startDate", label: "Start Date", type: "text" },
    { key: "endDate", label: "End Date", type: "text" },
    { key: "current", label: "Current Position", type: "checkbox" },
    { key: "description", label: "Description", type: "textarea" },
  ],
  education: [
    { key: "institution", label: "Institution", type: "text" },
    { key: "degree", label: "Degree", type: "text" },
    { key: "fieldOfStudy", label: "Field of Study", type: "text" },
    { key: "location", label: "Location", type: "text" },
    { key: "startDate", label: "Start Date", type: "text" },
    { key: "endDate", label: "End Date", type: "text" },
    { key: "current", label: "Currently Enrolled", type: "checkbox" },
    { key: "gpa", label: "GPA", type: "text" },
    { key: "description", label: "Description", type: "textarea" },
  ],
  projects: [
    { key: "title", label: "Title", type: "text" },
    { key: "techStack", label: "Tech Stack", type: "text" },
    { key: "github", label: "GitHub URL", type: "text" },
    { key: "liveDemo", label: "Live Demo URL", type: "text" },
    { key: "description", label: "Description", type: "textarea" },
  ],
  certifications: [
    { key: "name", label: "Name", type: "text" },
    { key: "issuer", label: "Issuer", type: "text" },
    { key: "issueDate", label: "Issue Date", type: "text" },
    { key: "credentialUrl", label: "Credential URL", type: "text" },
  ],
  languages: [
    { key: "language", label: "Language", type: "text" },
    { key: "proficiency", label: "Proficiency", type: "text" },
  ],
  interests: [
    { key: "name", label: "Interest", type: "text" },
  ],
  references: [
    { key: "name", label: "Name", type: "text" },
    { key: "designation", label: "Designation", type: "text" },
    { key: "organization", label: "Organization", type: "text" },
    { key: "email", label: "Email", type: "text" },
    { key: "phone", label: "Phone", type: "text" },
  ],
};

function getBlankItem(section) {
  const fields = fieldMeta[section] || [];
  const item = {};
  for (const f of fields) {
    item[f.key] = f.type === "checkbox" ? false : "";
  }
  return item;
}

export default function ReviewArraySection({
  section,
  items,
  sourceMeta,
  onUpdate,
  editedFields,
}) {
  const fields = fieldMeta[section] || [];
  const sectionSources = sourceMeta?.[section]?.sources || {};

  const handleItemChange = (itemIdx, fieldKey, value) => {
    const updated = [...items];
    updated[itemIdx] = { ...updated[itemIdx], [fieldKey]: value };
    onUpdate(section, updated);
  };

  const handleRemove = (itemIdx) => {
    const updated = items.filter((_, i) => i !== itemIdx);
    onUpdate(section, updated);
  };

  const handleAdd = () => {
    const updated = [...items, getBlankItem(section)];
    onUpdate(section, updated);
  };

  const getSource = (itemIdx, fieldKey) => {
    const sourceKey = `entry_${itemIdx}_${fieldKey}`;
    return sectionSources[sourceKey] || "";
  };

  const isEdited = (itemIdx, fieldKey) => {
    return editedFields?.[`${section}.${itemIdx}.${fieldKey}`] || false;
  };

  if (!items || items.length === 0) {
    return (
      <div>
        <p className="text-sm text-gray-400 mb-3">No entries found</p>
        <button
          type="button"
          onClick={handleAdd}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add {section}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item, itemIdx) => (
        <div
          key={itemIdx}
          className="border border-gray-200 rounded-lg p-3 bg-gray-50/50"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
              {`${section} ${itemIdx + 1}`}
            </span>
            <button
              type="button"
              onClick={() => handleRemove(itemIdx)}
              className="p-1 rounded-md hover:bg-red-50 hover:text-red-600 text-gray-400 transition-colors"
              title={`Remove ${section}`}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {fields.map((field) => (
              <div
                key={field.key}
                className={field.type === "textarea" ? "sm:col-span-2" : ""}
              >
                <div className="flex items-start gap-1.5">
                  <div className="flex-1 min-w-0">
                    <label className="block text-xs font-medium text-gray-500 mb-0.5">
                      {field.label}
                    </label>
                    {field.type === "textarea" ? (
                      <textarea
                        defaultValue={item[field.key] ?? ""}
                        onChange={(e) =>
                          handleItemChange(itemIdx, field.key, e.target.value)
                        }
                        className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary bg-white min-h-[50px] resize-y"
                        rows={2}
                      />
                    ) : field.type === "checkbox" ? (
                      <div className="flex items-center h-9">
                        <input
                          type="checkbox"
                          defaultChecked={!!item[field.key]}
                          onChange={(e) =>
                            handleItemChange(
                              itemIdx,
                              field.key,
                              e.target.checked
                            )
                          }
                          className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                        />
                      </div>
                    ) : (
                      <input
                        type="text"
                        defaultValue={item[field.key] ?? ""}
                        onChange={(e) =>
                          handleItemChange(itemIdx, field.key, e.target.value)
                        }
                        className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary bg-white"
                      />
                    )}
                  </div>
                  {getSource(itemIdx, field.key) === "ai" &&
                    !isEdited(itemIdx, field.key) && (
                      <span className="shrink-0 mt-5 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 select-none">
                        AI
                      </span>
                    )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      <button
        type="button"
        onClick={handleAdd}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Add {section}
      </button>
    </div>
  );
}
