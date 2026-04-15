export interface PolicyItem {
  id: string;
  title: string;
  description: string;
  category: string;
  severity: string;
  requirements: string[];
}

export interface AuditFinding {
  policy_id: string;
  policy_title: string;
  category: string;
  severity: string;
  status: string;
  evidence: string;
  matched_requirements: string[];
  missing_requirements: string[];
  recommendation: string;
  confidence: number;
}

export interface AuditState {
  audit_id: string;
  document_id: string;
  document_name: string;
  document_text: string;
  selected_policy_categories: string[];
  retrieved_policies: PolicyItem[];
  audit_findings: AuditFinding[];
  reflection_notes: string[];
  risk_level: string;
  confidence_score: number;
  status: string;
  approved: boolean;
  needs_approval: boolean;
  reflection_iterations: number;
  policy_count: number;
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  text_length: number;
}

export interface RunAuditRequest {
  document_id: string;
  selected_policies?: string[];
}

export interface ApproveRequest {
  audit_id: string;
  approved: boolean;
}

export interface AuditLogEntry {
  audit_id: string;
  step: string;
  message: string;
  timestamp: string;
}