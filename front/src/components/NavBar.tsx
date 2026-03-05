"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";

export function NavBar() {
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  if (pathname === "/gate") return null;

  return (
    <nav className="border-b bg-background">
      <div className="container mx-auto flex h-14 items-center px-4 gap-4">
        <Link href="/" className="font-bold text-lg shrink-0">
          TrendRadar
        </Link>

        {/* Desktop nav */}
        <div className="hidden sm:flex gap-4 text-sm items-center">
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
        <div className="hidden sm:flex ml-auto items-center gap-3">
          {!isLoading && (
            <>
              {isAuthenticated ? (
                <>
                  <span className="text-sm text-muted-foreground truncate max-w-[200px]">
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

        {/* Mobile hamburger */}
        <button
          className="sm:hidden ml-auto p-2 text-muted-foreground hover:text-foreground"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="sm:hidden border-t px-4 py-3 space-y-3">
          <div className="flex flex-col gap-2 text-sm">
            <Link
              href="/"
              onClick={() => setMenuOpen(false)}
              className="text-muted-foreground hover:text-foreground transition-colors py-1"
            >
              Home
            </Link>
            {isAuthenticated && user?.is_admin && (
              <Link
                href="/admin"
                onClick={() => setMenuOpen(false)}
                className="text-muted-foreground hover:text-foreground transition-colors py-1"
              >
                Admin
              </Link>
            )}
          </div>
          {!isLoading && (
            <div className="flex items-center gap-3 pt-2 border-t">
              {isAuthenticated ? (
                <>
                  <span className="text-sm text-muted-foreground truncate">
                    {user?.email}
                  </span>
                  <Button variant="ghost" size="sm" onClick={() => { logout(); setMenuOpen(false); }}>
                    Logout
                  </Button>
                </>
              ) : (
                <Link href="/login" onClick={() => setMenuOpen(false)}>
                  <Button variant="ghost" size="sm">
                    Login
                  </Button>
                </Link>
              )}
            </div>
          )}
        </div>
      )}
    </nav>
  );
}
