interface HITLApprovalProps {
  auditId?: string;
  needsApproval?: boolean;
  status?: string;
  isApproving?: boolean;
  onApprove: (approved: boolean) => Promise<void>;
}

export default function HITLApproval({ auditId, needsApproval, status, isApproving = false, onApprove }: HITLApprovalProps) {
  if (!auditId) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 text-sm text-slate-400">Run an audit before approval can be submitted.</div>;
  }

  if (!needsApproval && status !== 'WAITING_FOR_APPROVAL') {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 text-sm text-slate-400">No approval is needed for the current audit.</div>;
  }

  return (
    <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-5 shadow-glow">
      <h3 className="text-lg font-semibold text-amber-100">Human-in-the-Loop approval required</h3>
      <p className="mt-2 text-sm text-amber-100/80">This audit is high risk and must be approved or rejected manually.</p>
      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          disabled={isApproving}
          onClick={() => onApprove(true)}
          className="rounded-xl bg-emerald-500 px-4 py-2.5 font-medium text-white transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isApproving ? 'Submitting…' : 'Approve'}
        </button>
        <button
          type="button"
          disabled={isApproving}
          onClick={() => onApprove(false)}
          className="rounded-xl bg-rose-500 px-4 py-2.5 font-medium text-white transition hover:bg-rose-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Reject
        </button>
      </div>
    </div>
  );
}