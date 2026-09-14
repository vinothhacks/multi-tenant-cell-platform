"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../../lib/api";

export default function CellDetail() {
  const { id } = useParams();
  const [c, setC] = useState(null);
  useEffect(() => {
    api(`/v1/cells/${id}`).then(setC);
  }, [id]);
  if (!c) return <p>Loading cell…</p>;
  const mix = c.size_mix || {};
  return (
    <>
      <h1>{c.name}</h1>
      <p className="sub">
        Release {c.release} · {c.kind} · {c.region}
      </p>
      <div className="kpis">
        {[
          ["CPU", `${c.cpu}%`],
          ["Memory", `${c.memory}%`],
          ["PG connections", `${c.pg_connections}%`],
          ["IOPS", `${c.iops}%`],
          ["Redis", `${c.redis}%`],
          ["Celery", `${c.celery}%`],
        ].map(([l, v]) => (
          <div className="kpi" key={String(l)}>
            <div className="l">{l}</div>
            <div className="v">{v}</div>
          </div>
        ))}
      </div>
      <p>
        Tenants {c.tenants} · S/M/L {mix.S || 0}/{mix.M || 0}/{mix.L || 0} ·{" "}
        <span className={`badge ${c.health}`}>{c.health}</span>
      </p>
      <p className="sim">Split Cell / Scale are labelled simulations in v1. Move Tenant is real.</p>
    </>
  );
}
