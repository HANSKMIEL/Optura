import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { createProject } from '../services/api'
import type { CreateProjectRequest } from '../types'

const NewProject = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState<CreateProjectRequest>({
    name: '',
    description: '',
    goal: '',
    acceptance_criteria: [],
    risk_level: 'medium',
    environment: '',
    created_by: 'user',
  })
  const [criteriaInput, setCriteriaInput] = useState('')

  const mutation = useMutation({
    mutationFn: createProject,
    onSuccess: (data) => {
      navigate(`/project/${data.id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(formData)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const addCriteria = () => {
    if (criteriaInput.trim()) {
      setFormData(prev => ({
        ...prev,
        acceptance_criteria: [...(prev.acceptance_criteria || []), criteriaInput.trim()]
      }))
      setCriteriaInput('')
    }
  }

  const removeCriteria = (index: number) => {
    setFormData(prev => ({
      ...prev,
      acceptance_criteria: prev.acceptance_criteria?.filter((_, i) => i !== index) || []
    }))
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-3xl font-bold text-gray-900 mb-6">Create New Project</h2>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Project Name *
          </label>
          <input
            type="text"
            id="name"
            name="name"
            required
            value={formData.name}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="My Awesome Project"
          />
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
            Description *
          </label>
          <textarea
            id="description"
            name="description"
            required
            value={formData.description}
            onChange={handleChange}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="Describe your project..."
          />
        </div>

        {/* Goal */}
        <div>
          <label htmlFor="goal" className="block text-sm font-medium text-gray-700 mb-2">
            Goal *
          </label>
          <textarea
            id="goal"
            name="goal"
            required
            value={formData.goal}
            onChange={handleChange}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="What do you want to achieve?"
          />
        </div>

        {/* Acceptance Criteria */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Acceptance Criteria
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={criteriaInput}
              onChange={(e) => setCriteriaInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCriteria())}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Add a criterion..."
            />
            <button
              type="button"
              onClick={addCriteria}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
            >
              Add
            </button>
          </div>
          {formData.acceptance_criteria && formData.acceptance_criteria.length > 0 && (
            <ul className="space-y-2">
              {formData.acceptance_criteria.map((criterion, index) => (
                <li key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                  <span className="text-sm">{criterion}</span>
                  <button
                    type="button"
                    onClick={() => removeCriteria(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Risk Level */}
        <div>
          <label htmlFor="risk_level" className="block text-sm font-medium text-gray-700 mb-2">
            Risk Level
          </label>
          <select
            id="risk_level"
            name="risk_level"
            value={formData.risk_level}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        {/* Environment */}
        <div>
          <label htmlFor="environment" className="block text-sm font-medium text-gray-700 mb-2">
            Environment
          </label>
          <input
            type="text"
            id="environment"
            name="environment"
            value={formData.environment}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="e.g., Python 3.11, Node.js 18"
          />
        </div>

        {/* Error Display */}
        {mutation.isError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">Error: {(mutation.error as Error).message}</p>
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-4">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="flex-1 bg-primary-600 text-white hover:bg-primary-700 disabled:bg-gray-400 px-4 py-2 rounded-md font-medium"
          >
            {mutation.isPending ? 'Creating...' : 'Create Project'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="px-4 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md font-medium"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}

export default NewProject
