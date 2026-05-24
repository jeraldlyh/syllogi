"use client";

import { Text } from "@/components/common/text";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import { toast } from "sonner";

export default function SignupPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [confirmError, setConfirmError] = useState("");

  useEffect(() => {
    const redirect = async (): Promise<void> => {
      const response = await api({
        method: "GET",
        service: "auth",
        path: "me",
      });

      if (response.data && response.statusCode === 200) {
        router.push("/");
      }
    };

    redirect();
  }, [router]);

  const handleConfirmPasswordChange = (
    e: React.ChangeEvent<HTMLInputElement>,
  ): void => {
    const value = e.target.value;

    setConfirmPassword(value);
    if (value && value !== password) {
      setConfirmError("Passwords do not match");
    } else {
      setConfirmError("");
    }
  };

  const handlePasswordChange = (
    e: React.ChangeEvent<HTMLInputElement>,
  ): void => {
    const value = e.target.value;
    setPassword(value);
    if (confirmPassword && confirmPassword !== value) {
      setConfirmError("Passwords do not match");
    } else {
      setConfirmError("");
    }
  };

  const handleRegister = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    if (!username.trim()) {
      toast.error("Username is required");
      return;
    }

    if (!password) {
      toast.error("Password is required");
      return;
    }

    if (password !== confirmPassword) {
      setConfirmError("Passwords do not match");
      return;
    }

    setIsLoading(true);

    const response = await api({
      method: "POST",
      service: "auth",
      path: "register",
      body: { username: username.trim(), password },
    });

    setIsLoading(false);

    if (response.statusCode === 200) {
      router.push("/");
    } else {
      toast.error("Registration failed", {
        description: response.error?.message || "An unknown error occurred",
      });
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center gap-3">
          <Image
            src="/icon.png"
            alt="syllogi logo"
            width={64}
            height={64}
            className="rounded-xl bg-purple-600/10 p-2"
          />
          <div className="text-center">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">
              Create your account
            </h1>
            <Text
              className="text-muted-foreground"
              value="Start syncing your playlists with Jellyfin"
            />
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <form onSubmit={handleRegister} className="space-y-4">
            <div className="space-y-2">
              <Label
                htmlFor="username"
                className="text-sm text-muted-foreground"
              >
                Username
              </Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Choose a username"
                className="h-10"
                autoComplete="username"
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <Label
                htmlFor="password"
                className="text-sm text-muted-foreground"
              >
                Password
              </Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={handlePasswordChange}
                placeholder="Choose a password"
                className="h-10"
              />
            </div>

            <div className="space-y-2">
              <Label
                htmlFor="confirm-password"
                className="flex items-center justify-between text-sm"
              >
                <span className="text-muted-foreground">Confirm password</span>
                {confirmError && (
                  <span className="text-xs text-destructive">
                    {confirmError}
                  </span>
                )}
              </Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={handleConfirmPasswordChange}
                placeholder="Confirm your password"
                className={cn("h-10", {
                  "border-destructive focus-visible:ring-destructive":
                    confirmError,
                })}
              />
            </div>

            <Button
              type="submit"
              className="w-full h-10"
              disabled={isLoading || !!confirmError}
            >
              {isLoading ? "Creating account..." : "Create account"}
            </Button>
          </form>
        </div>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?&nbsp;
          <Link
            href="/login"
            className="font-medium text-foreground underline-offset-4 hover:underline hover:text-primary transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
