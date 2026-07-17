import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "@/constants/nav";
import { cn } from "@/lib/utils";
import { X, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function Sidebar({ collapsed, mobileOpen, onCloseMobile }) {
  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onCloseMobile}
          data-testid="sidebar-overlay"
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col border-r border-border bg-card transition-all duration-200 lg:relative lg:translate-x-0",
          collapsed ? "lg:w-[72px]" : "lg:w-64",
          "w-64",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
        data-testid="sidebar"
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b border-border px-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Zap className="h-4 w-4" strokeWidth={2.5} />
            </div>
            {!collapsed && (
              <div className="flex flex-col leading-tight">
                <span className="text-sm font-bold tracking-tight">JawCom</span>
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  AI Communication
                </span>
              </div>
            )}
          </div>
          <button
            onClick={onCloseMobile}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground lg:hidden"
            data-testid="sidebar-close-mobile"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-0.5 overflow-y-auto scrollbar-thin px-3 py-4">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
                onClick={onCloseMobile}
                data-testid={item.testId}
                className={({ isActive }) =>
                  cn(
                    "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                    collapsed && "justify-center px-2"
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" strokeWidth={2} />
                {!collapsed && (
                  <>
                    <span className="flex-1 truncate">{item.label}</span>
                    {item.badge ? (
                      <Badge
                        variant="secondary"
                        className="h-5 min-w-5 justify-center bg-primary/10 px-1.5 text-[10px] font-semibold text-primary"
                      >
                        {item.badge}
                      </Badge>
                    ) : null}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
