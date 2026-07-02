import { cn } from "@/lib/utils";

export default function PageHeader({ title, description, actions, className }) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 border-b border-border bg-background/60 px-4 py-5 backdrop-blur md:flex-row md:items-end md:justify-between md:px-8 md:py-6",
        className
      )}
      data-testid="page-header"
    >
      <div className="min-w-0">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl" data-testid="page-title">
          {title}
        </h1>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
