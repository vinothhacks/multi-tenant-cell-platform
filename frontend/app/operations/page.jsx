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
      <p className="index">05 — Proof</p>
      <h1 className="display">Operations</h1>
      <p className="lede">Isolation, chaos, and a labelled cost model. Break one tenant. Watch the rest hold.</p>
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
          <p className="index">Isolation {run.run_id?.slice(0, 8)}</p>
          <div className="invariants">
            {Object.entries(run.results || {}).map(([k, v]) => (
              <div key={k} className={v === "PASS" ? "ok" : ""}>
                <span>{k}</span>
                <span>{String(v)}</span>
              </div>
            ))}
          </div>
          {run.probe && (
            <p className="sub">
              {run.probe.attempt} → {run.probe.blocked ? "blocked" : "allowed"} · {run.probe.reason}
            </p>
          )}
        </div>
      )}
      {chaos && (
        <p className="banner">
          Degraded {chaos.degraded}. Others healthy: {String(chaos.others_healthy)} ({chaos.others}).
        </p>
      )}
      {obs && (
        <div className="kpis">
          <div className="kpi">
            <div className="l">Availability</div>
            <div className="v">{obs.api_availability}%</div>
          </div>
          <div className="kpi">
            <div className="l">p99</div>
            <div className="v">{obs.p99_latency_ms}</div>
          </div>
          <div className="kpi">
            <div className="l">Queue p95</div>
            <div className="v">{obs.queue_start_p95_s}s</div>
          </div>
        </div>
      )}
      {econ && (
        <>
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
        </>
      )}
    </>
  );
}
