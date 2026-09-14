"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";

export default function ReleasesPage() {
  const [rel, setRel] = useState(null);
  const [list, setList] = useState([]);

  const refresh = () => api("/v1/releases").then(setList);
  useEffect(() => {
    refresh();
  }, []);

  async function start() {
    const r = await api("/v1/releases", { method: "POST", body: JSON.stringify({ version: "V8" }) });
    setRel(r);
    refresh();
  }
  async function cmd(path) {
    if (!rel) return;
    const r = await api(`/v1/releases/${rel.release_id}/${path}`, { method: "POST", body: "{}" });
    setRel(r);
    refresh();
  }

  const current = rel || list[list.length - 1];

  return (
    <>
      <h1>Releases</h1>
      <p className="sub">One artifact, progressive waves. Operations are O(waves), not O(N).</p>
      <div className="row">
        <button className="btn" onClick={start}>
          Start V8
        </button>
        <button className="btn ghost" onClick={() => cmd("continue")}>
          Continue wave
        </button>
        <button className="btn ghost" onClick={() => cmd("halt")}>
          Halt
        </button>
        <button className="btn ghost" onClick={() => cmd("rollback")}>
          Rollback
        </button>
      </div>
      {current && (
        <div className="panel">
          <p>
            {current.version} · {current.status} · wave {current.wave} · digest <code>{current.digest}</code>
          </p>
          <p>Build ✓ Image · ✓ SBOM · ✓ Scan · ✓ Signed · Error budget {current.error_budget}%</p>
          <p>
            Schema {current.schema?.on_release}/{current.schema?.total} tenants on {current.version}
          </p>
          <table>
            <thead>
              <tr>
                <th>Cell</th>
                <th>Release</th>
                <th>State</th>
              </tr>
            </thead>
            <tbody>
              {(current.cells || []).map((c) => (
                <tr key={c.cell_id}>
                  <td>{c.cell_id}</td>
                  <td>{c.release}</td>
                  <td>
                    <span className={`badge ${c.state}`}>{c.state}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
