import * as React from "react";

import { cn } from "@/lib/utils";

const Label = React.forwardRef(function Label(
  { className, ...props },
  ref
) {
  return (
    <label
      ref={ref}
      className={cn("text-sm font-medium leading-none", className)}
      {...props}
    />
  );
});

export { Label };

