"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../../lib/api";

export default function TenantDetail() {
  const { id } = useParams();
  const [t, setT] = useState(null);
  const [msg, setMsg] = useState("");

  const load = () => api(`/v1/tenants/${id}`).then(setT);
  useEffect(() => {
    load();
  }, [id]);

  async function act(path) {
    const r = await api(path, { method: "POST", body: "{}" });
    setMsg(r.status || "ok");
    load();
  }

  if (!t) return <p>Loading tenant…</p>;

  return (
    <>
      <h1>Tenant: {t.name}</h1>
      <p className="sub">
        Isolation {t.isolation} · epoch {t.tenant_version} · {t.region}
      </p>
      <div className="dl panel">
        <dt>Isolation</dt>
        <dd>{t.isolation}</dd>
        <dt>Tier</dt>
        <dd>{t.tier}</dd>
        <dt>Cell</dt>
        <dd>{t.cell_id}</dd>
        <dt>Region</dt>
        <dd>{t.region}</dd>
        <dt>Database</dt>
        <dd>
          <code>{t.database_name}</code>
        </dd>
        <dt>Schema</dt>
        <dd>{t.schema_version}</dd>
        <dt>Tenant epoch</dt>
        <dd>{t.tenant_version}</dd>
        <dt>Status</dt>
        <dd>
          <span className={`badge ${t.status}`}>{t.status}</span>
        </dd>
        <dt>API</dt>
        <dd>{t.components?.api}</dd>
        <dt>Celery</dt>
        <dd>{t.components?.celery}</dd>
        <dt>Redis</dt>
        <dd>{t.components?.redis}</dd>
        <dt>PostgreSQL</dt>
        <dd>{t.components?.postgresql}</dd>
      </div>
      <div className="row">
        <Link className="btn" href={`/tenants/${id}/move`}>
          Move tenant
        </Link>
        <button className="btn ghost" onClick={() => act(`/v1/tenants/${id}/suspend`)}>
          Suspend
        </button>
        <button className="btn ghost" onClick={() => act(`/v1/tenants/${id}/resume`)}>
          Resume
        </button>
        <Link className="btn ghost" href="/operations">
          View audit / isolation
        </Link>
      </div>
      {msg && <p className="banner">{msg}</p>}
    </>
  );
}
