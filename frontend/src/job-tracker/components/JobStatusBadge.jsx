import { Badge } from "@/components/ui/badge";

const STATUS_META = {
  Wishlist: { variant: "outline" },
  Applied: { variant: "secondary" },
  Interview: { variant: "default" },
  Offer: { variant: "outline" },
  Accepted: { variant: "default" },
  Rejected: { variant: "destructive" },
  Withdrawn: { variant: "ghost" },
};

export function JobStatusBadge({ status, className }) {
  const meta = STATUS_META[status] || { variant: "outline" };

  return (
    <Badge variant={meta.variant} className={className}>
      {status || "Unknown"}
    </Badge>
  );
}

