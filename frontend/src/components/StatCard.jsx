import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

export default function StatCard({ label, value, delta, trend, hint, icon: Icon, testId }) {
  const trendColor =
    trend === "up"
      ? "text-emerald-600 dark:text-emerald-400"
      : trend === "down"
      ? "text-rose-600 dark:text-rose-400"
      : "text-muted-foreground";
  const TrendIcon = trend === "up" ? ArrowUpRight : trend === "down" ? ArrowDownRight : Minus;

  return (
    <Card
      className="rounded-xl border-border bg-card p-5 shadow-sm transition-colors hover:border-primary/30"
      data-testid={testId}
    >
      <div className="flex items-start justify-between">
        <span className="text-sm font-medium text-muted-foreground">{label}</span>
        {Icon && (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="font-mono text-3xl font-semibold tracking-tight">{value}</span>
      </div>
      <div className="mt-1.5 flex items-center gap-2 text-xs">
        {delta !== undefined && delta !== null && (
          <span className={cn("inline-flex items-center gap-0.5 font-semibold", trendColor)}>
            <TrendIcon className="h-3 w-3" />
            {delta > 0 ? "+" : ""}
            {delta}%
          </span>
        )}
        {hint && <span className="text-muted-foreground">{hint}</span>}
      </div>
    </Card>
  );
}
