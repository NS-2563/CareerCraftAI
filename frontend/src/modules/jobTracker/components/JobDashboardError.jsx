import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function JobDashboardError({
  title = "Something went wrong",
  message,
}) {
  return (
    <Alert variant="destructive">
      <AlertTitle>{title}</AlertTitle>
      {message ? <AlertDescription>{message}</AlertDescription> : null}
    </Alert>
  );
}

