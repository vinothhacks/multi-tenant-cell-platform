"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "../lib/api";

export default function FleetPage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api("/v1/fleet")
      .then(setData)
      .catch((e) => setErr(String(e.message || e)));
  }, []);

  if (err) {
    return (
      <>
        <p className="index">01 — Registry</p>
        <h1 className="display">Fleet</h1>
        <p className="banner">Backend unreachable. {err}</p>
      </>
    );
  }
  if (!data) return <p className="lede">Composing the registry…</p>;

  return (
    <>
      <p className="index">01 — Registry</p>
      <h1 className="display">Fleet</h1>
      <p className="lede">
        Tenants are partitions. The registry is source of truth. Operations scale as waves, not as N.
      </p>
      <div className="kpis">
        {[
          ["Total", data.total_tenants],
          ["Pooled", data.pooled],
          ["Dedicated", data.dedicated],
          ["Cells", data.cells],
          ["Healthy", data.healthy],
          ["Release", data.fleet_release],
        ].map(([l, v]) => (
          <div className="kpi" key={String(l)}>
            <div className="l">{l}</div>
            <div className="v">{v}</div>
          </div>
        ))}
      </div>
      <div className="row">
        <Link className="btn" href="/tenants/new">
          + Create tenant
        </Link>
      </div>
      <table>
        <thead>
          <tr>
            <th>Tenant</th>
            <th>Tier</th>
            <th>Cell</th>
            <th>Database</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.tenants.map((t) => (
            <tr key={t.tenant_id}>
              <td>
                <Link href={`/tenants/${t.tenant_id}`}>{t.name}</Link>
              </td>
              <td>{t.tier}</td>
              <td>{t.cell_id}</td>
              <td>
                <code>{t.database_name}</code>
              </td>
              <td>
                <span className={`badge ${t.status}`}>{t.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
