import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getProjects } from '../services/api'
import type { Project } from '../types'

const Dashboard = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading projects: {(error as Error).message}</p>
      </div>
    )
  }

  const projects = data?.projects || []

  const getRiskLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800',
    }
    return colors[level] || 'bg-gray-100 text-gray-800'
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-800',
      planning: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-purple-100 text-purple-800',
      review: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      archived: 'bg-gray-100 text-gray-600',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold text-gray-900">Projects</h2>
        <Link
          to="/new"
          className="bg-primary-600 text-white hover:bg-primary-700 px-4 py-2 rounded-md text-sm font-medium"
        >
          Create Project
        </Link>
      </div>

      {projects.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
          <p className="text-gray-500 mb-4">Get started by creating your first project</p>
          <Link
            to="/new"
            className="inline-block bg-primary-600 text-white hover:bg-primary-700 px-4 py-2 rounded-md text-sm font-medium"
          >
            Create Project
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project: Project) => (
            <Link
              key={project.id}
              to={`/project/${project.id}`}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6"
            >
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-xl font-semibold text-gray-900">{project.name}</h3>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskLevelColor(project.risk_level)}`}>
                  {project.risk_level}
                </span>
              </div>
              
              <p className="text-gray-600 text-sm mb-4 line-clamp-2">{project.description}</p>
              
              <div className="flex items-center justify-between">
                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(project.status)}`}>
                  {project.status.replace('_', ' ')}
                </span>
                <span className="text-xs text-gray-500">
                  {new Date(project.created_at).toLocaleDateString()}
                </span>
              </div>

              {project.deadline && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <span className="text-xs text-gray-500">
                    Deadline: {new Date(project.deadline).toLocaleDateString()}
                  </span>
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

export default Dashboard
