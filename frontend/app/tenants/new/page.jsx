"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "../../../lib/api";

const STEPS = [
  "requested",
  "provisioning",
  "database_ready",
  "schema_ready",
  "secrets_ready",
  "routing_ready",
  "active",
];

export default function CreateTenant() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "Acme Logistics",
    isolation: "L1",
    region: "Chennai",
    size_class: "S",
    contract: "standard",
  });
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    const t = await api("/v1/tenants", { method: "POST", body: JSON.stringify(form) });
    setResult(t);
    setBusy(false);
  }

  return (
    <>
      <h1>Create tenant</h1>
      <p className="sub">Controller reconciles requested → active. Each step is idempotent.</p>
      <form className="panel" onSubmit={submit} style={{ display: "grid", gap: 12, maxWidth: 480 }}>
        <label>
          Company name
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </label>
        <label>
          Isolation class
          <select value={form.isolation} onChange={(e) => setForm({ ...form, isolation: e.target.value })}>
            <option>L1</option>
            <option>L2</option>
            <option>L3</option>
          </select>
        </label>
        <label>
          Region
          <input value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value })} />
        </label>
        <label>
          Size class
          <select value={form.size_class} onChange={(e) => setForm({ ...form, size_class: e.target.value })}>
            <option>S</option>
            <option>M</option>
            <option>L</option>
            <option>XL</option>
          </select>
        </label>
        <label>
          Contract
          <input value={form.contract} onChange={(e) => setForm({ ...form, contract: e.target.value })} />
        </label>
        <button className="btn" disabled={busy} type="submit">
          {busy ? "Creating…" : "Create"}
        </button>
      </form>
      {result && (
        <div className="panel">
          <div className="steps">
            {STEPS.map((s) => (
              <div key={s} className={result.completed_steps?.includes(s) || result.status === "active" ? "ok" : ""}>
                {s.toUpperCase()} {result.status === "active" || result.completed_steps?.includes(s) ? "✓" : ""}
              </div>
            ))}
          </div>
          <p>
            Provisioning time: {result.provisioning_seconds}s · Cell: {result.cell_id} · Database:{" "}
            <code>{result.database_name}</code> · Release: {result.schema_version}
          </p>
          <button className="btn" onClick={() => router.push(`/tenants/${result.tenant_id}`)}>
            Open tenant
          </button>
        </div>
      )}
    </>
  );
}
