import { AlertTriangle } from "lucide-react";

export default function ErrorState({
  message,
  onRetry
}) {
  return (
    <div className="rounded-xl border border-destructive/30 p-10">

      <div className="flex flex-col items-center text-center">

        <AlertTriangle
          className="h-14 w-14 text-destructive mb-5"
        />

        <h2 className="text-2xl font-bold">
          Unable to Generate Career Report
        </h2>

        <p className="mt-3 text-muted-foreground max-w-xl">

          {message ||
            "Something went wrong while communicating with the AI service."}

        </p>

        <button
          onClick={onRetry}
          className="mt-8 rounded-lg bg-primary px-6 py-2 text-primary-foreground hover:opacity-90 transition"
        >
          Try Again
        </button>

      </div>

    </div>
  );
}