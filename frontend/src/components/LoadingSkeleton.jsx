import { Skeleton } from "@/components/ui/skeleton";

export default function LoadingSkeleton({ rows = 3 }) {
  return (
    <div className="space-y-3" data-testid="loading-skeleton">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full rounded-lg" />
      ))}
    </div>
  );
}
