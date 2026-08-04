import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

function Field({ label, name, type = "text", value, onChange, required = false, placeholder, minLength, maxLength }) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={`profile-${name}`} className="text-sm font-medium">
        {label}
      </label>
      <Input
        id={`profile-${name}`}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        required={required}
        placeholder={placeholder}
        minLength={minLength}
        maxLength={maxLength}
      />
    </div>
  );
}

/**
 * Shared form for the four real editable profile fields
 * (full_name, username, email, profile_picture). Used by both the Profile
 * page's edit action and the Settings Account tab so there is a single
 * source of truth for the profile form.
 *
 * @param {{
 *   initialValues: { full_name?: string, username?: string, email?: string, profile_picture?: string }
 *   onSubmit: (values: { full_name: string, username: string, email: string, profile_picture: string }) => void
 *   busy?: boolean
 *   error?: string
 *   submitLabel?: string
 * }} props
 */
export default function ProfileForm({
  initialValues = {},
  onSubmit,
  busy = false,
  error = "",
  submitLabel = "Save changes",
}) {
  const [values, setValues] = useState({
    full_name: initialValues.full_name ?? "",
    username: initialValues.username ?? "",
    email: initialValues.email ?? "",
    profile_picture: initialValues.profile_picture ?? "",
  });

  const handleChange = (e) => {
    setValues((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(values);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          label="Full name"
          name="full_name"
          value={values.full_name}
          onChange={handleChange}
          maxLength={255}
          placeholder="Jordan Rivera"
        />
        <Field
          label="Username"
          name="username"
          value={values.username}
          onChange={handleChange}
          required
          minLength={3}
          maxLength={100}
          placeholder="jordan"
        />
      </div>

      <Field
        label="Email"
        name="email"
        type="email"
        value={values.email}
        onChange={handleChange}
        required
        maxLength={255}
        placeholder="you@example.com"
      />

      <Field
        label="Profile picture URL"
        name="profile_picture"
        type="url"
        value={values.profile_picture}
        onChange={handleChange}
        maxLength={2048}
        placeholder="https://..."
      />

      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={busy}>
          {busy ? "Saving..." : submitLabel}
        </Button>
      </div>
    </form>
  );
}
