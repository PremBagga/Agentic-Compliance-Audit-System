import React from 'react';
import DocumentUpload from './DocumentUpload';

interface AuditRunnerProps {
  documentId?: string;
  uploadedFilename?: string;
  selectedPolicies: string[];
  onSelectedPoliciesChange: (next: string[]) => void;
  onUpload: (file: File) => Promise<void>;
  onRunAudit: () => Promise<void>;
  isUploading: boolean;
  isRunning: boolean;
}

const POLICY_OPTIONS = [
  { label: 'Security', value: 'security' },
  { label: 'Privacy', value: 'privacy' },
  { label: 'Compliance', value: 'compliance' },
  { label: 'Financial', value: 'financial' },
  { label: 'All', value: 'ALL' },
];

export default function AuditRunner({
  documentId,
  uploadedFilename,
  selectedPolicies,
  onSelectedPoliciesChange,
  onUpload,
  onRunAudit,
  isUploading,
  isRunning,
}: AuditRunnerProps) {
  const togglePolicy = (value: string) => {
    if (value === 'ALL') {
      onSelectedPoliciesChange(selectedPolicies.includes('ALL') ? [] : ['ALL']);
      return;
    }

    const withoutAll = selectedPolicies.filter((item) => item !== 'ALL');
    if (withoutAll.includes(value)) {
      onSelectedPoliciesChange(withoutAll.filter((item) => item !== value));
      return;
    }

    onSelectedPoliciesChange([...withoutAll, value]);
  };

  return (
    <div className="space-y-6">
      <DocumentUpload
        onUpload={onUpload}
        isUploading={isUploading}
        uploadedDocumentId={documentId}
        uploadedFilename={uploadedFilename}
      />

      <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-5 shadow-glow">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-slate-100">Policy selector</h3>
            <p className="text-sm text-slate-400">Choose one or more categories, or leave blank to use the default fallback set.</p>
          </div>
          <div className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
            {selectedPolicies.length === 0 ? 'Default policies active' : `${selectedPolicies.length} selected`}
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          {POLICY_OPTIONS.map((option) => (
            <label
              key={option.value}
              className="flex items-center gap-3 rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-slate-200 transition hover:border-indigo-500/50"
            >
              <input
                type="checkbox"
                checked={selectedPolicies.includes(option.value)}
                onChange={() => togglePolicy(option.value)}
                className="h-4 w-4 rounded border-slate-500 bg-slate-900 text-indigo-500 focus:ring-indigo-500"
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>

        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-slate-400">
            {documentId ? (
              <>
                Ready to audit <span className="font-mono text-slate-200">{uploadedFilename ?? documentId}</span>
              </>
            ) : (
              'Upload a document before running the audit.'
            )}
          </div>
          <button
            type="button"
            disabled={!documentId || isRunning}
            onClick={onRunAudit}
            className="inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2.5 font-medium text-white transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isRunning ? 'Running audit…' : 'Run Audit'}
          </button>
        </div>
      </div>
    </div>
  );
}