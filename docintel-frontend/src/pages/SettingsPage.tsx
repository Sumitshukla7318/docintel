import { useNavigate } from "react-router-dom";
import { LogOut, Moon, Sun, ShieldCheck, ShieldAlert } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-2xl px-6 py-10">
        <h1 className="font-serif text-3xl font-semibold text-foreground">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your profile and preferences.</p>

        <div className="mt-8 space-y-6">
          {/* Profile */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Profile</CardTitle>
              <CardDescription>Your account details for this workspace.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <Avatar name={user?.full_name || user?.email || "?"} className="h-14 w-14 text-lg" />
                <div className="min-w-0">
                  <p className="truncate text-base font-medium text-foreground">
                    {user?.full_name || "No name set"}
                  </p>
                  <p className="truncate text-sm text-muted-foreground">{user?.email}</p>
                </div>
              </div>

              <Separator className="my-5" />

              <dl className="grid grid-cols-2 gap-y-3 text-sm">
                <dt className="text-muted-foreground">Role</dt>
                <dd className="text-right font-medium capitalize text-foreground">{user?.role}</dd>

                <dt className="text-muted-foreground">Account status</dt>
                <dd className="flex justify-end">
                  <Badge variant={user?.is_active ? "success" : "destructive"}>
                    {user?.is_active ? "Active" : "Inactive"}
                  </Badge>
                </dd>

                <dt className="text-muted-foreground">Email verification</dt>
                <dd className="flex justify-end items-center gap-1.5">
                  {user?.is_verified ? (
                    <>
                      <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                      <span className="font-medium text-foreground">Verified</span>
                    </>
                  ) : (
                    <>
                      <ShieldAlert className="h-3.5 w-3.5 text-amber-600" />
                      <span className="font-medium text-foreground">Not verified</span>
                    </>
                  )}
                </dd>

                <dt className="text-muted-foreground">Workspace ID</dt>
                <dd className="truncate text-right font-mono text-xs text-muted-foreground">
                  {user?.workspace_id}
                </dd>
              </dl>
            </CardContent>
          </Card>

          {/* Appearance */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Appearance</CardTitle>
              <CardDescription>Choose how DocIntel looks on this device.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {theme === "light" ? (
                    <Sun className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Moon className="h-4 w-4 text-muted-foreground" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-foreground">Dark mode</p>
                    <p className="text-xs text-muted-foreground">
                      {theme === "dark" ? "Currently on" : "Currently off"}
                    </p>
                  </div>
                </div>
                <Switch checked={theme === "dark"} onCheckedChange={toggleTheme} />
              </div>
            </CardContent>
          </Card>

          {/* Account actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Account</CardTitle>
              <CardDescription>Session and sign-out options.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" onClick={handleLogout} className="gap-2 text-destructive hover:text-destructive">
                <LogOut className="h-4 w-4" />
                Log out of this account
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
