"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "@/lib/auth-api";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Invalid verification link.");
      return;
    }

    verifyEmail(token)
      .then(() => {
        setStatus("success");
        setMessage("Your email has been verified successfully!");
      })
      .catch((err) => {
        setStatus("error");
        setMessage(
          err instanceof Error ? err.message : "Verification failed."
        );
      });
  }, [token]);

  return (
    <div className="text-center space-y-4">
      {status === "loading" && (
        <>
          <h1 className="text-xl font-semibold">Verifying email...</h1>
          <p className="text-sm text-muted-foreground">Please wait...</p>
        </>
      )}
      {status === "success" && (
        <>
          <h1 className="text-xl font-semibold">Email verified</h1>
          <p className="text-sm text-muted-foreground">{message}</p>
          <Link
            href="/login"
            className="inline-block text-sm text-foreground hover:underline"
          >
            Sign in
          </Link>
        </>
      )}
      {status === "error" && (
        <>
          <h1 className="text-xl font-semibold">Verification failed</h1>
          <p className="text-sm text-destructive">{message}</p>
          <Link
            href="/login"
            className="inline-block text-sm text-foreground hover:underline"
          >
            Back to login
          </Link>
        </>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyEmailContent />
    </Suspense>
  );
}
