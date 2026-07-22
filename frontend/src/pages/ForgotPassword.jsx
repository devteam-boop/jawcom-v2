import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authService } from "@/services/auth";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await authService.forgotPassword(email);
      setDone(true);
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-background px-4 text-foreground">
      <Card className="w-full max-w-sm rounded-xl border-border bg-card p-8 shadow-sm">
        <div className="mb-6">
          <h1 className="text-lg font-bold">Forgot password</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Enter your registered email. A one-time code will be sent to your workspace
            administrator, who will relay it to you.
          </p>
        </div>

        {done ? (
          <div className="space-y-4">
            <p className="text-sm" data-testid="forgot-password-done">
              If that account exists, a reset code has been sent to the administrator. Ask them
              for the code, then continue to reset your password.
            </p>
            <Button className="w-full" onClick={() => navigate("/reset-password", { state: { email } })}>
              I have a code
            </Button>
          </div>
        ) : (
          <form className="space-y-4" onSubmit={handleSubmit} data-testid="forgot-password-form">
            <div className="space-y-1.5">
              <Label htmlFor="fp-email">Email</Label>
              <Input
                id="fp-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                data-testid="forgot-password-email"
                autoFocus
                required
              />
            </div>
            {error && <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>}
            <Button type="submit" className="w-full" disabled={submitting} data-testid="forgot-password-submit">
              {submitting ? "Sending…" : "Send reset code"}
            </Button>
          </form>
        )}

        <div className="mt-6 text-center text-sm">
          <Link to="/login" className="font-medium text-primary hover:underline">
            Back to sign in
          </Link>
        </div>
      </Card>
    </div>
  );
}
