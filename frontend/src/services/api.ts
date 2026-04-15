import type { ApproveRequest, AuditLogEntry, AuditState, RunAuditRequest, UploadResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail ?? `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  return parseResponse<UploadResponse>(response);
}

export async function runAudit(payload: RunAuditRequest): Promise<AuditState> {
  const response = await fetch(`${API_BASE_URL}/run_audit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  return parseResponse<AuditState>(response);
}

export async function getAudit(auditId: string): Promise<AuditState> {
  const response = await fetch(`${API_BASE_URL}/audit/${encodeURIComponent(auditId)}`);
  return parseResponse<AuditState>(response);
}

export async function approveAudit(payload: ApproveRequest): Promise<AuditState> {
  const response = await fetch(`${API_BASE_URL}/approve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  return parseResponse<AuditState>(response);
}

export async function getAuditLog(auditId: string): Promise<AuditLogEntry[]> {
  const response = await fetch(`${API_BASE_URL}/audit_log/${encodeURIComponent(auditId)}`);
  return parseResponse<AuditLogEntry[]>(response);
}

export async function healthCheck(): Promise<{ status: string; documents: number; audits: number }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return parseResponse<{ status: string; documents: number; audits: number }>(response);
}