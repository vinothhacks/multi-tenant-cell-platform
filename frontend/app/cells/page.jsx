"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function CellsPage() {
  const [cells, setCells] = useState([]);
  useEffect(() => {
    api("/v1/cells").then(setCells);
  }, []);

  return (
    <>
      <h1>Cell topology</h1>
      <p className="sub">Cells are the unit of deployment, capacity, and failure containment.</p>
      <div className="panel">
        <strong>CONTROL PLANE</strong>
        <div style={{ color: "var(--muted)", margin: "8px 0 16px" }}>Registry · Release engine · Secrets</div>
      </div>
      <div className="topology">
        {cells.map((c) => (
          <Link key={c.cell_id} href={`/cells/${c.cell_id}`} className="cellcard">
            <h3>{c.name}</h3>
            <div>
              {c.tenants} tenants · {c.utilization_pct}% capacity
            </div>
            <div className="bar">
              <span style={{ width: `${c.utilization_pct}%` }} />
            </div>
            <div className="sub">Django · Celery · Redis · PgBouncer · PostgreSQL</div>
            <span className={`badge ${c.health}`}>{c.health}</span>
          </Link>
        ))}
      </div>
    </>
  );
}
