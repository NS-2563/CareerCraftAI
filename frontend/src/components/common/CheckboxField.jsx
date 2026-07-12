import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

export default function CheckboxField({ label, checked, onCheckedChange }) {
  return (
    <div className="flex items-center space-x-2">
      <Checkbox checked={checked} onCheckedChange={onCheckedChange} />
      {label ? <Label>{label}</Label> : null}
    </div>
  );
}



