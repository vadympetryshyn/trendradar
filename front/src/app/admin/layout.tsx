"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useEffect } from "react";

const NAV_ITEMS = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/trends", label: "Trends" },
  { href: "/admin/tasks", label: "Tasks" },
  { href: "/admin/schedules", label: "Scheduler" },
  { href: "/admin/metrics", label: "Server Metrics" },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && (!isAuthenticated || !user?.is_admin)) {
      router.replace(isAuthenticated ? "/" : "/login");
    }
  }, [isLoading, isAuthenticated, user, router]);

  const isActive = (href: string) =>
    href === "/admin" ? pathname === "/admin" : pathname.startsWith(href);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user?.is_admin) {
    return null;
  }

  return (
    <div className="flex flex-col md:flex-row gap-6">
      <nav className="flex md:flex-col md:w-[220px] md:shrink-0 gap-1 overflow-x-auto">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`block rounded-md px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors ${
              isActive(item.href)
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground"
            }`}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  );
}
