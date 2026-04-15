import React from 'react';
import AuditLogViewer from './components/AuditLogViewer';
import AuditResults from './components/AuditResults';
import AuditRunner from './components/AuditRunner';
import HITLApproval from './components/HITLApproval';
import { approveAudit, getAudit, getAuditLog, runAudit, uploadDocument } from './services/api';
import type { AuditLogEntry, AuditState, UploadResponse } from './types/api';

type TabName = 'upload' | 'results' | 'approval' | 'logs';

const TERMINAL_STATUSES = new Set(['COMPLETE', 'APPROVED', 'REJECTED', 'FAILED']);

export default function App() {
  const [activeTab, setActiveTab] = React.useState<TabName>('upload');
  const [documentId, setDocumentId] = React.useState<string>('');
  const [uploadedFilename, setUploadedFilename] = React.useState<string>('');
  const [selectedPolicies, setSelectedPolicies] = React.useState<string[]>([]);
  const [auditState, setAuditState] = React.useState<AuditState | null>(null);
  const [logs, setLogs] = React.useState<AuditLogEntry[]>([]);
  const [isUploading, setIsUploading] = React.useState(false);
  const [isRunning, setIsRunning] = React.useState(false);
  const [isApproving, setIsApproving] = React.useState(false);
  const [error, setError] = React.useState<string>('');
  const previousAuditStatusRef = React.useRef<{ auditId: string; status: string } | null>(null);

  const refreshAudit = React.useCallback(async (auditId: string) => {
    const [latestAudit, latestLogs] = await Promise.all([getAudit(auditId), getAuditLog(auditId)]);
    setAuditState(latestAudit);
    setLogs(latestLogs);
  }, []);

  React.useEffect(() => {
    if (!auditState?.audit_id) {
      return;
    }

    const previous = previousAuditStatusRef.current;
    const sameAudit = previous?.auditId === auditState.audit_id;
    const wasWaiting = sameAudit && previous?.status === 'WAITING_FOR_APPROVAL';
    const nowWaiting = auditState.status === 'WAITING_FOR_APPROVAL';

    if (nowWaiting && !wasWaiting) {
      setActiveTab('approval');
    }

    previousAuditStatusRef.current = {
      auditId: auditState.audit_id,
      status: auditState.status,
    };
  }, [auditState?.audit_id, auditState?.status]);

  React.useEffect(() => {
    if (!auditState?.audit_id) {
      return;
    }

    if (TERMINAL_STATUSES.has(auditState.status)) {
      return;
    }

    const interval = window.setInterval(() => {
      void refreshAudit(auditState.audit_id).catch((err: Error) => setError(err.message));
    }, 3000);

    return () => window.clearInterval(interval);
  }, [auditState?.audit_id, auditState?.status, refreshAudit]);

  const handleUpload = async (file: File) => {
    setError('');
    setIsUploading(true);
    try {
      const result: UploadResponse = await uploadDocument(file);
      setDocumentId(result.document_id);
      setUploadedFilename(result.filename);
      setActiveTab('upload');
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Failed to upload document.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunAudit = async () => {
    if (!documentId) {
      setError('Upload a document before running the audit.');
      return;
    }

    setError('');
    setIsRunning(true);
    try {
      const result = await runAudit({
        document_id: documentId,
        selected_policies: selectedPolicies,
      });
      setAuditState(result);
      setLogs(await getAuditLog(result.audit_id));
      setActiveTab('results');
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : 'Failed to run audit.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleApprove = async (approved: boolean) => {
    if (!auditState?.audit_id) {
      setError('No audit is available for approval.');
      return;
    }

    setError('');
    setIsApproving(true);
    try {
      const result = await approveAudit({ audit_id: auditState.audit_id, approved });
      setAuditState(result);
      setLogs(await getAuditLog(auditState.audit_id));
      setActiveTab('results');
    } catch (approvalError) {
      setError(approvalError instanceof Error ? approvalError.message : 'Failed to update approval.');
    } finally {
      setIsApproving(false);
    }
  };

  const tabButton = (tab: TabName, label: string) => (
    <button
      type="button"
      onClick={() => setActiveTab(tab)}
      className={`rounded-full px-4 py-2 text-sm font-medium transition ${
        activeTab === tab ? 'bg-indigo-500 text-white shadow-glow' : 'bg-slate-900/80 text-slate-300 hover:bg-slate-800'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-8 rounded-3xl border border-slate-700 bg-slate-900/70 p-6 shadow-glow backdrop-blur">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.25em] text-indigo-300">Agentic Compliance & Audit Intelligence System</p>
            <p className="mt-3 max-w-3xl text-sm text-slate-400">
              Upload a document, choose policy categories, run the audit, review structured findings, and approve high-risk results when required.
            </p>
          </div>
          <div className="grid gap-3 text-sm text-slate-300 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3">
              <span className="block text-xs uppercase tracking-[0.2em] text-slate-500">Document</span>
              <span className="mt-1 block font-medium text-slate-100">{uploadedFilename || 'Not uploaded yet'}</span>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3">
              <span className="block text-xs uppercase tracking-[0.2em] text-slate-500">Audit ID</span>
              <span className="mt-1 block font-mono text-slate-100">{auditState?.audit_id || 'Pending'}</span>
            </div>
          </div>
        </div>
        {error ? <div className="mt-5 rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">{error}</div> : null}
      </header>

      <nav className="mb-6 flex flex-wrap gap-3">
        {tabButton('upload', 'Upload')}
        {tabButton('results', 'Results')}
        {tabButton('approval', 'Approval')}
        {tabButton('logs', 'Logs')}
      </nav>

      <main className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
        <section className="space-y-6">
          {activeTab === 'upload' ? (
            <AuditRunner
              documentId={documentId}
              uploadedFilename={uploadedFilename}
              selectedPolicies={selectedPolicies}
              onSelectedPoliciesChange={setSelectedPolicies}
              onUpload={handleUpload}
              onRunAudit={handleRunAudit}
              isUploading={isUploading}
              isRunning={isRunning}
            />
          ) : null}

          {activeTab === 'results' ? <AuditResults audit={auditState} /> : null}

          {activeTab === 'approval' ? (
            <HITLApproval
              auditId={auditState?.audit_id}
              needsApproval={auditState?.needs_approval}
              status={auditState?.status}
              isApproving={isApproving}
              onApprove={handleApprove}
            />
          ) : null}

          {activeTab === 'logs' ? <AuditLogViewer auditId={auditState?.audit_id} logs={logs} /> : null}
        </section>

        <aside className="space-y-6">
          <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-5 shadow-glow">
            <h2 className="text-lg font-semibold text-slate-100">Workflow summary</h2>
            <div className="mt-4 space-y-3 text-sm text-slate-300">
              <div className="rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                <span className="block text-xs uppercase tracking-[0.2em] text-slate-500">Policies count</span>
                <span className="mt-1 block text-base font-medium text-slate-100">{auditState?.policy_count ?? 0}</span>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                <span className="block text-xs uppercase tracking-[0.2em] text-slate-500">Findings</span>
                <span className="mt-1 block text-base font-medium text-slate-100">{auditState?.audit_findings.length ?? 0}</span>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                <span className="block text-xs uppercase tracking-[0.2em] text-slate-500">Confidence</span>
                <span className="mt-1 block text-base font-medium text-slate-100">
                  {auditState ? `${(auditState.confidence_score * 100).toFixed(0)}%` : '—'}
                </span>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                <span className="block text-xs uppercase tracking-[0.2em] text-slate-500">Approval required</span>
                <span className="mt-1 block text-base font-medium text-slate-100">
                  {auditState?.needs_approval ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-5 shadow-glow">
            <h2 className="text-lg font-semibold text-slate-100">How it works</h2>
            <ul className="mt-4 space-y-3 text-sm text-slate-400">
              <li>1. Upload PDF/TXT and store the parsed text.</li>
              <li>2. Select policy categories or use the default set.</li>
              <li>3. Retrieve policies, audit the document, and run reflection.</li>
              <li>4. High-risk results trigger HITL approval.</li>
              <li>5. Logs and state remain available through the API.</li>
            </ul>
          </div>
        </aside>
      </main>
    </div>
  );
}