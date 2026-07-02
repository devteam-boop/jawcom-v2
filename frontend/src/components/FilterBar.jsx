import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export default function FilterBar({ options, value, onChange, className, testId = "filter-bar" }) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-1 rounded-lg bg-secondary/60 p-1",
        className
      )}
      data-testid={testId}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <Button
            key={opt.value}
            variant="ghost"
            size="sm"
            onClick={() => onChange?.(opt.value)}
            className={cn(
              "h-7 rounded-md px-3 text-xs font-medium transition-colors",
              active
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
            data-testid={`filter-${opt.value}`}
          >
            {opt.label}
            {opt.count !== undefined && (
              <span
                className={cn(
                  "ml-1.5 rounded px-1 text-[10px] font-semibold",
                  active ? "bg-primary/10 text-primary" : "text-muted-foreground"
                )}
              >
                {opt.count}
              </span>
            )}
          </Button>
        );
      })}
    </div>
  );
}
