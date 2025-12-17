import axios from 'axios';
import type { Project, Task, Artifact, CreateProjectRequest, TaskApproval, TaskRejection, DependencyGraph } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Projects
export const getProjects = async (): Promise<{ projects: Project[]; total: number }> => {
  const response = await api.get('/projects/');
  return response.data;
};

export const getProject = async (id: number): Promise<Project> => {
  const response = await api.get(`/projects/${id}`);
  return response.data;
};

export const createProject = async (data: CreateProjectRequest): Promise<Project> => {
  const response = await api.post('/projects/', data);
  return response.data;
};

export const updateProject = async (id: number, data: Partial<CreateProjectRequest>): Promise<Project> => {
  const response = await api.patch(`/projects/${id}`, data);
  return response.data;
};

export const deleteProject = async (id: number): Promise<void> => {
  await api.delete(`/projects/${id}`);
};

export const generatePlan = async (id: number): Promise<any> => {
  const response = await api.post(`/projects/${id}/generate-plan`);
  return response.data;
};

export const getAuditLog = async (id: number): Promise<any> => {
  const response = await api.get(`/projects/${id}/audit-log`);
  return response.data;
};

// Tasks
export const getTasks = async (projectId: number): Promise<Task[]> => {
  const response = await api.get(`/tasks/project/${projectId}`);
  return response.data;
};

export const getTask = async (id: number): Promise<Task> => {
  const response = await api.get(`/tasks/${id}`);
  return response.data;
};

export const generateSpec = async (id: number): Promise<any> => {
  const response = await api.post(`/tasks/${id}/generate-spec`);
  return response.data;
};

export const approveTask = async (id: number, data: TaskApproval): Promise<any> => {
  const response = await api.post(`/tasks/${id}/approve`, data);
  return response.data;
};

export const rejectTask = async (id: number, data: TaskRejection): Promise<any> => {
  const response = await api.post(`/tasks/${id}/reject`, data);
  return response.data;
};

export const runTests = async (id: number): Promise<any> => {
  const response = await api.post(`/tasks/${id}/run-tests`);
  return response.data;
};

export const completeTask = async (id: number): Promise<any> => {
  const response = await api.post(`/tasks/${id}/complete`);
  return response.data;
};

// Artifacts
export const uploadArtifact = async (taskId: number, file: File): Promise<Artifact> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post(`/artifacts/task/${taskId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getArtifacts = async (taskId: number): Promise<Artifact[]> => {
  const response = await api.get(`/artifacts/task/${taskId}`);
  return response.data;
};

export const verifyArtifact = async (id: number): Promise<any> => {
  const response = await api.post(`/artifacts/${id}/verify`);
  return response.data;
};

// Orchestrator
export const getCriticalPath = async (projectId: number): Promise<any> => {
  const response = await api.get(`/orchestrator/project/${projectId}/critical-path`);
  return response.data;
};

export const getDependencyGraph = async (projectId: number): Promise<DependencyGraph> => {
  const response = await api.get(`/orchestrator/project/${projectId}/dependency-graph`);
  return response.data;
};

export const reprioritizeTasks = async (projectId: number): Promise<any> => {
  const response = await api.post(`/orchestrator/project/${projectId}/reprioritize`);
  return response.data;
};

export const getNextActions = async (projectId: number): Promise<any> => {
  const response = await api.get(`/orchestrator/project/${projectId}/next-actions`);
  return response.data;
};

export const getStatusSummary = async (projectId: number): Promise<any> => {
  const response = await api.get(`/orchestrator/project/${projectId}/status-summary`);
  return response.data;
};

export default api;
