    

import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

export default function TextareaField({
  label,
  value,
  onChange,
  placeholder,
  rows = 4,
  className = "space-y-2",
}) {
  return (
    <div className={className}>
      {label ? <Label>{label}</Label> : null}

      <Textarea
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
      />
    </div>
  );
}