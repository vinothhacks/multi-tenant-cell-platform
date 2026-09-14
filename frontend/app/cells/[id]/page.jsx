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
  if (!c) return <p className="lede">Reading cell…</p>;
  const mix = c.size_mix || {};
  const tenantCount = Array.isArray(c.tenants) ? c.tenants.length : c.tenants || 0;
  const mixCount = (key) => {
    const v = mix[key];
    if (typeof v === "number") return v;
    if (Array.isArray(v)) return v.length;
    return 0;
  };
  return (
    <>
      <p className="index">02 — {c.kind}</p>
      <h1 className="display">{c.name}</h1>
      <p className="lede">
        Release {c.release} · {c.region}. Split and scale stay labelled simulations. Move is real.
      </p>
      <div className="kpis">
        {[
          ["CPU", `${c.cpu}%`],
          ["Memory", `${c.memory}%`],
          ["Connections", `${c.pg_connections}%`],
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
      <p className="sub">
        Tenants {tenantCount} · S/M/L {mixCount("S")}/{mixCount("M")}/{mixCount("L")} ·{" "}
        <span className={`badge ${c.health}`}>{c.health}</span>
      </p>
    </>
  );
}
