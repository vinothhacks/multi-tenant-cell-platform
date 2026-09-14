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
      <p className="index">02 — Topology</p>
      <h1 className="display">Cells</h1>
      <p className="lede">
        A cell is the unit of deploy, capacity, and blast radius. Control plane stays above the fold.
      </p>
      <p className="sub">Registry · Release engine · Secrets</p>
      <div className="topology">
        {cells.map((c, i) => (
          <Link key={c.cell_id} href={`/cells/${c.cell_id}`} className="cellcard">
            <p className="index">0{i + 1}</p>
            <h3>{c.name}</h3>
            <div>
              {c.tenants} tenants · {c.utilization_pct}%
            </div>
            <div className="bar">
              <span style={{ width: `${c.utilization_pct}%` }} />
            </div>
            <span className={`badge ${c.health}`}>{c.health}</span>
          </Link>
        ))}
      </div>
    </>
  );
}
