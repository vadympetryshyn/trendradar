import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const SITE_PASSWORD = process.env.SITE_PASSWORD;

export function middleware(request: NextRequest) {
  // Skip all auth checks in development
  if (process.env.NODE_ENV === "development") {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;

  // Site-wide password gate (production only, when SITE_PASSWORD is set)
  if (SITE_PASSWORD && pathname !== "/gate") {
    const sitePass = request.cookies.get("site_password")?.value;
    if (sitePass !== SITE_PASSWORD) {
      const url = new URL("/gate", request.url);
      if (sitePass) url.searchParams.set("error", "1");
      return NextResponse.redirect(url);
    }
  }

  // Only protect /admin routes beyond this point
  if (!pathname.startsWith("/admin")) {
    return NextResponse.next();
  }

  const token = request.cookies.get("auth_token")?.value;

  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Decode JWT payload (no verification - just read claims)
  try {
    const parts = token.split(".");
    if (parts.length !== 3) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
    const payload = JSON.parse(atob(parts[1]));

    // Check expiry
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      return NextResponse.redirect(new URL("/login", request.url));
    }

    // Check admin role
    if (!payload.is_admin) {
      return NextResponse.redirect(new URL("/", request.url));
    }
  } catch {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
