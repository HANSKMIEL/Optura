import { useQuery } from '@tanstack/react-query'
import { getDependencyGraph } from '../services/api'
import { useEffect, useRef } from 'react'

interface PlanCanvasProps {
  projectId: number
}

const PlanCanvas = ({ projectId }: PlanCanvasProps) => {
  const canvasRef = useRef<HTMLDivElement>(null)

  const { data: graph, isLoading } = useQuery({
    queryKey: ['dependencyGraph', projectId],
    queryFn: () => getDependencyGraph(projectId),
  })

  useEffect(() => {
    if (!graph || !canvasRef.current) return

    // Clear previous content
    canvasRef.current.innerHTML = ''

    // Simple visualization: list nodes and edges
    const container = canvasRef.current

    // Create node elements
    const nodeElements = new Map<number, HTMLDivElement>()
    graph.nodes.forEach((node, index) => {
      const nodeDiv = document.createElement('div')
      nodeDiv.className = 'inline-block bg-white border-2 rounded-lg p-3 m-2 shadow'
      
      const statusColors: Record<string, string> = {
        pending: 'border-gray-300',
        in_progress: 'border-blue-500',
        blocked: 'border-red-500',
        review: 'border-yellow-500',
        approved: 'border-green-400',
        completed: 'border-green-600',
        failed: 'border-red-600',
      }
      
      nodeDiv.classList.add(statusColors[node.status] || 'border-gray-300')
      
      nodeDiv.innerHTML = `
        <div class="text-sm font-semibold">${node.name}</div>
        <div class="text-xs text-gray-600 mt-1">
          Status: ${node.status}
          ${node.estimate_hours ? ` | ${node.estimate_hours}h` : ''}
        </div>
        ${node.requires_approval ? '<div class="text-xs text-orange-600 mt-1">⚠️ Requires Approval</div>' : ''}
      `
      
      container.appendChild(nodeDiv)
      nodeElements.set(node.id, nodeDiv)
    })

    // Display edges as text (simple approach)
    if (graph.edges.length > 0) {
      const edgesDiv = document.createElement('div')
      edgesDiv.className = 'mt-4 p-3 bg-gray-50 rounded'
      edgesDiv.innerHTML = '<div class="text-sm font-semibold mb-2">Dependencies:</div>'
      
      const edgesList = document.createElement('ul')
      edgesList.className = 'text-xs text-gray-600 space-y-1'
      
      graph.edges.forEach(edge => {
        const fromNode = graph.nodes.find(n => n.id === edge.from)
        const toNode = graph.nodes.find(n => n.id === edge.to)
        
        if (fromNode && toNode) {
          const li = document.createElement('li')
          li.textContent = `${fromNode.name} → ${toNode.name}`
          edgesList.appendChild(li)
        }
      })
      
      edgesDiv.appendChild(edgesList)
      container.appendChild(edgesDiv)
    }

  }, [graph])

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!graph) {
    return <div className="text-center text-gray-500 py-8">No dependency data available</div>
  }

  return (
    <div>
      <div 
        ref={canvasRef}
        className="border border-gray-200 rounded-lg p-4 bg-gray-50 min-h-[200px]"
      />
      <div className="mt-4 text-xs text-gray-600">
        <p>Legend: Blue = In Progress, Yellow = Review, Green = Approved/Completed, Red = Blocked/Failed</p>
        <p className="mt-1">Note: This is a simplified visualization. For complex graphs, consider using a dedicated graph library.</p>
      </div>
    </div>
  )
}

export default PlanCanvas
