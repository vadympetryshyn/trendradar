"use client";

import { useEffect, useState } from "react";
import { getRegistrationStatus } from "@/lib/auth-api";

export function useRegistrationStatus() {
  const [registrationEnabled, setRegistrationEnabled] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getRegistrationStatus()
      .then((data) => setRegistrationEnabled(data.registration_enabled))
      .catch(() => setRegistrationEnabled(false))
      .finally(() => setIsLoading(false));
  }, []);

  return { registrationEnabled, isLoading };
}
