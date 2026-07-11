import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";


export default function InputField({ label, value, onChange, placeholder, type = "text", className = "space-y-2" }) {

  return (
    <div className={className}>
      {label ? <Label>{label}</Label> : null}
      <Input type={type} value={value ?? ""} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} />
    </div>
  );
}

