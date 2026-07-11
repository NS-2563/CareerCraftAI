import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function AddItemButton({ onClick, children }) {
  return (
    <Button type="button" variant="secondary" onClick={onClick}>
      <Plus className="mr-2 h-4 w-4" />
      {children}
    </Button>
  );
}

