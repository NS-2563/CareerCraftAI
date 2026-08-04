import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/useAuth";
import InputField from "@/components/common/InputField";
import { AuthLayout } from "@/components/auth/AuthLayout";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Mail, Lock, User, AlertCircle, ArrowRight } from "lucide-react";

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, error, clearError, isLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [localError, setLocalError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError("");
    clearError();

    if (!email || !username || !password || !confirmPassword) {
      setLocalError("Please fill in all fields");
      return;
    }

    if (password !== confirmPassword) {
      setLocalError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setLocalError("Password must be at least 8 characters");
      return;
    }

    try {
      await register(email, username, password);
      navigate("/", { replace: true });
    } catch (err) {
      setLocalError(err.message);
    }
  };

  return (
    <AuthLayout>
      <h1 className="font-display text-3xl font-semibold tracking-tight">Create your account</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Start crafting your career story today.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-4">
        {(localError || error) && (
          <Alert variant="destructive">
            <AlertCircle className="size-4" />
            <AlertDescription>{localError || error}</AlertDescription>
          </Alert>
        )}

        <InputField
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          placeholder="you@example.com"
          required
          autoComplete="email"
          icon={Mail}
          inputClassName="rounded-xl bg-card/60 h-11"
        />

        <InputField
          label="Username"
          type="text"
          value={username}
          onChange={setUsername}
          placeholder="johndoe"
          required
          autoComplete="username"
          icon={User}
          inputClassName="rounded-xl bg-card/60 h-11"
        />

        <InputField
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="At least 8 characters"
          required
          autoComplete="new-password"
          icon={Lock}
          inputClassName="rounded-xl bg-card/60 h-11"
        />

        <InputField
          label="Confirm Password"
          type="password"
          value={confirmPassword}
          onChange={setConfirmPassword}
          placeholder="Confirm your password"
          required
          autoComplete="new-password"
          icon={Lock}
          inputClassName="rounded-xl bg-card/60 h-11"
        />

        <Button type="submit" variant="brand" size="lg" className="mt-2 w-full" disabled={isLoading}>
          {isLoading ? "Creating account..." : "Create account"}
          {!isLoading && <ArrowRight className="size-4" />}
        </Button>
      </form>

      <p className="mt-8 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-[var(--emerald)] hover:underline">
          Sign in
        </Link>
      </p>
    </AuthLayout>
  );
}

export default RegisterPage;
