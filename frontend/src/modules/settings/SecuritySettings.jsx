import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { authService } from "@/services/auth";
import { useAuth } from "@/context/AuthContext";

function SettingCard({ title, description, action, children }) {
  return (
    <Card className="mb-4 rounded-xl border-border bg-card p-6 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold">{title}</h3>
          {description && <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>}
        </div>
        {action}
      </div>
      {children}
    </Card>
  );
}

export default function SecuritySettings() {
  const { user, logout, refresh } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState(user?.full_name || "");
  const [savingProfile, setSavingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);

  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(true);

  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  useEffect(() => {
    setFullName(user?.full_name || "");
  }, [user]);

  const loadSessions = () => {
    setLoadingSessions(true);
    authService
      .listSessions()
      .then(setSessions)
      .catch(() => setSessions([]))
      .finally(() => setLoadingSessions(false));
  };

  useEffect(() => {
    loadSessions();
    authService
      .loginHistory(20)
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoadingHistory(false));
  }, []);

  const handleSaveProfile = async () => {
    if (!fullName.trim()) return;
    setSavingProfile(true);
    try {
      await authService.updateProfile({ fullName: fullName.trim() });
      await refresh();
      toast.success("Profile updated");
    } catch (err) {
      toast.error(err?.body?.detail || err.message || "Could not update profile");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast.error("New passwords do not match");
      return;
    }
    setChangingPassword(true);
    try {
      await authService.changePassword({ currentPassword, newPassword });
      toast.success("Password changed. Other sessions were signed out.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      loadSessions();
    } catch (err) {
      toast.error(err?.body?.detail || err.message || "Could not change password");
    } finally {
      setChangingPassword(false);
    }
  };

  const handleRevokeSession = async (id) => {
    try {
      await authService.revokeSession(id);
      loadSessions();
    } catch (err) {
      toast.error(err?.body?.detail || err.message || "Could not revoke session");
    }
  };

  const handleSignOut = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div data-testid="settings-security-panel">
      <SettingCard title="Your account" description="Signed in as this admin.">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Email</Label>
            <Input value={user?.email || ""} disabled />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="sec-full-name">Full name</Label>
            <Input id="sec-full-name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
        </div>
        <div className="mt-4 flex items-center gap-2">
          <Button size="sm" onClick={handleSaveProfile} disabled={savingProfile}>
            {savingProfile ? "Saving…" : "Save profile"}
          </Button>
          <Button size="sm" variant="outline" onClick={handleSignOut} data-testid="settings-sign-out">
            Sign out
          </Button>
        </div>
      </SettingCard>

      <SettingCard title="Change password" description="6+ characters, upper, lower, number, and special character.">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="sec-current-pw">Current password</Label>
            <Input id="sec-current-pw" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="sec-new-pw">New password</Label>
            <Input id="sec-new-pw" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="sec-confirm-pw">Confirm new password</Label>
            <Input id="sec-confirm-pw" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
          </div>
        </div>
        <Button
          size="sm"
          className="mt-4"
          onClick={handleChangePassword}
          disabled={changingPassword || !currentPassword || !newPassword}
          data-testid="settings-change-password"
        >
          {changingPassword ? "Changing…" : "Change password"}
        </Button>
      </SettingCard>

      <SettingCard title="Active sessions" description="Devices/browsers currently signed in as you.">
        {loadingSessions ? (
          <p className="text-xs text-muted-foreground">Loading…</p>
        ) : sessions.length === 0 ? (
          <p className="text-xs text-muted-foreground">No active sessions.</p>
        ) : (
          <ul className="divide-y divide-border">
            {sessions.map((s) => (
              <li key={s.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium">
                    {s.ip_address || "Unknown IP"} {s.is_current && <span className="text-xs text-primary">(this device)</span>}
                  </div>
                  <div className="truncate text-xs text-muted-foreground">{s.user_agent || "Unknown device"}</div>
                  <div className="text-[11px] text-muted-foreground">
                    Last active {s.last_seen_at ? new Date(s.last_seen_at).toLocaleString() : "—"} · Expires{" "}
                    {new Date(s.expires_at).toLocaleString()}
                  </div>
                </div>
                {!s.is_current && (
                  <Button variant="ghost" size="sm" className="text-xs" onClick={() => handleRevokeSession(s.id)}>
                    Terminate
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </SettingCard>

      <SettingCard title="Login history" description="Recent sign-in and security events on this account.">
        <Separator className="mb-3" />
        {loadingHistory ? (
          <p className="text-xs text-muted-foreground">Loading…</p>
        ) : history.length === 0 ? (
          <p className="text-xs text-muted-foreground">No history yet.</p>
        ) : (
          <ul className="max-h-64 space-y-2 overflow-y-auto font-mono text-xs">
            {history.map((h, i) => (
              <li key={i} className="text-muted-foreground">
                {new Date(h.created_at).toLocaleString()} — {h.event_type} {h.ip_address ? `from ${h.ip_address}` : ""}
              </li>
            ))}
          </ul>
        )}
      </SettingCard>
    </div>
  );
}
