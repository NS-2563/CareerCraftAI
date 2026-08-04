import { useEffect, useState } from "react";
import { User, Mail, CalendarDays, Pencil, X } from "lucide-react";
import PageHeader from "@/components/app/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import ProfileForm from "@/components/profile/ProfileForm";
import userApi from "@/services/userApi";
import { useAuth } from "@/context/useAuth";

function getInitials(name, email) {
  if (name?.trim()) {
    return name
      .trim()
      .split(/\s+/)
      .map((p) => p[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  }
  return (email?.[0] || "U").toUpperCase();
}

function formatMemberSince(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "long" });
}

export default function Profile() {
  const { user: authUser, refreshUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      const res = await userApi.getProfile();
      if (mounted) {
        if (res.success) setProfile(res.data);
        else setError(res.error || "Failed to load your profile.");
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
      setEditing(false);
      if (refreshUser) await refreshUser();
    } else {
      setFormError(res.error || "Failed to save your profile.");
    }
    setSaving(false);
  };

  const name =
    profile?.full_name || authUser?.full_name || profile?.username || authUser?.username || "";
  const email = profile?.email || authUser?.email || "";
  const username = profile?.username || authUser?.username || "";
  const picture = profile?.profile_picture || "";
  const memberSince = formatMemberSince(profile?.created_at);

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        icon={User}
        accent="var(--brand)"
        eyebrow="Account"
        title="Profile"
        description="Your identity across CareerCraft AI."
      />

      {loading ? (
        <div className="animate-pulse space-y-6">
          <div className="h-56 rounded-xl bg-muted/60" />
          <div className="h-40 rounded-xl bg-muted/60" />
        </div>
      ) : error ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Cover + identity header */}
          <Card className="overflow-hidden p-0">
            <div className="relative h-36 bg-gradient-to-br from-[color-mix(in_oklch,var(--brand)_40%,transparent)] via-[color-mix(in_oklch,var(--indigo)_30%,transparent)] to-[color-mix(in_oklch,var(--cyan)_20%,transparent)] sm:h-44">
              <div className="absolute inset-0 bg-[linear-gradient(to_right,color-mix(in_oklch,var(--border)_30%,transparent)_1px,transparent_1px),linear-gradient(to_bottom,color-mix(in_oklch,var(--border)_30%,transparent)_1px,transparent_1px)] bg-[size:40px_40px]" />
            </div>
            <div className="px-5 pb-6 sm:px-8">
              <div className="-mt-12 flex flex-col gap-4 sm:-mt-14 sm:flex-row sm:items-end sm:justify-between">
                <div className="flex items-end gap-4">
                  {picture ? (
                    <img
                      src={picture}
                      alt={name || "Profile"}
                      className="h-24 w-24 rounded-2xl border-4 border-background object-cover sm:h-28 sm:w-28"
                    />
                  ) : (
                    <div
                      className="flex h-24 w-24 shrink-0 items-center justify-center rounded-2xl border-4 border-background font-display text-2xl font-semibold text-background sm:h-28 sm:w-28"
                      style={{
                        background:
                          "linear-gradient(140deg, color-mix(in oklch, var(--brand) 90%, white 10%), color-mix(in oklch, var(--indigo) 80%, black))",
                      }}
                    >
                      {getInitials(name, email)}
                    </div>
                  )}
                  <div className="pb-1">
                    <h1 className="font-display text-2xl font-semibold tracking-tight">
                      {name || "Your name"}
                    </h1>
                    {username && (
                      <p className="text-sm text-muted-foreground">@{username}</p>
                    )}
                  </div>
                </div>
                {!editing && (
                  <Button
                    variant="outline"
                    className="self-start sm:self-auto"
                    onClick={() => setEditing(true)}
                  >
                    <Pencil className="size-3.5" />
                    Edit profile
                  </Button>
                )}
              </div>

              <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
                {email && (
                  <span className="inline-flex items-center gap-1.5">
                    <Mail className="size-4" /> {email}
                  </span>
                )}
                {memberSince && (
                  <span className="inline-flex items-center gap-1.5">
                    <CalendarDays className="size-4" /> Member since {memberSince}
                  </span>
                )}
              </div>
            </div>
          </Card>

          {/* Edit form */}
          {editing && (
            <Card className="mt-6">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>Edit profile</CardTitle>
                    <CardDescription>Update the details shown on your profile.</CardDescription>
                  </div>
                  <button
                    onClick={() => {
                      setEditing(false);
                      setFormError("");
                    }}
                    className="flex size-8 items-center justify-center rounded-lg hover:bg-accent"
                    aria-label="Cancel editing"
                  >
                    <X className="size-4" />
                  </button>
                </div>
              </CardHeader>
              <CardContent>
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
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
