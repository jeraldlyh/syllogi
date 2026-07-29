import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SWRConfig } from "swr";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "sonner";
import { fetcher } from "@/lib/api";

import Page from "../app/page";
import LoginPage from "../app/login/page";
import SignupPage from "../app/signup/page";
import OAuthCallbackPage from "../app/oauth/callback/page";

import "../app/globals.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <SWRConfig
        value={{
          fetcher,
          revalidateOnFocus: true,
          dedupingInterval: 2000,
        }}
      >
        <TooltipProvider delayDuration={200}>
          <Routes>
            <Route path="/" element={<Page />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/oauth/callback" element={<OAuthCallbackPage />} />
          </Routes>
          <Toaster />
        </TooltipProvider>
      </SWRConfig>
    </BrowserRouter>
  </React.StrictMode>,
);
