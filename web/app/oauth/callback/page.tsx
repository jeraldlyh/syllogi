"use client";

import { OAuthCallback } from "@/components/oauth";
import { Suspense } from "react";

export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={<></>}>
      <OAuthCallback />
    </Suspense>
  );
}
