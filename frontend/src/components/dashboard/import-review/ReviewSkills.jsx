import { useState } from "react";
import { Plus, X } from "lucide-react";

export default function ReviewSkills({ items, onUpdate, section }) {
  const [inputValue, setInputValue] = useState("");

  const skillNames = (items || []).map((s) => s.name).filter(Boolean);

  const handleAddSkill = () => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;
    if (skillNames.some((s) => s.toLowerCase() === trimmed.toLowerCase())) return;
    const updated = [...(items || []), { name: trimmed, category: "" }];
    onUpdate(section, updated);
    setInputValue("");
  };

  const handleRemoveSkill = (index) => {
    const updated = (items || []).filter((_, i) => i !== index);
    onUpdate(section, updated);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddSkill();
    }
  };

  return (
    <div>
      {skillNames.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {items.map((skill, idx) =>
            skill.name ? (
              <span
                key={idx}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm bg-primary/10 text-primary border border-primary/20"
              >
                {skill.name}
                <button
                  type="button"
                  onClick={() => handleRemoveSkill(idx)}
                  className="hover:bg-primary/20 rounded-full p-0.5 transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ) : null
          )}
        </div>
      )}
      {skillNames.length === 0 && (
        <p className="text-sm text-gray-400 mb-3">No skills found</p>
      )}
      <div className="flex gap-2">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add a skill..."
          className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary bg-white"
        />
        <button
          type="button"
          onClick={handleAddSkill}
          disabled={!inputValue.trim()}
          className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary/5 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add
        </button>
      </div>
    </div>
  );
}
