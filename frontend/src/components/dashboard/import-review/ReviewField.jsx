export default function ReviewField({
  label,
  value,
  source,
  onChange,
  type = "text",
  edited,
}) {
  const isAi = !edited && source === "ai";

  const handleChange = (e) => {
    const newVal = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    onChange?.(newVal);
  };

  const effectiveValue = value ?? "";

  const inputClass =
    "w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary bg-white transition-colors";

  return (
    <div className="flex items-start gap-2">
      <div className="flex-1 min-w-0">
        <label className="block text-xs font-medium text-gray-500 mb-0.5">
          {label}
        </label>
        {type === "textarea" ? (
          <textarea
            defaultValue={effectiveValue}
            onChange={handleChange}
            className={`${inputClass} min-h-[60px] resize-y`}
            rows={2}
          />
        ) : type === "checkbox" ? (
          <div className="flex items-center h-9">
            <input
              type="checkbox"
              defaultChecked={!!effectiveValue}
              onChange={handleChange}
              className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
          </div>
        ) : (
          <input
            type={type}
            defaultValue={effectiveValue}
            onChange={handleChange}
            className={inputClass}
          />
        )}
      </div>
      {isAi && (
        <span className="shrink-0 mt-5 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 select-none">
          AI
        </span>
      )}
    </div>
  );
}
