import { Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function RemoveItemButton({ onClick, disabled, className }) {
  return (
    <Button
      type="button"
      variant="destructive"
      size="sm"
      onClick={onClick}
      disabled={disabled}
      className={className}
    >
      <Trash2 className="mr-2 h-4 w-4" />
      Remove
    </Button>
  );
}



