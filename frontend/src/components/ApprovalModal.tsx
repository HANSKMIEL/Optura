import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { approveTask, rejectTask, getTask } from '../services/api'
import type { TaskApproval, TaskRejection } from '../types'

interface ApprovalModalProps {
  taskId: number
  onClose: () => void
}

const ApprovalModal = ({ taskId, onClose }: ApprovalModalProps) => {
  const [approver, setApprover] = useState('')
  const [rejectionReason, setRejectionReason] = useState('')
  const [action, setAction] = useState<'approve' | 'reject' | null>(null)

  const { data: task } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => getTask(taskId),
  })

  const approveMutation = useMutation({
    mutationFn: (data: TaskApproval) => approveTask(taskId, data),
    onSuccess: () => {
      onClose()
    },
  })

  const rejectMutation = useMutation({
    mutationFn: (data: TaskRejection) => rejectTask(taskId, data),
    onSuccess: () => {
      onClose()
    },
  })

  const handleApprove = () => {
    if (!approver.trim()) {
      alert('Please enter your name')
      return
    }
    approveMutation.mutate({ approved_by: approver })
  }

  const handleReject = () => {
    if (!approver.trim() || !rejectionReason.trim()) {
      alert('Please enter your name and rejection reason')
      return
    }
    rejectMutation.mutate({
      rejected_by: approver,
      rejection_reason: rejectionReason,
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">
            Task Review & Approval
          </h3>

          {task && (
            <div className="mb-6">
              <h4 className="font-semibold text-lg mb-2">{task.name}</h4>
              <p className="text-sm text-gray-600 mb-4">{task.description}</p>

              {/* Spec Details */}
              {task.spec && (
                <div className="bg-gray-50 border border-gray-200 rounded p-4 mb-4">
                  <h5 className="font-semibold text-sm mb-2">Specification</h5>
                  <div className="text-xs space-y-2">
                    {task.spec.objective && (
                      <div>
                        <span className="font-medium">Objective:</span> {task.spec.objective}
                      </div>
                    )}
                    {task.spec.confidence_score !== undefined && (
                      <div>
                        <span className="font-medium">Confidence Score:</span>{' '}
                        {(task.spec.confidence_score * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Test Results */}
              {task.test_results && (
                <div className="bg-gray-50 border border-gray-200 rounded p-4 mb-4">
                  <h5 className="font-semibold text-sm mb-2">Test Results</h5>
                  <div className="text-xs">
                    <div>
                      <span className="font-medium">Status:</span> {task.test_results.status}
                    </div>
                    {task.test_results.message && (
                      <div className="mt-1">{task.test_results.message}</div>
                    )}
                  </div>
                </div>
              )}

              {/* Guardrails Check */}
              <div className="bg-blue-50 border border-blue-200 rounded p-4 mb-4">
                <h5 className="font-semibold text-sm mb-2">Guardrails Check</h5>
                <ul className="text-xs space-y-1">
                  <li className={task.spec ? 'text-green-600' : 'text-red-600'}>
                    {task.spec ? '✓' : '✗'} Specification: {task.spec ? 'Present' : 'Missing'}
                  </li>
                  <li className={task.test_results ? 'text-green-600' : 'text-yellow-600'}>
                    {task.test_results ? '✓' : '⚠️'} Tests: {task.test_results ? 'Run' : 'Not run yet'}
                  </li>
                </ul>
              </div>
            </div>
          )}

          {/* Approval Form */}
          {!action && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Name *
                </label>
                <input
                  type="text"
                  value={approver}
                  onChange={(e) => setApprover(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Enter your name"
                />
              </div>

              <div className="flex gap-4">
                <button
                  onClick={() => setAction('approve')}
                  className="flex-1 bg-green-600 text-white hover:bg-green-700 px-4 py-2 rounded-md font-medium"
                >
                  Approve
                </button>
                <button
                  onClick={() => setAction('reject')}
                  className="flex-1 bg-red-600 text-white hover:bg-red-700 px-4 py-2 rounded-md font-medium"
                >
                  Reject
                </button>
              </div>
            </div>
          )}

          {/* Rejection Form */}
          {action === 'reject' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rejection Reason *
                </label>
                <textarea
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Explain why you're rejecting this task..."
                />
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handleReject}
                  disabled={rejectMutation.isPending}
                  className="flex-1 bg-red-600 text-white hover:bg-red-700 disabled:bg-gray-400 px-4 py-2 rounded-md font-medium"
                >
                  {rejectMutation.isPending ? 'Rejecting...' : 'Confirm Rejection'}
                </button>
                <button
                  onClick={() => setAction(null)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md font-medium"
                >
                  Back
                </button>
              </div>
            </div>
          )}

          {/* Approval Confirmation */}
          {action === 'approve' && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded p-4">
                <p className="text-sm text-green-800">
                  You are about to approve this task. This will allow it to proceed to completion.
                </p>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={handleApprove}
                  disabled={approveMutation.isPending}
                  className="flex-1 bg-green-600 text-white hover:bg-green-700 disabled:bg-gray-400 px-4 py-2 rounded-md font-medium"
                >
                  {approveMutation.isPending ? 'Approving...' : 'Confirm Approval'}
                </button>
                <button
                  onClick={() => setAction(null)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md font-medium"
                >
                  Back
                </button>
              </div>
            </div>
          )}

          {/* Error Display */}
          {(approveMutation.isError || rejectMutation.isError) && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">
                Error: {(approveMutation.error as Error)?.message || (rejectMutation.error as Error)?.message}
              </p>
            </div>
          )}

          {/* Close Button */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <button
              onClick={onClose}
              className="w-full px-4 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ApprovalModal
