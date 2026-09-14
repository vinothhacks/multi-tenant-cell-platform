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

  if (!tenant) return <p className="lede">Preparing cutover…</p>;

  return (
    <>
      <p className="index">From {tenant.cell_id}</p>
      <h1 className="display">Move</h1>
      <p className="lede">
        {tenant.name}. Validated dump/restore, then a registry commit. Not logical replication on this host.
      </p>
      <div className="form">
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
        <div className="row">
          <button className="btn" onClick={start}>
            Start move
          </button>
        </div>
      </div>
      {result && (
        <div className="panel">
          <div className="steps">
            {GATES.map((g) => (
              <div key={g} className={result.move_gates?.[g] ? "ok" : ""}>
                {g.replaceAll("_", " ")} {result.move_gates?.[g] ? "—" : ""}
              </div>
            ))}
          </div>
          <p className="lede">{result.move_committed ? "Cutover complete." : "Source remains authoritative."}</p>
          <button className="btn" onClick={() => router.push(`/tenants/${id}`)}>
            Back →
          </button>
        </div>
      )}
    </>
  );
}
