import { Skeleton } from "@/components/ui/skeleton";

export function SkeletonHero() {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Skeleton className="h-48 rounded-xl lg:col-span-2" />
      <Skeleton className="h-48 rounded-xl" />
    </div>
  );
}

export function SkeletonStats() {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="h-32 rounded-xl" />
      ))}
    </div>
  );
}

export function SkeletonReadiness() {
  return <Skeleton className="h-64 rounded-xl" />;
}

export function SkeletonFocusCard() {
  return (
    <div>
      <Skeleton className="mb-3 h-4 w-40" />
      <div className="grid gap-4 sm:grid-cols-2">
        <Skeleton className="h-24 rounded-xl" />
        <Skeleton className="h-24 rounded-xl" />
      </div>
    </div>
  );
}

export function SkeletonActivityFeed() {
  return (
    <div>
      <Skeleton className="mb-3 h-4 w-32" />
      <Skeleton className="h-64 rounded-xl" />
    </div>
  );
}

export function SkeletonUpcomingTasks() {
  return (
    <div>
      <Skeleton className="mb-3 h-4 w-32" />
      <Skeleton className="h-64 rounded-xl" />
    </div>
  );
}

export function DashboardSkeletons() {
  return (
    <div className="mx-auto max-w-7xl animate-fade-up space-y-6">
      <SkeletonHero />
      <SkeletonStats />
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="flex flex-col gap-4 lg:col-span-2">
          <SkeletonFocusCard />
          <SkeletonActivityFeed />
        </div>
        <div className="flex flex-col gap-4">
          <SkeletonUpcomingTasks />
        </div>
      </div>
    </div>
  );
}

export default DashboardSkeletons;
