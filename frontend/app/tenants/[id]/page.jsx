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

  if (!t) return <p className="lede">Reading tenant…</p>;

  return (
    <>
      <p className="index">
        {t.isolation} · epoch {t.tenant_version}
      </p>
      <h1 className="display">{t.name}</h1>
      <p className="lede">
        {t.tier} on {t.cell_id}. {t.region}.
      </p>
      {msg && <p className="banner">{msg}</p>}
      <dl className="dl">
        <dt>Isolation</dt>
        <dd>{t.isolation}</dd>
        <dt>Tier</dt>
        <dd>{t.tier}</dd>
        <dt>Cell</dt>
        <dd>{t.cell_id}</dd>
        <dt>Database</dt>
        <dd>{t.database_name}</dd>
        <dt>Schema</dt>
        <dd>{t.schema_version}</dd>
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
        <dt>Store</dt>
        <dd>{t.components?.postgresql}</dd>
      </dl>
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
          Isolation
        </Link>
      </div>
    </>
  );
}
