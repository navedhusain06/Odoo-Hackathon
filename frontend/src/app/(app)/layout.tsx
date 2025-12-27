import Link from "next/link";
import { ReactNode } from "react";

import { Separator } from "@/components/ui/separator";

export default function AppLayout({ children }: { children: ReactNode }) {
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
        </div>
      </header>

      <Separator />

      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
