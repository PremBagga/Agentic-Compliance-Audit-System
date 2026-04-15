import React from 'react';

interface DocumentUploadProps {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
  uploadedDocumentId?: string;
  uploadedFilename?: string;
}

export default function DocumentUpload({ onUpload, isUploading, uploadedDocumentId, uploadedFilename }: DocumentUploadProps) {
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);

  return (
    <div className="space-y-4">
      <label className="flex cursor-pointer flex-col gap-2 rounded-2xl border border-slate-700 bg-slate-900/80 p-4 text-sm text-slate-300 shadow-glow transition hover:border-indigo-500/50">
        <span className="font-medium text-slate-100">Upload document</span>
        <span className="text-slate-400">PDF or TXT documents are supported.</span>
        <input
          type="file"
          accept=".pdf,.txt,.md,.csv,.log"
          className="hidden"
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => setSelectedFile(event.target.files?.[0] ?? null)}
        />
      </label>

      {selectedFile ? (
        <div className="rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3 text-sm text-slate-300">
          Selected: <span className="font-medium text-slate-100">{selectedFile.name}</span>
        </div>
      ) : null}

      <button
        type="button"
        disabled={!selectedFile || isUploading}
        onClick={() => selectedFile && onUpload(selectedFile)}
        className="inline-flex items-center justify-center rounded-xl bg-indigo-500 px-4 py-2.5 font-medium text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isUploading ? 'Uploading…' : 'Upload Document'}
      </button>

      {uploadedDocumentId ? (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
          Uploaded {uploadedFilename ?? 'document'} — document ID: <span className="font-mono">{uploadedDocumentId}</span>
        </div>
      ) : null}
    </div>
  );
}