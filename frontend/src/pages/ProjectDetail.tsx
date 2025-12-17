import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { getProject, getTasks, generatePlan, getStatusSummary } from '../services/api'
import TaskCard from '../components/TaskCard'
import PlanCanvas from '../components/PlanCanvas'
import ApprovalModal from '../components/ApprovalModal'

const ProjectDetail = () => {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id || '0')
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showGraph, setShowGraph] = useState(false)
  const [approvalTask, setApprovalTask] = useState<number | null>(null)

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId),
  })

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks', projectId],
    queryFn: () => getTasks(projectId),
  })

  const { data: summary } = useQuery({
    queryKey: ['summary', projectId],
    queryFn: () => getStatusSummary(projectId),
  })

  const planMutation = useMutation({
    mutationFn: () => generatePlan(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['summary', projectId] })
    },
  })

  if (projectLoading || tasksLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Project not found</p>
      </div>
    )
  }

  const getRiskLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800',
    }
    return colors[level] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div>
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <button
              onClick={() => navigate('/')}
              className="text-sm text-gray-600 hover:text-gray-900 mb-2"
            >
              ← Back to Projects
            </button>
            <h2 className="text-3xl font-bold text-gray-900">{project.name}</h2>
          </div>
          <span className={`px-3 py-1 rounded text-sm font-medium ${getRiskLevelColor(project.risk_level)}`}>
            {project.risk_level}
          </span>
        </div>

        <p className="text-gray-600 mb-4">{project.description}</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <h4 className="font-semibold text-sm text-gray-700 mb-2">Goal</h4>
            <p className="text-sm text-gray-600">{project.goal}</p>
          </div>

          {project.acceptance_criteria && project.acceptance_criteria.length > 0 && (
            <div>
              <h4 className="font-semibold text-sm text-gray-700 mb-2">Acceptance Criteria</h4>
              <ul className="list-disc list-inside text-sm text-gray-600">
                {project.acceptance_criteria.map((criterion, i) => (
                  <li key={i}>{criterion}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          {(!tasks || tasks.length === 0) && (
            <button
              onClick={() => planMutation.mutate()}
              disabled={planMutation.isPending}
              className="bg-primary-600 text-white hover:bg-primary-700 disabled:bg-gray-400 px-4 py-2 rounded-md text-sm font-medium"
            >
              {planMutation.isPending ? 'Generating Plan...' : 'Generate Plan'}
            </button>
          )}
          {tasks && tasks.length > 0 && (
            <button
              onClick={() => setShowGraph(!showGraph)}
              className="border border-gray-300 text-gray-700 hover:bg-gray-50 px-4 py-2 rounded-md text-sm font-medium"
            >
              {showGraph ? 'Hide Dependency Graph' : 'Show Dependency Graph'}
            </button>
          )}
        </div>

        {planMutation.isError && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">Error: {(planMutation.error as Error).message}</p>
          </div>
        )}
      </div>

      {/* Status Summary */}
      {summary && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Project Status</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600">Progress</p>
              <p className="text-2xl font-bold text-primary-600">{summary.progress_percent}%</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Tasks</p>
              <p className="text-2xl font-bold">{summary.total_tasks}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Completed Hours</p>
              <p className="text-2xl font-bold">{summary.completed_estimate_hours || 0}h</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Hours</p>
              <p className="text-2xl font-bold">{summary.total_estimate_hours || 0}h</p>
            </div>
          </div>
        </div>
      )}

      {/* Dependency Graph */}
      {showGraph && tasks && tasks.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Dependency Graph</h3>
          <PlanCanvas projectId={projectId} />
        </div>
      )}

      {/* Tasks */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Tasks ({tasks?.length || 0})</h3>

        {!tasks || tasks.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">No tasks yet. Generate a plan to get started.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onApprovalRequest={() => setApprovalTask(task.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Approval Modal */}
      {approvalTask && (
        <ApprovalModal
          taskId={approvalTask}
          onClose={() => {
            setApprovalTask(null)
            queryClient.invalidateQueries({ queryKey: ['tasks', projectId] })
          }}
        />
      )}
    </div>
  )
}

export default ProjectDetail
