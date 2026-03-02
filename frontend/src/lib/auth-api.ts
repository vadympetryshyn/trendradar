import { fetchApi } from "./api";
import type { UserResponse } from "./types";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

interface MessageResponse {
  message: string;
}

interface RegistrationStatusResponse {
  registration_enabled: boolean;
}

export function getRegistrationStatus(): Promise<RegistrationStatusResponse> {
  return fetchApi("/api/v1/auth/registration-status", { skipAuth: true });
}

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const body = new URLSearchParams({ username: email, password });
  return fetchApi("/api/v1/auth/login", {
    method: "POST",
    body: body.toString(),
    formUrlEncoded: true,
  });
}

export function register(data: {
  email: string;
  name?: string;
  password: string;
  password_confirm: string;
}): Promise<UserResponse> {
  return fetchApi("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
    skipAuth: true,
  });
}

export function googleAuth(token: string): Promise<TokenResponse> {
  return fetchApi("/api/v1/auth/google", {
    method: "POST",
    body: JSON.stringify({ token }),
    skipAuth: true,
  });
}

export function getMe(): Promise<UserResponse> {
  return fetchApi("/api/v1/auth/me");
}

export function forgotPassword(email: string): Promise<MessageResponse> {
  return fetchApi("/api/v1/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
    skipAuth: true,
  });
}

export function resetPassword(
  token: string,
  password: string,
  password_confirm: string
): Promise<MessageResponse> {
  return fetchApi("/api/v1/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, password, password_confirm }),
    skipAuth: true,
  });
}

export function verifyEmail(token: string): Promise<MessageResponse> {
  return fetchApi(`/api/v1/auth/verify-email/${token}`, { skipAuth: true });
}

export function resendVerification(email: string): Promise<MessageResponse> {
  return fetchApi("/api/v1/auth/resend-verification", {
    method: "POST",
    body: JSON.stringify({ email }),
    skipAuth: true,
  });
}

export function updateProfile(name: string): Promise<UserResponse> {
  return fetchApi("/api/v1/auth/profile", {
    method: "PUT",
    body: JSON.stringify({ name }),
  });
}

export function changePassword(
  current_password: string,
  new_password: string,
  new_password_confirm: string
): Promise<MessageResponse> {
  return fetchApi("/api/v1/auth/change-password", {
    method: "PUT",
    body: JSON.stringify({
      current_password,
      new_password,
      new_password_confirm,
    }),
  });
}

export function setPassword(
  new_password: string,
  new_password_confirm: string
): Promise<MessageResponse> {
  return fetchApi("/api/v1/auth/set-password", {
    method: "PUT",
    body: JSON.stringify({ new_password, new_password_confirm }),
  });
}

export function deleteAccount(): Promise<void> {
  return fetchApi("/api/v1/auth/account", { method: "DELETE" });
}

export function logout(): void {
  localStorage.removeItem("auth_token");
  document.cookie = "auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
}
