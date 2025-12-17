import logging
from typing import List, Dict, Any, Tuple
import networkx as nx
from sqlalchemy.orm import Session
from ..models.task import Task, TaskDependency, TaskStatus

logger = logging.getLogger(__name__)


class OrchestratorService:
    """Service for managing task dependencies and orchestration."""

    @staticmethod
    def calculate_critical_path(project_id: int, db: Session) -> Dict[str, Any]:
        """Calculate the critical path for a project using networkx."""
        tasks = db.query(Task).filter(Task.project_id == project_id).all()
        dependencies = db.query(TaskDependency).join(
            Task, TaskDependency.task_id == Task.id
        ).filter(Task.project_id == project_id).all()

        if not tasks:
            return {
                "critical_path": [],
                "total_hours": 0,
                "project_id": project_id
            }

        # Build directed graph
        G = nx.DiGraph()

        # Add nodes with task info
        for task in tasks:
            G.add_node(
                task.id,
                name=task.name,
                estimate_hours=task.estimate_hours or 1.0,
                status=task.status.value
            )

        # Add edges for dependencies
        for dep in dependencies:
            G.add_edge(dep.depends_on_task_id, dep.task_id)

        # Check for cycles
        if not nx.is_directed_acyclic_graph(G):
            logger.error(f"Circular dependency detected in project {project_id}")
            return {
                "critical_path": [],
                "total_hours": 0,
                "project_id": project_id,
                "error": "Circular dependency detected"
            }

        # Find critical path using longest path algorithm
        try:
            # Add weights (negative for longest path)
            for node in G.nodes():
                G.nodes[node]['weight'] = -(G.nodes[node]['estimate_hours'])

            # Find all paths from start nodes (no predecessors) to end nodes (no successors)
            start_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
            end_nodes = [n for n in G.nodes() if G.out_degree(n) == 0]

            longest_path = []
            max_duration = 0

            for start in start_nodes:
                for end in end_nodes:
                    if nx.has_path(G, start, end):
                        path = nx.shortest_path(G, start, end, weight='weight')
                        duration = sum(G.nodes[n]['estimate_hours'] for n in path)
                        if duration > max_duration:
                            max_duration = duration
                            longest_path = path

            # Build response
            critical_path = [
                {
                    "task_id": task_id,
                    "name": G.nodes[task_id]['name'],
                    "estimate_hours": G.nodes[task_id]['estimate_hours'],
                    "status": G.nodes[task_id]['status']
                }
                for task_id in longest_path
            ]

            return {
                "critical_path": critical_path,
                "total_hours": max_duration,
                "project_id": project_id
            }

        except Exception as e:
            logger.error(f"Error calculating critical path: {e}")
            return {
                "critical_path": [],
                "total_hours": 0,
                "project_id": project_id,
                "error": str(e)
            }

    @staticmethod
    def get_dependency_graph(project_id: int, db: Session) -> Dict[str, Any]:
        """Get the dependency graph for visualization."""
        tasks = db.query(Task).filter(Task.project_id == project_id).all()
        dependencies = db.query(TaskDependency).join(
            Task, TaskDependency.task_id == Task.id
        ).filter(Task.project_id == project_id).all()

        nodes = [
            {
                "id": task.id,
                "name": task.name,
                "status": task.status.value,
                "estimate_hours": task.estimate_hours,
                "requires_approval": task.requires_approval,
                "order": task.order
            }
            for task in tasks
        ]

        edges = [
            {
                "from": dep.depends_on_task_id,
                "to": dep.task_id
            }
            for dep in dependencies
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "project_id": project_id
        }

    @staticmethod
    def reprioritize(project_id: int, db: Session) -> Dict[str, Any]:
        """Reprioritize tasks based on dependencies and status."""
        tasks = db.query(Task).filter(Task.project_id == project_id).order_by(Task.order).all()

        # Simple reprioritization: blocked tasks go last
        priority_map = {
            TaskStatus.IN_PROGRESS: 0,
            TaskStatus.REVIEW: 1,
            TaskStatus.APPROVED: 2,
            TaskStatus.PENDING: 3,
            TaskStatus.BLOCKED: 4,
            TaskStatus.COMPLETED: 5,
            TaskStatus.FAILED: 6
        }

        sorted_tasks = sorted(tasks, key=lambda t: (priority_map.get(t.status, 10), t.order))

        # Update order
        changes = []
        for new_order, task in enumerate(sorted_tasks):
            if task.order != new_order:
                old_order = task.order
                task.order = new_order
                changes.append({
                    "task_id": task.id,
                    "name": task.name,
                    "old_order": old_order,
                    "new_order": new_order
                })

        db.commit()

        return {
            "project_id": project_id,
            "changes": changes,
            "total_tasks": len(tasks)
        }

    @staticmethod
    def suggest_next_actions(project_id: int, db: Session) -> Dict[str, Any]:
        """Suggest next actionable tasks."""
        tasks = db.query(Task).filter(Task.project_id == project_id).all()
        dependencies = db.query(TaskDependency).join(
            Task, TaskDependency.task_id == Task.id
        ).filter(Task.project_id == project_id).all()

        # Build dependency map
        blocked_by = {}
        for dep in dependencies:
            if dep.task_id not in blocked_by:
                blocked_by[dep.task_id] = []
            blocked_by[dep.task_id].append(dep.depends_on_task_id)

        # Find tasks that can be started
        actionable = []
        blocked = []
        needs_approval = []

        for task in tasks:
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.IN_PROGRESS]:
                continue

            # Check if all dependencies are completed
            if task.id in blocked_by:
                deps = blocked_by[task.id]
                dep_tasks = db.query(Task).filter(Task.id.in_(deps)).all()
                if all(t.status == TaskStatus.COMPLETED for t in dep_tasks):
                    if task.status == TaskStatus.REVIEW and task.requires_approval:
                        needs_approval.append({
                            "task_id": task.id,
                            "name": task.name,
                            "status": task.status.value
                        })
                    else:
                        actionable.append({
                            "task_id": task.id,
                            "name": task.name,
                            "status": task.status.value,
                            "estimate_hours": task.estimate_hours
                        })
                else:
                    blocked.append({
                        "task_id": task.id,
                        "name": task.name,
                        "blocked_by": [t.name for t in dep_tasks if t.status != TaskStatus.COMPLETED]
                    })
            else:
                # No dependencies
                if task.status == TaskStatus.REVIEW and task.requires_approval:
                    needs_approval.append({
                        "task_id": task.id,
                        "name": task.name,
                        "status": task.status.value
                    })
                else:
                    actionable.append({
                        "task_id": task.id,
                        "name": task.name,
                        "status": task.status.value,
                        "estimate_hours": task.estimate_hours
                    })

        return {
            "project_id": project_id,
            "actionable": actionable[:5],  # Top 5
            "needs_approval": needs_approval,
            "blocked": blocked[:5]
        }
