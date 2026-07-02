import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function ChartCard({ title, description, action, children, className, testId }) {
  return (
    <Card
      className={cn("rounded-xl border-border bg-card p-5 shadow-sm", className)}
      data-testid={testId}
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold tracking-tight">{title}</h3>
          {description && (
            <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
          )}
        </div>
        {action}
      </div>
      <div className="w-full">{children}</div>
    </Card>
  );
}
