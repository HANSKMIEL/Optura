import { useMutation, useQueryClient } from '@tanstack/react-query'
import { generateSpec, runTests, completeTask } from '../services/api'
import type { Task } from '../types'

interface TaskCardProps {
  task: Task
  onApprovalRequest: () => void
}

const TaskCard = ({ task, onApprovalRequest }: TaskCardProps) => {
  const queryClient = useQueryClient()

  const specMutation = useMutation({
    mutationFn: () => generateSpec(task.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', task.project_id] })
    },
  })

  const testMutation = useMutation({
    mutationFn: () => runTests(task.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', task.project_id] })
    },
  })

  const completeMutation = useMutation({
    mutationFn: () => completeTask(task.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', task.project_id] })
      queryClient.invalidateQueries({ queryKey: ['summary', task.project_id] })
    },
  })

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-800',
      in_progress: 'bg-blue-100 text-blue-800',
      blocked: 'bg-red-100 text-red-800',
      review: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h4 className="text-lg font-semibold text-gray-900">{task.name}</h4>
          <p className="text-sm text-gray-600 mt-1">{task.description}</p>
        </div>
        <div className="flex flex-col items-end gap-2 ml-4">
          <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(task.status)}`}>
            {task.status.replace('_', ' ')}
          </span>
          {task.requires_approval && (
            <span className="px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-800">
              Requires Approval
            </span>
          )}
        </div>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3 text-xs text-gray-600">
        {task.estimate_hours && (
          <div>
            <span className="font-medium">Estimate:</span> {task.estimate_hours}h
          </div>
        )}
        {task.confidence_score !== null && (
          <div>
            <span className="font-medium">Confidence:</span> {(task.confidence_score * 100).toFixed(0)}%
          </div>
        )}
        {task.tests.length > 0 && (
          <div>
            <span className="font-medium">Tests:</span> {task.tests.length}
          </div>
        )}
        {task.security_checks.length > 0 && (
          <div>
            <span className="font-medium">Security:</span> {task.security_checks.length}
          </div>
        )}
      </div>

      {/* Spec Status */}
      {!task.spec && (
        <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
          ⚠️ No specification generated yet
        </div>
      )}

      {/* Test Results */}
      {task.test_results && (
        <div className={`mb-3 p-2 rounded text-xs ${
          task.test_results.status === 'pass' 
            ? 'bg-green-50 border border-green-200 text-green-800'
            : task.test_results.status === 'fail'
            ? 'bg-red-50 border border-red-200 text-red-800'
            : 'bg-gray-50 border border-gray-200 text-gray-800'
        }`}>
          {task.test_results.status === 'pass' ? '✓' : task.test_results.status === 'fail' ? '✗' : 'ℹ️'} 
          {' '}{task.test_results.message || `Tests ${task.test_results.status}`}
        </div>
      )}

      {/* Approval Status */}
      {task.approved_by && (
        <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded text-xs text-green-800">
          ✓ Approved by {task.approved_by} on {new Date(task.approved_at!).toLocaleString()}
        </div>
      )}

      {task.rejection_reason && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
          ✗ Rejected: {task.rejection_reason}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 flex-wrap">
        {!task.spec && (
          <button
            onClick={() => specMutation.mutate()}
            disabled={specMutation.isPending}
            className="px-3 py-1 bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400 rounded text-xs font-medium"
          >
            {specMutation.isPending ? 'Generating...' : 'Generate Spec'}
          </button>
        )}

        {task.spec && task.status === 'pending' && (
          <button
            onClick={() => testMutation.mutate()}
            disabled={testMutation.isPending}
            className="px-3 py-1 bg-purple-600 text-white hover:bg-purple-700 disabled:bg-gray-400 rounded text-xs font-medium"
          >
            {testMutation.isPending ? 'Running...' : 'Run Tests'}
          </button>
        )}

        {task.status === 'review' && task.requires_approval && (
          <button
            onClick={onApprovalRequest}
            className="px-3 py-1 bg-yellow-600 text-white hover:bg-yellow-700 rounded text-xs font-medium"
          >
            Review & Approve
          </button>
        )}

        {task.status === 'approved' && (
          <button
            onClick={() => completeMutation.mutate()}
            disabled={completeMutation.isPending}
            className="px-3 py-1 bg-green-600 text-white hover:bg-green-700 disabled:bg-gray-400 rounded text-xs font-medium"
          >
            {completeMutation.isPending ? 'Completing...' : 'Mark Complete'}
          </button>
        )}
      </div>

      {/* Error Display */}
      {(specMutation.isError || testMutation.isError || completeMutation.isError) && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
          Error: {
            (specMutation.error as Error)?.message ||
            (testMutation.error as Error)?.message ||
            (completeMutation.error as Error)?.message
          }
        </div>
      )}
    </div>
  )
}

export default TaskCard
