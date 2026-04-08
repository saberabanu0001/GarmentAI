import {
  auditorZonesFixture,
  precisionLogFixture,
} from "@/data/fixtures/auditorOverview";

function zoneClass(v: (typeof auditorZonesFixture)[number]["variant"]) {
  if (v === "ok") return "bg-emerald-50 text-emerald-900 ring-emerald-100";
  if (v === "warn") return "bg-amber-50 text-amber-900 ring-amber-100";
  return "bg-red-50 text-red-900 ring-red-100";
}

export default function AuditorPage() {
  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
            System overview
          </div>
          <h1 className="text-2xl font-bold text-zinc-900">Audit intelligence</h1>
        </div>
        <button
          type="button"
          className="inline-flex h-10 items-center justify-center rounded-xl bg-[#004D40] px-4 text-sm font-semibold text-white shadow hover:bg-[#00695c]"
        >
          Generate PDF audit
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl bg-white p-5 shadow-md">
          <h2 className="text-sm font-semibold text-zinc-900">
            Factory safety compliance heatmap
          </h2>
          <p className="mt-1 text-xs text-zinc-500">
            Sample tiles — connect to real zone scores later.
          </p>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {auditorZonesFixture.map((z) => (
              <div
                key={z.id}
                className={`rounded-xl p-4 ring-1 ${zoneClass(z.variant)}`}
              >
                <div className="text-xs font-medium opacity-80">{z.label}</div>
                <div className="mt-1 text-2xl font-bold">{z.pct}%</div>
                {z.subtitle ? (
                  <div className="mt-1 text-xs opacity-90">{z.subtitle}</div>
                ) : null}
              </div>
            ))}
            <div className="col-span-2 grid grid-cols-2 gap-2 md:grid-cols-4">
              {[
                { l: "Stitching 1", p: 92 },
                { l: "Stitching 2", p: 89 },
                { l: "Finishing", p: 95 },
                { l: "Packing", p: 78 },
              ].map((x) => (
                <div
                  key={x.l}
                  className="rounded-lg bg-zinc-50 p-3 text-xs ring-1 ring-zinc-100"
                >
                  <div className="font-medium text-zinc-700">{x.l}</div>
                  <div className="text-lg font-bold text-zinc-900">{x.p}%</div>
                </div>
              ))}
            </div>
          </div>
          <p className="mt-4 text-xs text-zinc-500">
            Real-time sensor overlay — placeholder.
          </p>
        </div>

        <div className="space-y-4 rounded-xl bg-white p-5 shadow-md">
          <h2 className="text-sm font-semibold text-zinc-900">
            AI auditor observations
          </h2>
          <div className="rounded-xl bg-emerald-50/80 p-4 text-sm text-emerald-950 ring-1 ring-emerald-100">
            Labor hours in Section B show a deviation from local mandates
            (sample insight). Replace with model output from your analytics
            pipeline.
          </div>
          <div className="rounded-xl bg-zinc-50 p-4 text-sm text-zinc-700 ring-1 ring-zinc-100">
            <div className="text-xs font-semibold uppercase text-zinc-500">
              Upcoming deadlines
            </div>
            <ul className="mt-2 list-inside list-disc text-sm">
              <li>Fire safety renewal (2 days)</li>
              <li>Quarterly ESG filing (14 days)</li>
            </ul>
          </div>
          <button
            type="button"
            className="w-full rounded-xl border border-zinc-200 py-2 text-sm font-semibold text-[#004D40] hover:bg-zinc-50"
          >
            View full AI log
          </button>
        </div>
      </div>

      <div className="rounded-xl bg-white p-5 shadow-md">
        <div className="flex flex-col justify-between gap-2 md:flex-row md:items-center">
          <div>
            <h2 className="text-sm font-semibold text-zinc-900">
              Regulatory comparison engine
            </h2>
            <p className="text-xs text-zinc-500">
              Side-by-side reconciliation (static mock — wire to RAG / rules later).
            </p>
          </div>
          <div className="flex gap-2">
            <span className="rounded-full bg-[#004D40] px-3 py-1 text-xs font-semibold text-white">
              Compliance gap
            </span>
            <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-semibold text-zinc-600">
              Text alignment
            </span>
          </div>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="rounded-xl bg-zinc-50 p-4 ring-1 ring-zinc-100">
            <div className="text-xs font-bold uppercase text-zinc-600">
              Local law (excerpt)
            </div>
            <p className="mt-2 text-sm leading-relaxed text-zinc-700">
              Ventilation and chemical storage must meet BNBC / factory rules
              (placeholder text).
            </p>
            <div className="mt-3 text-xs font-semibold text-zinc-500">
              Requirement score: 85% met
            </div>
          </div>
          <div className="rounded-xl bg-zinc-50 p-4 ring-1 ring-zinc-100">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase text-zinc-600">
                Global standards (CBLM)
              </span>
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold uppercase text-emerald-800">
                Stronger mandate
              </span>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-zinc-700">
              Buyer / training material may be stricter than local minima
              (placeholder).
            </p>
            <div className="mt-3 text-xs font-semibold text-[#c62828]">
              Gap example: document turnover frequency
            </div>
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl bg-white shadow-md">
        <div className="flex flex-col border-b border-zinc-100 px-5 py-4 md:flex-row md:items-center md:justify-between">
          <h2 className="font-semibold text-zinc-900">Precision audit logs</h2>
          <span className="text-xs text-zinc-500">
            Viewing {precisionLogFixture.length} of 1,240 (sample)
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-zinc-50 text-xs font-semibold uppercase text-zinc-500">
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-5 py-3">Factory zone</th>
                <th className="px-5 py-3">Category</th>
                <th className="px-5 py-3">Compliance delta</th>
                <th className="px-5 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {precisionLogFixture.map((row) => (
                <tr
                  key={row.id}
                  className="border-t border-zinc-100 hover:bg-zinc-50/60"
                >
                  <td className="whitespace-nowrap px-5 py-3 text-zinc-600">
                    {row.ts}
                  </td>
                  <td className="px-5 py-3 text-zinc-700">{row.zone}</td>
                  <td className="px-5 py-3 text-zinc-700">{row.category}</td>
                  <td className="px-5 py-3">
                    <span
                      className={
                        row.deltaPct >= 0
                          ? "font-semibold text-emerald-700"
                          : "font-semibold text-[#c62828]"
                      }
                    >
                      {row.deltaPct >= 0 ? "+" : ""}
                      {row.deltaPct}%
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-bold ${
                        row.status === "VERIFIED"
                          ? "bg-emerald-50 text-emerald-800 ring-1 ring-emerald-100"
                          : "bg-red-50 text-red-800 ring-1 ring-red-100"
                      }`}
                    >
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
