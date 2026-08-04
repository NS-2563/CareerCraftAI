import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Settings2, User, Shield, Download, Trash2, LogOut, KeyRound, Check } from "lucide-react";
import PageHeader from "@/components/app/PageHeader";
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import ProfileForm from "@/components/profile/ProfileForm";
import userApi from "@/services/userApi";
import { useAuth } from "@/context/useAuth";

// ─── Account tab ───────────────────────────────────────────────────────

function AccountTab({ onSessionEnd }) {
  const { user, logout, refreshUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [actionError, setActionError] = useState("");
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const res = await userApi.getProfile();
      if (mounted) {
        if (res.success) setProfile(res.data);
        else setActionError(res.error || "Failed to load your profile.");
      }
      if (mounted) setLoading(false);
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const handleSave = async (values) => {
    setSaving(true);
    setFormError("");
    const res = await userApi.updateProfile(values);
    if (res.success) {
      setProfile(res.data);
      if (refreshUser) await refreshUser();
    } else {
      setFormError(res.error || "Failed to save your profile.");
    }
    setSaving(false);
  };

  const handleDownload = async () => {
    setDownloading(true);
    setActionError("");
    const res = await userApi.exportData();
    if (res.success) {
      const blob = new Blob([JSON.stringify(res.data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "careercraft-data.json";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } else {
      setActionError(res.error || "Failed to download your data.");
    }
    setDownloading(false);
  };

  const handleDelete = async () => {
    setDeleting(true);
    setActionError("");
    const res = await userApi.deleteAccount();
    if (res.success) {
      await logout();
      onSessionEnd("Your account has been deleted.");
    } else {
      setDeleting(false);
      setActionError(res.error || "Failed to delete your account. Please try again.");
    }
  };

  const emailToConfirm = profile?.email || user?.email || "";
  const confirmEnabled = typed === emailToConfirm && !deleting;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Account details</CardTitle>
          <CardDescription>Update your personal information.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-9 rounded-xl bg-muted/60" />
              <div className="h-9 rounded-xl bg-muted/60" />
              <div className="h-9 rounded-xl bg-muted/60" />
            </div>
          ) : (
            <ProfileForm
              initialValues={{
                full_name: profile?.full_name ?? "",
                username: profile?.username ?? "",
                email: profile?.email ?? "",
                profile_picture: profile?.profile_picture ?? "",
              }}
              onSubmit={handleSave}
              busy={saving}
              error={formError}
            />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your data</CardTitle>
          <CardDescription>Download a copy of everything stored for your account.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-3">
          <Button
            variant="outline"
            onClick={handleDownload}
            disabled={downloading}
          >
            <Download className="size-3.5" />
            {downloading ? "Preparing..." : "Download my data"}
          </Button>
          {actionError && <p className="text-sm text-destructive">{actionError}</p>}
        </CardContent>
      </Card>

      <Card className="border-destructive/30">
        <CardHeader>
          <CardTitle className="text-destructive">Delete account</CardTitle>
          <CardDescription>
            Permanently removes your account and all associated data — resumes,
            cover letters, career reports and job applications. This action is
            irreversible.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="destructive" onClick={() => setDeleteOpen(true)}>
            <Trash2 className="size-3.5" />
            Delete account
          </Button>
        </CardContent>
      </Card>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete your account?</DialogTitle>
            <DialogDescription>
              This permanently deletes your account and all associated data. It
              cannot be undone. Type <span className="font-medium text-foreground">{emailToConfirm}</span>{" "}
              to confirm.
            </DialogDescription>
          </DialogHeader>
          <Input
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            placeholder={emailToConfirm}
            disabled={deleting}
            autoComplete="off"
          />
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteOpen(false)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={!confirmEnabled}
              onClick={handleDelete}
            >
              {deleting ? "Deleting..." : "Delete account"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ─── Security tab ──────────────────────────────────────────────────────

function SecurityTab({ onSessionEnd }) {
  const { logout } = useAuth();
  const [pw, setPw] = useState({ current: "", next: "", confirm: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [logoutAllOpen, setLogoutAllOpen] = useState(false);
  const [loggingOutAll, setLoggingOutAll] = useState(false);

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setError("");

    if (pw.next.length < 8) {
      setError("New password must be at least 8 characters.");
      return;
    }
    if (pw.next !== pw.confirm) {
      setError("New password and confirmation do not match.");
      return;
    }

    setBusy(true);
    const res = await userApi.changePassword({
      current_password: pw.current,
      new_password: pw.next,
    });
    if (res.success) {
      await logout();
      onSessionEnd("Password changed — please log in again.");
    } else {
      setError(res.error || "Failed to change password.");
    }
    setBusy(false);
  };

  const handleLogoutAll = async () => {
    setLoggingOutAll(true);
    setError("");
    const res = await userApi.logoutAll();
    if (res.success) {
      await logout();
      onSessionEnd("You've been logged out of all devices. Please log in again.");
    } else {
      setLoggingOutAll(false);
      setLogoutAllOpen(false);
      setError(res.error || "Failed to log out of all devices.");
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Change password</CardTitle>
          <CardDescription>
            Updating your password signs you out everywhere, including this device,
            so you'll need to log in again.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordChange} className="space-y-4">
            {error && (
              <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </p>
            )}

            <div className="space-y-1.5">
              <label htmlFor="current-password" className="text-sm font-medium">
                Current password
              </label>
              <Input
                id="current-password"
                type="password"
                value={pw.current}
                onChange={(e) => setPw((p) => ({ ...p, current: e.target.value }))}
                autoComplete="current-password"
                required
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label htmlFor="new-password" className="text-sm font-medium">
                  New password
                </label>
                <Input
                  id="new-password"
                  type="password"
                  value={pw.next}
                  onChange={(e) => setPw((p) => ({ ...p, next: e.target.value }))}
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="confirm-password" className="text-sm font-medium">
                  Confirm new password
                </label>
                <Input
                  id="confirm-password"
                  type="password"
                  value={pw.confirm}
                  onChange={(e) => setPw((p) => ({ ...p, confirm: e.target.value }))}
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={busy}>
                <KeyRound className="size-3.5" />
                {busy ? "Updating..." : "Update password"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Sessions</CardTitle>
          <CardDescription>
            Invalidates your session on every other device. Because the backend
            invalidates all issued tokens, you'll be signed out on this device
            too and need to log in again.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={() => setLogoutAllOpen(true)}>
            <LogOut className="size-3.5" />
            Log out of all other devices
          </Button>
        </CardContent>
      </Card>

      <Dialog open={logoutAllOpen} onOpenChange={setLogoutAllOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Log out of all devices?</DialogTitle>
            <DialogDescription>
              This signs you out of every session, including this one. You'll need
              to log in again.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setLogoutAllOpen(false)}
              disabled={loggingOutAll}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleLogoutAll}
              disabled={loggingOutAll}
            >
              <Check className="size-3.5" />
              {loggingOutAll ? "Signing out..." : "Log out of all devices"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ─── Settings page ─────────────────────────────────────────────────────

export default function Settings() {
  const navigate = useNavigate();

  const handleSessionEnd = (message) => {
    navigate("/login", { state: { message } });
  };

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        icon={Settings2}
        accent="var(--brand)"
        eyebrow="Account & preferences"
        title="Settings"
        description="Manage your account, security, and data."
      />

      <Tabs defaultValue="account" orientation="vertical" className="flex gap-6">
        <TabsList
          variant="line"
          className="w-44 shrink-0 flex-col items-start gap-1 self-start"
        >
          <TabsTrigger
            value="account"
            className="w-full justify-start gap-2.5 rounded-xl px-3.5 py-2.5"
          >
            <User className="size-4" />
            Account
          </TabsTrigger>
          <TabsTrigger
            value="security"
            className="w-full justify-start gap-2.5 rounded-xl px-3.5 py-2.5"
          >
            <Shield className="size-4" />
            Security
          </TabsTrigger>
        </TabsList>

        <TabsContent value="account" className="min-w-0 flex-1">
          <AccountTab onSessionEnd={handleSessionEnd} />
        </TabsContent>
        <TabsContent value="security" className="min-w-0 flex-1">
          <SecurityTab onSessionEnd={handleSessionEnd} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
