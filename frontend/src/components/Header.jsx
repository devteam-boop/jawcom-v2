import { Bell, Menu, Search, ChevronsUpDown, Check } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import ThemeToggle from "@/components/ThemeToggle";
import { WORKSPACES } from "@/dummy-data";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

function initialsOf(name) {
  return (name || "")
    .split(" ")
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export default function Header({ onToggleSidebar, onOpenMobile }) {
  const [workspace, setWorkspace] = useState(WORKSPACES[0]);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleSignOut = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <header
      className="flex h-16 shrink-0 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur lg:px-6"
      data-testid="app-header"
    >
      {/* Mobile menu */}
      <button
        onClick={onOpenMobile}
        className="rounded-md p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground lg:hidden"
        data-testid="header-open-mobile"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Desktop sidebar toggle */}
      <button
        onClick={onToggleSidebar}
        className="hidden rounded-md p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground lg:inline-flex"
        data-testid="header-toggle-sidebar"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Workspace switcher */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="hidden h-9 items-center gap-2 px-2 text-sm font-medium hover:bg-secondary md:inline-flex"
            data-testid="workspace-switcher"
          >
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10 text-[11px] font-bold text-primary">
              {workspace.name.split(" ").map((w) => w[0]).slice(0, 2).join("")}
            </div>
            <span className="max-w-[160px] truncate">{workspace.name}</span>
            <ChevronsUpDown className="h-3.5 w-3.5 text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-64">
          <DropdownMenuLabel className="text-[11px] uppercase tracking-wider text-muted-foreground">
            Workspaces
          </DropdownMenuLabel>
          {WORKSPACES.map((w) => (
            <DropdownMenuItem
              key={w.id}
              onClick={() => setWorkspace(w)}
              className="flex items-center justify-between"
              data-testid={`workspace-${w.id}`}
            >
              <div className="flex flex-col">
                <span className="text-sm font-medium">{w.name}</span>
                <span className="text-xs text-muted-foreground">{w.plan} plan</span>
              </div>
              {w.id === workspace.id && <Check className="h-4 w-4 text-primary" />}
            </DropdownMenuItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuItem className="text-sm">+ Create workspace</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Search */}
      <div className="relative flex-1 max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              navigate(query ? `/search?q=${encodeURIComponent(query)}` : "/search");
            }
          }}
          onFocus={() => navigate(query ? `/search?q=${encodeURIComponent(query)}` : "/search")}
          placeholder="Search customers, conversations, campaigns…"
          className="h-9 pl-9 bg-secondary/40 border-transparent focus-visible:bg-background"
          data-testid="header-search"
        />
      </div>

      <div className="flex flex-1 items-center justify-end gap-1.5">
        <ThemeToggle />

        {/* Notifications */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="relative h-9 w-9"
              data-testid="header-notifications"
            >
              <Bell className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-96">
            <div className="flex items-center justify-between px-2 py-1.5">
              <DropdownMenuLabel className="p-0">Notifications</DropdownMenuLabel>
            </div>
            <DropdownMenuSeparator />
            {/* No notifications API exists yet — this used to show fake
                demo items. See audit report: needs a backend endpoint. */}
            <div className="px-3 py-6 text-center text-xs text-muted-foreground">
              No notifications yet.
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="flex h-9 items-center gap-2 rounded-lg px-1.5 hover:bg-secondary"
              data-testid="header-user-menu"
            >
              <Avatar className="h-7 w-7">
                <AvatarFallback className="bg-primary text-[11px] font-semibold text-primary-foreground">
                  {initialsOf(user?.full_name) || "?"}
                </AvatarFallback>
              </Avatar>
              <span className="hidden text-sm font-medium md:block">
                {(user?.full_name || "").split(" ")[0]}
              </span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="flex flex-col">
                <span className="text-sm font-semibold">{user?.full_name}</span>
                <span className="text-xs font-normal text-muted-foreground">
                  {user?.email}
                </span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate("/settings")}>Profile &amp; security</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleSignOut} data-testid="header-sign-out">Sign out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
