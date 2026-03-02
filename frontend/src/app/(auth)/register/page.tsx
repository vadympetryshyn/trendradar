"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useRegistrationStatus } from "@/hooks/useRegistrationStatus";
import { RegisterForm } from "@/components/auth/RegisterForm";

export default function RegisterPage() {
  const { registrationEnabled, isLoading } = useRegistrationStatus();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !registrationEnabled) {
      router.replace("/login");
    }
  }, [isLoading, registrationEnabled, router]);

  if (isLoading || !registrationEnabled) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h1 className="text-xl font-semibold">Create an account</h1>
        <p className="text-sm text-muted-foreground">
          Enter your details to create a new account
        </p>
      </div>
      <RegisterForm />
    </div>
  );
}
