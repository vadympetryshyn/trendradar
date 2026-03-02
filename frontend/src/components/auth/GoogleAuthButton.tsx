"use client";

import { GoogleOAuthProvider, GoogleLogin } from "@react-oauth/google";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

interface GoogleAuthButtonProps {
  onSuccess: (token: string) => void;
  onError?: () => void;
}

function GoogleLoginInner({ onSuccess, onError }: GoogleAuthButtonProps) {
  return (
    <GoogleLogin
      onSuccess={(response) => {
        if (response.credential) {
          onSuccess(response.credential);
        }
      }}
      onError={() => onError?.()}
      theme="filled_black"
      size="large"
      width="100%"
      text="continue_with"
    />
  );
}

export function GoogleAuthButton(props: GoogleAuthButtonProps) {
  if (!GOOGLE_CLIENT_ID) return null;

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <GoogleLoginInner {...props} />
    </GoogleOAuthProvider>
  );
}
