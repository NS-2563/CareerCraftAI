import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

export default function ReviewSection({
  title,
  summary,
  aiEnhanced = false,
  defaultOpen = true,
  children,
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border rounded-xl bg-white overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm font-semibold text-gray-900 truncate">
            {title}
          </span>
          {summary !== undefined && !open && (
            <span className="text-xs text-gray-400 truncate ml-1">
              {summary}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {aiEnhanced && (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
              AI enhanced
            </span>
          )}
          {open ? (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-400" />
          )}
        </div>
      </button>
      {open && (
        <div className="px-4 pb-4 pt-1 border-t border-gray-100">
          {children}
        </div>
      )}
    </div>
  );
}
