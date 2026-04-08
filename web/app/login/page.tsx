"use client";
import { Text } from "@/components/common/text";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useSettings } from "@/hooks/useSettings";
import { api } from "@/lib/api";
import { Layers } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import { toast } from "sonner";

export default function LoginPage() {
  const { data } = useSettings();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

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

  const handlePasswordLogin = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    const response = await api({
      service: "auth",
      method: "POST",
      path: "login",
      formData,
    });

    if (response.statusCode === 200) {
      router.push("/");
    } else {
      toast.error("Login failed", {
        description: response.error?.message || "An unknown error occurred",
      });
    }
  };

  const handleOAuthLogin = (): void => {
    console.log("OAuth login clicked");
  };

  const renderAuthentikButton = (): React.JSX.Element | undefined => {
    if (!data || !data.isOAuthEnabled) return;

    return (
      <>
        <div className="my-6 flex items-center gap-3">
          <Separator className="flex-1" />
          <span className="text-xs text-muted-foreground">OR</span>
          <Separator className="flex-1" />
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={handleOAuthLogin}
          className="w-full h-10 gap-2"
        >
          <Layers />
          Sign in with Authentik
        </Button>
      </>
    );
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
              syllogi
            </h1>
            <Text
              className="text-muted-foreground"
              value="Unify your playlists with Jellyfin"
            />
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <form onSubmit={handlePasswordLogin} className="space-y-4">
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
                placeholder="Enter your username"
                className="h-10"
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
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="h-10"
              />
            </div>
            <Button type="submit" className="w-full h-10">
              Sign in
            </Button>
            {renderAuthentikButton()}
          </form>
        </div>
      </div>
    </div>
  );
}
