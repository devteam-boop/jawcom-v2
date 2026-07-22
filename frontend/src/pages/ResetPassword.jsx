import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";
import { authService } from "@/services/auth";

export default function ResetPassword() {
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState(location.state?.email || "");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (submitting) return;
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await authService.resetPassword({ email, otp, newPassword });
      setDone(true);
    } catch (err) {
      setError(err.message || "Could not reset password");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-background px-4 text-foreground">
      <Card className="w-full max-w-sm rounded-xl border-border bg-card p-8 shadow-sm">
        <div className="mb-6">
          <h1 className="text-lg font-bold">Reset password</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Enter the code your administrator relayed to you, then choose a new password.
          </p>
        </div>

        {done ? (
          <div className="space-y-4">
            <p className="text-sm" data-testid="reset-password-done">
              Your password has been reset. You can now sign in.
            </p>
            <Button className="w-full" onClick={() => navigate("/login", { replace: true })}>
              Go to sign in
            </Button>
          </div>
        ) : (
          <form className="space-y-4" onSubmit={handleSubmit} data-testid="reset-password-form">
            <div className="space-y-1.5">
              <Label htmlFor="rp-email">Email</Label>
              <Input
                id="rp-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                data-testid="reset-password-email"
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label>6-digit code</Label>
              <InputOTP maxLength={6} value={otp} onChange={setOtp} data-testid="reset-password-otp">
                <InputOTPGroup>
                  {[0, 1, 2, 3, 4, 5].map((i) => (
                    <InputOTPSlot key={i} index={i} />
                  ))}
                </InputOTPGroup>
              </InputOTP>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="rp-new">New password</Label>
              <Input
                id="rp-new"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                data-testid="reset-password-new"
                required
              />
              <p className="text-xs text-muted-foreground">
                12+ characters, with upper, lower, number and special character.
              </p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="rp-confirm">Confirm new password</Label>
              <Input
                id="rp-confirm"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                data-testid="reset-password-confirm"
                required
              />
            </div>

            {error && <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>}

            <Button type="submit" className="w-full" disabled={submitting || otp.length !== 6} data-testid="reset-password-submit">
              {submitting ? "Resetting…" : "Reset password"}
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
