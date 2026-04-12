"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Layers } from "lucide-react";
import { toast } from "sonner";
import { Text } from "@/components/common/text";

export default function OAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleOAuthCallback = (): void => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const errorParam = searchParams.get("error");
      const errorDescription = searchParams.get("error_description");

      if (errorParam) {
        const errorMessage = errorDescription || errorParam;

        setError(errorMessage);
        toast.error("OAuth login failed", { description: errorMessage });

        setTimeout(() => router.replace("/login"), 3000);
        return;
      }

      if (!code || !state) {
        const errorMessage = "Missing authorization code or state.";

        setError(errorMessage);
        toast.error(errorMessage);

        setTimeout(() => router.replace("/login"), 3000);
        return;
      }
      const backendUrl =
        process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      window.location.href = `${backendUrl}/api/oauth/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`;
    };
    handleOAuthCallback();
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <Layers className="h-10 w-10 text-destructive" />
        <div className="flex flex-col items-center gap-2">
          <Text
            value={error || "OAuth login failed"}
            className="text-destructive font-semibold"
          />
          <Text
            value="Please try again or contact support if the issue persists."
            className="text-muted-foreground"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <Layers className="h-10 w-10 animate-pulse text-primary" />
      <div className="flex flex-col items-center gap-2">
        <Text
          value="OAuth login successful"
          className="text-primary font-semibold"
        />
        <Text
          value="Completing sign-in with Authentik…"
          className="text-muted-foreground"
        />
      </div>
    </div>
  );
}
