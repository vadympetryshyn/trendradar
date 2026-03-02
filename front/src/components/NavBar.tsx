"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";

export function NavBar() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto flex h-14 items-center px-4 gap-6">
        <Link href="/" className="font-bold text-lg">
          TrendRadar
        </Link>
        <div className="flex gap-4 text-sm items-center">
          <Link
            href="/"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            Home
          </Link>
          {isAuthenticated && user?.is_admin && (
            <Link
              href="/admin"
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              Admin
            </Link>
          )}
        </div>
        <div className="ml-auto flex items-center gap-3">
          {!isLoading && (
            <>
              {isAuthenticated ? (
                <>
                  <span className="text-sm text-muted-foreground">
                    {user?.email}
                  </span>
                  <Button variant="ghost" size="sm" onClick={logout}>
                    Logout
                  </Button>
                </>
              ) : (
                <Link href="/login">
                  <Button variant="ghost" size="sm">
                    Login
                  </Button>
                </Link>
              )}
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
