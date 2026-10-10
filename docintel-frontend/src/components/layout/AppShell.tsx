import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { Library, MessageSquare, LogOut, Settings, Menu, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Avatar } from "@/components/ui/avatar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/library", label: "Library", icon: Library },
  { to: "/chat", label: "Assistant", icon: MessageSquare },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function AppShell() {
  const { user, logout } = useAuth();
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  const closeMobileNav = () => setIsMobileNavOpen(false);

  return (
    <div className="flex h-screen flex-col bg-background md:flex-row">
      {/* Mobile top bar — hidden on md+ where the sidebar is always visible */}
      <div className="flex items-center justify-between border-b border-border bg-card px-4 py-3 md:hidden">
        <div className="flex items-center gap-2 font-serif text-lg font-semibold text-foreground">
          <span className="flex h-7 w-7 items-center justify-center rounded bg-primary font-mono text-xs text-primary-foreground">
            DI
          </span>
          DocIntel
        </div>
        <button
          onClick={() => setIsMobileNavOpen(true)}
          className="rounded-md p-1.5 text-foreground hover:bg-secondary"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
      </div>

      {/* Backdrop for mobile drawer */}
      {isMobileNavOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={closeMobileNav}
          aria-hidden="true"
        />
      )}

      {/* Sidebar — fixed drawer on mobile, static column on md+ */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 shrink-0 transform flex-col border-r border-border bg-card transition-transform duration-200 md:relative md:z-auto md:w-60 md:translate-x-0",
          isMobileNavOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center justify-between px-5 py-5">
          <div className="flex items-center gap-2 font-serif text-lg font-semibold text-foreground">
            <span className="flex h-7 w-7 items-center justify-center rounded bg-primary font-mono text-xs text-primary-foreground">
              DI
            </span>
            DocIntel
          </div>
          <button
            onClick={closeMobileNav}
            className="rounded-md p-1 text-muted-foreground hover:bg-secondary md:hidden"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-3">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={closeMobileNav}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-secondary text-secondary-foreground"
                    : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border p-3">
          <div className="mb-1 flex items-center justify-between px-2">
            <span className="text-xs font-medium text-muted-foreground">Appearance</span>
            <ThemeToggle />
          </div>
          <div className="flex items-center gap-3 rounded-md px-2 py-2">
            <Avatar name={user?.full_name || user?.email || "?"} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-foreground">
                {user?.full_name || user?.email}
              </p>
              <p className="truncate text-xs capitalize text-muted-foreground">{user?.role}</p>
            </div>
            <button
              onClick={logout}
              title="Log out"
              className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
