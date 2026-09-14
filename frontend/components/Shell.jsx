"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Fleet", n: "01" },
  { href: "/cells", label: "Cells", n: "02" },
  { href: "/tenants/new", label: "Provision", n: "03" },
  { href: "/releases", label: "Releases", n: "04" },
  { href: "/operations", label: "Operations", n: "05" },
];

export default function Shell({ children }) {
  const path = usePathname();
  return (
    <div className="shell">
      <header className="top">
        <Link href="/" className="mark">
          CELL.<span>Platform</span>
        </Link>
        <nav className="nav" aria-label="Control plane">
          {LINKS.map((l) => {
            const on =
              l.href === "/"
                ? path === "/"
                : path === l.href || (l.href !== "/tenants/new" && path.startsWith(`${l.href}/`));
            return (
              <Link key={l.href} href={l.href} className={on ? "active" : ""}>
                <em>{l.n}</em>
                {l.label}
              </Link>
            );
          })}
        </nav>
      </header>
      <main className="stage">{children}</main>
      <footer className="foot">
        <span>O(N) → O(waves)</span>
        <span>Control plane</span>
        <span>Not a customer product</span>
      </footer>
    </div>
  );
}
