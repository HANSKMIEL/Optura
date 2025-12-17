export interface Project {
  id: number;
  name: string;
  description: string;
  goal: string;
  acceptance_criteria: string[];
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  status: 'draft' | 'planning' | 'in_progress' | 'review' | 'completed' | 'archived';
  environment: string | null;
  deadline: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  project_id: number;
  name: string;
  description: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  tests: Array<{ type: string; description: string }>;
  security_checks: Array<{ type: string; description: string }>;
  estimate_hours: number | null;
  status: 'pending' | 'in_progress' | 'blocked' | 'review' | 'approved' | 'completed' | 'failed';
  confidence_score: number | null;
  requires_approval: boolean;
  approved_by: string | null;
  approved_at: string | null;
  rejection_reason: string | null;
  order: number;
  spec: Record<string, any> | null;
  test_results: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface Artifact {
  id: number;
  task_id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_hash: string;
  mime_type: string;
  size_bytes: number;
  status: 'pending' | 'verified' | 'rejected';
  verification_result: Record<string, any> | null;
  created_at: string;
}

export interface CreateProjectRequest {
  name: string;
  description: string;
  goal: string;
  acceptance_criteria?: string[];
  risk_level?: 'low' | 'medium' | 'high' | 'critical';
  environment?: string;
  deadline?: string;
  created_by?: string;
}

export interface TaskApproval {
  approved_by: string;
}

export interface TaskRejection {
  rejected_by: string;
  rejection_reason: string;
}

export interface DependencyGraph {
  nodes: Array<{
    id: number;
    name: string;
    status: string;
    estimate_hours: number | null;
    requires_approval: boolean;
    order: number;
  }>;
  edges: Array<{
    from: number;
    to: number;
  }>;
  project_id: number;
}
