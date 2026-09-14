"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../../../lib/api";

const GATES = [
  "initial_copy",
  "replication",
  "catch_up",
  "lag_zero",
  "transactions_zero",
  "sequences_synced",
  "validation",
  "health_check",
  "epoch_increment",
  "routing_switched",
];

export default function MoveTenant() {
  const { id } = useParams();
  const router = useRouter();
  const [cells, setCells] = useState([]);
  const [tenant, setTenant] = useState(null);
  const [target, setTarget] = useState("");
  const [reason, setReason] = useState("cell capacity / noisy neighbour");
  const [result, setResult] = useState(null);

  useEffect(() => {
    api(`/v1/tenants/${id}`).then(setTenant);
    api("/v1/cells").then((c) => {
      setCells(c);
      const other = c.find((x) => x.kind === "pooled");
      if (other) setTarget(other.cell_id);
    });
  }, [id]);

  async function start() {
    const r = await api(`/v1/tenants/${id}/move`, {
      method: "POST",
      body: JSON.stringify({ target_cell_id: target, reason }),
    });
    setResult(r);
  }

  if (!tenant) return <p>Loading…</p>;

  return (
    <>
      <h1>Move tenant</h1>
      <p className="sub">
        {tenant.name} · from {tenant.cell_id}. Mechanism: validated dump/restore + cutover commit (not logical
        replication on this host).
      </p>
      <div className="panel" style={{ display: "grid", gap: 12, maxWidth: 480 }}>
        <label>
          Target cell
          <select value={target} onChange={(e) => setTarget(e.target.value)}>
            {cells.map((c) => (
              <option key={c.cell_id} value={c.cell_id}>
                {c.name} ({c.kind})
              </option>
            ))}
          </select>
        </label>
        <label>
          Reason
          <input value={reason} onChange={(e) => setReason(e.target.value)} />
        </label>
        <button className="btn" onClick={start}>
          Start move
        </button>
      </div>
      {result && (
        <div className="panel">
          <div className="steps">
            {GATES.map((g) => (
              <div key={g} className={result.move_gates?.[g] ? "ok" : ""}>
                {g} {result.move_gates?.[g] ? "✓" : ""}
              </div>
            ))}
          </div>
          <p>{result.move_committed ? "MOVE COMPLETE" : "SOURCE REMAINS AUTHORITATIVE"}</p>
          <button className="btn" onClick={() => router.push(`/tenants/${id}`)}>
            Back to tenant
          </button>
        </div>
      )}
    </>
  );
}
