import type { AuditLogEntry } from '../types/api';

interface AuditLogViewerProps {
  auditId?: string;
  logs: AuditLogEntry[];
}

export default function AuditLogViewer({ auditId, logs }: AuditLogViewerProps) {
  if (!auditId) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 text-sm text-slate-400">Audit logs will appear after an audit is run.</div>;
  }

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-5 shadow-glow">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-slate-100">Audit logs</h3>
        <span className="rounded-full border border-slate-700 bg-slate-950/70 px-3 py-1 text-xs text-slate-300">
          {logs.length} entries
        </span>
      </div>
      <div className="mt-4 space-y-3">
        {logs.length === 0 ? (
          <p className="text-sm text-slate-400">No logs available yet.</p>
        ) : (
          logs.map((entry) => (
            <div key={`${entry.step}-${entry.timestamp}`} className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-sm">
              <div className="flex flex-wrap items-center gap-2 text-slate-300">
                <span className="font-medium text-slate-100">{entry.step}</span>
                <span className="text-slate-500">{entry.timestamp}</span>
              </div>
              <p className="mt-2 text-slate-400">{entry.message}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}