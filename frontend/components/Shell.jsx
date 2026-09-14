"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Fleet" },
  { href: "/cells", label: "Cells" },
  { href: "/tenants/new", label: "Provision" },
  { href: "/releases", label: "Releases" },
  { href: "/operations", label: "Operations" },
];

export default function Shell({ children }) {
  const path = usePathname();
  return (
    <div className="shell">
      <nav className="nav" aria-label="Control plane">
        <p className="brand">CELL PLATFORM</p>
        {LINKS.map((l) => (
          <Link key={l.href} href={l.href} className={path === l.href ? "active" : ""}>
            {l.label}
          </Link>
        ))}
      </nav>
      <main className="main">{children}</main>
    </div>
  );
}
