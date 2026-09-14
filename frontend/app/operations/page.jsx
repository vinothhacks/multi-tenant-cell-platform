"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function Operations() {
  const [econ, setEcon] = useState(null);
  const [obs, setObs] = useState(null);
  const [run, setRun] = useState(null);
  const [tenants, setTenants] = useState([]);
  const [chaos, setChaos] = useState(null);

  useEffect(() => {
    api("/v1/economics").then(setEcon);
    api("/v1/observability").then(setObs);
    api("/v1/tenants").then(setTenants);
  }, []);

  async function isolate() {
    const live = tenants.filter((t) => t.status === "active");
    const r = await api("/v1/isolation/run", {
      method: "POST",
      body: JSON.stringify({
        tenant_a: live[0]?.tenant_id,
        tenant_b: live[1]?.tenant_id,
      }),
    });
    setRun(r);
  }

  async function breakOne() {
    const live = tenants.filter((t) => t.status === "active");
    const r = await api("/v1/chaos/db-down", {
      method: "POST",
      body: JSON.stringify({ tenant_id: live[0]?.tenant_id }),
    });
    setChaos(r);
  }

  async function seed() {
    await api("/v1/synthetic/seed", { method: "POST", body: JSON.stringify({ count: 20, prefix: "syn" }) });
    setTenants(await api("/v1/tenants"));
  }

  return (
    <>
      <h1>Operations</h1>
      <p className="sub">Isolation verification, fleet health, chaos, and illustrative economics.</p>
      <div className="row">
        <button className="btn" onClick={seed}>
          Seed 20 tenants
        </button>
        <button className="btn ghost" onClick={isolate}>
          Run I1–I10
        </button>
        <button className="btn ghost" onClick={breakOne}>
          Break one tenant DB
        </button>
      </div>
      {run && (
        <div className="panel">
          <h3>Isolation verification {run.run_id?.slice(0, 8)}</h3>
          {Object.entries(run.results || {}).map(([k, v]) => (
            <div key={k} className={v === "PASS" ? "ok" : ""}>
              {k} {String(v)}
            </div>
          ))}
          {run.probe && (
            <p>
              Attempt {run.probe.attempt} → {run.probe.blocked ? "BLOCKED" : "ALLOWED"} ({run.probe.reason})
            </p>
          )}
        </div>
      )}
      {chaos && (
        <div className="panel">
          Degraded {chaos.degraded}. Others healthy: {String(chaos.others_healthy)} ({chaos.others} tenants).
        </div>
      )}
      {obs && (
        <div className="panel">
          <h3>Fleet health</h3>
          <p>
            Availability {obs.api_availability}% · p99 {obs.p99_latency_ms}ms · queue p95 {obs.queue_start_p95_s}s
          </p>
          {obs.cells.map((c) => (
            <div key={c.cell_id}>
              {c.cell_id}
              <div className="bar">
                <span style={{ width: `${c.utilization}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
      {econ && (
        <div className="panel">
          <h3>Economics</h3>
          <p className="sim">{econ.label}</p>
          <table>
            <thead>
              <tr>
                <th>N</th>
                <th>Silo</th>
                <th>Pooled</th>
              </tr>
            </thead>
            <tbody>
              {econ.rows.map((r) => (
                <tr key={r.n}>
                  <td>{r.n}</td>
                  <td>${r.silo.toLocaleString()}</td>
                  <td>${r.pooled.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
