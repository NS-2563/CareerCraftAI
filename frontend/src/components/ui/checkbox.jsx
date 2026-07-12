import * as React from "react";

import { cn } from "@/lib/utils";

const Checkbox = React.forwardRef(function Checkbox(
  { className, onCheckedChange, ...props },
  ref
) {
  return (
    <input
      ref={ref}
      type="checkbox"
      className={cn(
        "h-4 w-4 rounded border border-input bg-background text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      onChange={(e) => onCheckedChange?.(e.target.checked)}
      {...props}
    />
  );
});

Checkbox.displayName = "Checkbox";

export { Checkbox };

