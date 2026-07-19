import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export default function StatCard({
  title,
  value,
  icon,
  variant = "default",
  className,
}) {
  return (
    <Card className={cn("h-full", className)}>
      <CardHeader className="flex-row items-start justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon ? (
          <div className="flex items-center justify-center rounded-md bg-primary/10 p-2">
            {icon}
          </div>
        ) : (
          <Badge variant={variant} className="hidden sm:inline-flex">
            {title}
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold leading-tight">{value}</div>
      </CardContent>
    </Card>
  );
}
