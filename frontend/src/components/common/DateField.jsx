import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function DateField({
  label,
  value,
  onChange,
  disabled = false,
  className = "space-y-2",
}) {
  return (
    <div className={className}>
      {label ? <Label>{label}</Label> : null}

      <Input
        type="month"
        value={value ?? ""}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

