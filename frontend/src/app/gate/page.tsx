"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

function GateForm() {
  const searchParams = useSearchParams();
  const hasError = searchParams.get("error") === "1";
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    document.cookie = `site_password=${encodeURIComponent(password)}; path=/; max-age=${60 * 60 * 24 * 30}; SameSite=Lax`;
    window.location.href = "/";
  };

  return (
    <div className="flex items-center justify-center py-20">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-bold">Access Required</h1>
          <p className="text-sm text-muted-foreground">
            Enter password to access the site
          </p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
          />
          {hasError && (
            <p className="text-sm text-destructive">Wrong password</p>
          )}
          <Button type="submit" className="w-full">
            Enter
          </Button>
        </form>
      </div>
    </div>
  );
}

export default function GatePage() {
  return (
    <Suspense>
      <GateForm />
    </Suspense>
  );
}
