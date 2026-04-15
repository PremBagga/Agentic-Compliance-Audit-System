import type { AuditState } from '../types/api';

interface AuditResultsProps {
  audit?: AuditState | null;
}

function badgeClass(value: string): string {
  switch (value.toUpperCase()) {
    case 'HIGH':
      return 'bg-rose-500/15 text-rose-200 border-rose-500/30';
    case 'MEDIUM':
      return 'bg-amber-500/15 text-amber-200 border-amber-500/30';
    default:
      return 'bg-emerald-500/15 text-emerald-200 border-emerald-500/30';
  }
}

export default function AuditResults({ audit }: AuditResultsProps) {
  if (!audit) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 text-sm text-slate-400">No audit has been run yet.</div>;
  }

  return (
    <div className="space-y-5 rounded-2xl border border-slate-700 bg-slate-900/80 p-5 shadow-glow">
      <div className="flex flex-wrap gap-3">
        <span className={`rounded-full border px-3 py-1 text-xs font-medium ${badgeClass(audit.risk_level)}`}>Risk: {audit.risk_level}</span>
        <span className="rounded-full border border-slate-700 bg-slate-950/70 px-3 py-1 text-xs font-medium text-slate-200">
          Confidence: {(audit.confidence_score * 100).toFixed(0)}%
        </span>
        <span className="rounded-full border border-slate-700 bg-slate-950/70 px-3 py-1 text-xs font-medium text-slate-200">
          Status: {audit.status}
        </span>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-sm text-slate-400">Policies retrieved</p>
          <p className="mt-1 text-2xl font-semibold text-slate-100">{audit.policy_count}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-sm text-slate-400">Findings</p>
          <p className="mt-1 text-2xl font-semibold text-slate-100">{audit.audit_findings.length}</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-sm text-slate-400">Reflection passes</p>
          <p className="mt-1 text-2xl font-semibold text-slate-100">{audit.reflection_iterations}</p>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
        <p className="text-sm font-medium text-slate-300">Findings</p>
        <div className="mt-4 space-y-3">
          {audit.audit_findings.length === 0 ? (
            <p className="text-sm text-slate-400">No findings were generated for this audit.</p>
          ) : (
            audit.audit_findings.map((finding) => (
              <div key={finding.policy_id} className="rounded-xl border border-slate-800 bg-slate-900/80 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <h4 className="font-semibold text-slate-100">{finding.policy_title}</h4>
                  <span className={`rounded-full border px-2.5 py-0.5 text-xs ${badgeClass(finding.severity)}`}>{finding.severity}</span>
                </div>
                <p className="mt-2 text-sm text-slate-300">{finding.evidence}</p>
                <p className="mt-2 text-sm text-slate-400">Recommendation: {finding.recommendation}</p>
                {finding.missing_requirements.length > 0 ? (
                  <p className="mt-2 text-xs text-slate-500">Missing: {finding.missing_requirements.join(', ')}</p>
                ) : null}
              </div>
            ))
          )}
        </div>
      </div>

      {audit.reflection_notes.length > 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
          <p className="text-sm font-medium text-slate-300">Reflection notes</p>
          <ul className="mt-3 space-y-2 text-sm text-slate-400">
            {audit.reflection_notes.map((note) => (
              <li key={note} className="rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-2">
                {note}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}