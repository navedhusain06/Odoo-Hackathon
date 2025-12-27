"use client";

import Link from "next/link";
import { ReactNode, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type Me = {
  id: number;
  name: string;
  email: string;
  role: string;
  avatar_url?: string | null;
};

export default function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    api<Me>("/auth/me")
      .then(setMe)
      .catch(() => {
        clearToken();
        router.replace("/login");
      });
  }, [router]);

  const logout = () => {
    clearToken();
    router.replace("/login");
  };

  if (!me) {
    return <div className="p-6 text-sm text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link href="/requests" className="font-semibold">
            GearGuard
          </Link>

          <nav className="flex items-center gap-4 text-sm text-muted-foreground">
            <Link href="/requests" className="hover:text-foreground">
              Requests
            </Link>
            <Link href="/calendar" className="hover:text-foreground">
              Calendar
            </Link>
            <Link href="/equipment" className="hover:text-foreground">
              Equipment
            </Link>
          </nav>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-9 px-2">
                <Avatar className="h-7 w-7">
                  {me.avatar_url ? (
                    <AvatarImage src={me.avatar_url} alt={me.name} />
                  ) : null}
                  <AvatarFallback>
                    {me.name
                      .split(" ")
                      .map((n) => n[0] || "")
                      .join("")
                      .slice(0, 2)
                      .toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <span className="ml-2 text-sm text-foreground">{me.name}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel className="text-xs">
                {me.email} · {me.role}
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onSelect={logout}>Logout</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <Separator />
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
