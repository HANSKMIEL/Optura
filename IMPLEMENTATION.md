# Optura MVP - Implementation Guide

## Overview

This document describes the complete MVP implementation of Optura, an AI-powered development orchestration platform that breaks down high-level project goals into testable, auditable tasks with built-in guardrails.

## Architecture

### Backend (FastAPI + SQLAlchemy + SQLite)

```
backend/
├── app/
│   ├── agents/          # AI agents with LLM integration
│   │   ├── base.py              # BaseAgent with OpenAI client
│   │   ├── planner.py           # Converts goals to task plans
│   │   ├── spec_generator.py   # Creates machine-readable specs
│   │   └── verifier.py          # Static analysis & security checks
│   ├── api/             # FastAPI routes
│   │   ├── projects.py          # Project CRUD + generate-plan
│   │   ├── tasks.py             # Task management + approval workflow
│   │   ├── artifacts.py         # File upload/verify
│   │   └── orchestrator.py      # Critical path, dependency graph
│   ├── models/          # SQLAlchemy ORM models
│   │   ├── project.py           # Project with status/risk
│   │   ├── task.py              # Task + TaskDependency
│   │   ├── artifact.py          # Immutable artifact storage
│   │   └── audit.py             # Audit trail
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # Business logic
│   │   ├── orchestrator.py      # networkx graph algorithms
│   │   ├── sandbox.py           # Docker-based test runner
│   │   ├── file_validator.py   # Upload security
│   │   └── audit.py             # Logging service
│   ├── prompts/         # LLM prompts
│   ├── config.py        # Settings management
│   ├── database.py      # SQLAlchemy setup
│   └── main.py          # FastAPI app
└── tests/               # Pytest test suite
```

### Frontend (React + TypeScript + Tailwind CSS)

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx        # Project list
│   │   ├── NewProject.tsx       # Project creation form
│   │   └── ProjectDetail.tsx    # Task management view
│   ├── components/
│   │   ├── TaskCard.tsx         # Task display with actions
│   │   ├── PlanCanvas.tsx       # Dependency visualization
│   │   └── ApprovalModal.tsx    # Human approval UI
│   ├── services/
│   │   └── api.ts               # Axios API client
│   ├── types/
│   │   └── index.ts             # TypeScript interfaces
│   ├── App.tsx          # React Router setup
│   └── main.tsx         # Entry point
```

### Sandbox (Docker)

```
sandbox/
├── Dockerfile.python    # Python 3.11 + pytest
└── Dockerfile.node      # Node 18 + jest
```

## Key Features

### 1. AI-Powered Planning

**PlannerAgent** converts high-level goals into structured task plans:

```python
# Example: Generate plan for a project
planner = PlannerAgent()
plan = planner.generate_plan(
    project_name="Build REST API",
    goal="Implement secure REST API with authentication",
    description="FastAPI with JWT auth",
    acceptance_criteria=["API works", "Auth secure", "Tests pass"]
)
# Returns: { tasks: [...], risk_level: "medium", estimated_total_hours: 10.0 }
```

**Fallback**: If OpenAI API key not configured, uses deterministic 3-task template:
1. Research and Requirements (requires approval)
2. Implementation
3. Testing and Validation (requires approval)

### 2. Machine-Readable Specifications

**SpecGeneratorAgent** creates detailed specs with test cases:

```python
spec_gen = SpecGeneratorAgent()
spec = spec_gen.generate_spec(
    task_name="User Authentication",
    task_description="Implement JWT authentication",
    project_context="REST API project",
    inputs={"email": "string", "password": "string"},
    outputs={"token": "JWT string"},
    tests=[{"type": "unit", "description": "Test login endpoint"}]
)
# Returns comprehensive spec with inputs, outputs, test_cases, edge_cases, security_requirements
```

### 3. Critical Guardrails (ENFORCED)

#### Spec Binding
Tasks cannot be approved without a machine-readable spec:

```python
# POST /api/tasks/{id}/approve
# Returns 400 if spec is None:
# "Task cannot be approved without a machine-readable specification"
```

#### Test Gate
Tasks cannot be completed without test results:

```python
# POST /api/tasks/{id}/complete
# Returns 400 if test_results is None:
# "Task cannot be completed without test results"
```

#### Human Approval Gate
Tasks with `requires_approval=True` must be explicitly approved:

```python
# POST /api/tasks/{id}/complete
# Returns 400 if not approved:
# "Task requires human approval before completion"
```

#### Confidence Threshold
Tasks with confidence < 0.5 are flagged for review (automatic in PlannerAgent fallback).

### 4. Orchestration

**Critical Path Calculation** using networkx:

```python
# GET /api/orchestrator/project/{id}/critical-path
{
  "critical_path": [
    {"task_id": 1, "name": "Research", "estimate_hours": 2.0},
    {"task_id": 2, "name": "Implementation", "estimate_hours": 4.0},
    {"task_id": 3, "name": "Testing", "estimate_hours": 2.0}
  ],
  "total_hours": 8.0
}
```

**Dependency Graph**:

```python
# GET /api/orchestrator/project/{id}/dependency-graph
{
  "nodes": [{"id": 1, "name": "Task 1", "status": "pending", ...}],
  "edges": [{"from": 1, "to": 2}]  # Task 2 depends on Task 1
}
```

**Next Actions**:

```python
# GET /api/orchestrator/project/{id}/next-actions
{
  "actionable": [/* tasks ready to start */],
  "needs_approval": [/* tasks waiting for review */],
  "blocked": [/* tasks blocked by dependencies */]
}
```

### 5. Audit Trail

Every significant action is logged:

```python
AuditService.log(
    db=db,
    project_id=1,
    action="task_approved",
    actor="john.doe",
    details={"task_id": 5, "reason": "Spec validated"},
    task_id=5
)
```

Retrieve audit log:

```python
# GET /api/projects/{id}/audit-log
{
  "logs": [
    {
      "id": 1,
      "action": "project_created",
      "actor": "system",
      "created_at": "2024-01-01T00:00:00Z",
      "details": {...}
    }
  ]
}
```

### 6. Artifact Management

**Upload with Security Checks**:

```python
# POST /api/artifacts/task/{task_id}
# - Validates file size (max 10MB)
# - Checks allowed extensions (.py, .js, .ts, etc.)
# - Detects path traversal attempts (../, URL-encoded variants)
# - Calculates SHA256 hash
# - Validates path safety with os.path.realpath()
# - Stores immutably with hash prefix
```

**Verification**:

```python
# POST /api/artifacts/{id}/verify
# Uses VerifierAgent to:
# - Run static analysis
# - Detect security issues (SQL injection, XSS, hardcoded secrets)
# - Check code quality
# Returns: {status: "pass|fail|warning", overall_score: 0.85, checks: [...]}
```

### 7. Sandboxed Test Execution

```python
sandbox = SandboxRunner()

# Python tests
result = sandbox.run_python_tests(
    code="def add(a, b): return a + b",
    tests="def test_add(): assert add(1, 2) == 3",
    timeout=60
)

# Node.js tests
result = sandbox.run_node_tests(
    code="function add(a, b) { return a + b; }",
    tests="test('add', () => expect(add(1, 2)).toBe(3));",
    timeout=60
)
```

**Security**:
- Isolated Docker containers
- Network disabled
- Memory limits (512MB)
- CPU limits
- Timeouts (60s default)
- Non-root user execution

## API Endpoints

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/projects/` | Create project |
| GET | `/api/projects/` | List projects |
| GET | `/api/projects/{id}` | Get project details |
| PATCH | `/api/projects/{id}` | Update project |
| DELETE | `/api/projects/{id}` | Delete project |
| POST | `/api/projects/{id}/generate-plan` | Generate task plan with AI |
| GET | `/api/projects/{id}/audit-log` | Get audit trail |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tasks/` | Create task |
| GET | `/api/tasks/{id}` | Get task details |
| GET | `/api/tasks/project/{id}` | List tasks for project |
| PATCH | `/api/tasks/{id}` | Update task |
| DELETE | `/api/tasks/{id}` | Delete task |
| POST | `/api/tasks/{id}/generate-spec` | Generate specification with AI |
| POST | `/api/tasks/{id}/approve` | Approve task (requires spec) |
| POST | `/api/tasks/{id}/reject` | Reject task with reason |
| POST | `/api/tasks/{id}/run-tests` | Execute tests in sandbox |
| POST | `/api/tasks/{id}/complete` | Complete task (requires tests + approval) |
| POST | `/api/tasks/dependencies` | Create task dependency |

### Artifacts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/artifacts/task/{id}` | Upload artifact (with security checks) |
| GET | `/api/artifacts/{id}` | Get artifact details |
| GET | `/api/artifacts/task/{id}` | List task artifacts |
| POST | `/api/artifacts/{id}/verify` | Verify artifact with AI |
| DELETE | `/api/artifacts/{id}` | Delete artifact |

### Orchestrator

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/orchestrator/project/{id}/critical-path` | Calculate critical path |
| GET | `/api/orchestrator/project/{id}/dependency-graph` | Get dependency graph |
| POST | `/api/orchestrator/project/{id}/reprioritize` | Reprioritize tasks |
| GET | `/api/orchestrator/project/{id}/next-actions` | Get actionable tasks |
| GET | `/api/orchestrator/project/{id}/status-summary` | Get project status |

## Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=sqlite:///./optura.db

# Security
SECRET_KEY=your-secret-key-change-in-production

# LLM (optional - fallback used if not set)
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# File Upload
MAX_UPLOAD_SIZE_MB=10
ALLOWED_EXTENSIONS=.py,.js,.ts,.tsx,.jsx,.json,.md,.txt,.yaml,.yml
UPLOAD_DIR=./uploads

# Sandbox
SANDBOX_TIMEOUT_SECONDS=60
SANDBOX_MEMORY_LIMIT_MB=512

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Debug
DEBUG=true
```

## Running the Application

### Development (Local)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Production (Docker Compose)

```bash
docker-compose up --build
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Testing

### Run Backend Tests

```bash
cd backend
pytest tests/ -v
```

**Current Status:** 8/8 tests passing

### Run Integration Test

```bash
cd backend
python -c "from app.main import app; from fastapi.testclient import TestClient; ..."
```

See integration test in commit history for full test script.

## Security

### Implemented Protections

1. **XSS Prevention**: Safe DOM manipulation (no innerHTML with user data)
2. **Path Traversal Protection**: 
   - Filename sanitization
   - URL-encoded pattern detection
   - Path safety validation with `os.path.realpath()`
3. **File Upload Security**:
   - Size limits (10MB default)
   - Extension whitelist
   - Content validation
   - SHA256 checksums
4. **Sandboxed Execution**:
   - Network isolation
   - Resource limits
   - Non-root containers
5. **Input Validation**: Pydantic schemas for all endpoints
6. **SQL Injection Protection**: SQLAlchemy ORM (no raw SQL)

### Security Scan Results

- **CodeQL**: 0 vulnerabilities
- **Manual Review**: All critical issues addressed

## Database Schema

### Project
- id, name, description, goal, acceptance_criteria (JSON)
- risk_level (enum: low/medium/high/critical)
- status (enum: draft/planning/in_progress/review/completed/archived)
- environment, deadline, created_by, created_at, updated_at

### Task
- id, project_id (FK), name, description
- inputs (JSON), outputs (JSON), tests (JSON), security_checks (JSON)
- estimate_hours, status, confidence_score
- requires_approval, approved_by, approved_at, rejection_reason
- order, spec (JSON), test_results (JSON)
- created_at, updated_at

### TaskDependency
- id, task_id (FK), depends_on_task_id (FK), created_at

### Artifact
- id, task_id (FK), filename, original_filename, file_path
- file_hash (SHA256), mime_type, size_bytes
- status (pending/verified/rejected), verification_result (JSON)
- created_at

### AuditLog
- id, project_id (FK), task_id, action, actor
- details (JSON), created_at

## Development Workflow

### 1. Create Project
```typescript
POST /api/projects/
{
  "name": "Build Authentication System",
  "description": "JWT-based auth for REST API",
  "goal": "Secure user authentication",
  "acceptance_criteria": ["Login works", "Tokens secure", "Tests pass"],
  "risk_level": "high"
}
```

### 2. Generate Plan
```typescript
POST /api/projects/1/generate-plan
// Creates tasks with dependencies
```

### 3. For Each Task
```typescript
// Generate spec
POST /api/tasks/1/generate-spec

// Upload code artifact
POST /api/artifacts/task/1

// Verify artifact
POST /api/artifacts/1/verify

// Run tests
POST /api/tasks/1/run-tests

// Approve (if required)
POST /api/tasks/1/approve
{ "approved_by": "john.doe" }

// Complete
POST /api/tasks/1/complete
```

### 4. Monitor Progress
```typescript
GET /api/orchestrator/project/1/status-summary
GET /api/orchestrator/project/1/critical-path
GET /api/orchestrator/project/1/next-actions
```

## Extending the System

### Add New Agent

1. Create `backend/app/agents/your_agent.py`:
```python
from .base import BaseAgent

class YourAgent(BaseAgent):
    def process(self, input_data):
        if not self.client:
            return self._fallback(input_data)
        
        response = self._call_llm(system_prompt, user_prompt)
        return self._parse_json_response(response)
    
    def _fallback(self, input_data):
        # Deterministic logic
        return {"result": "..."}
```

2. Export in `backend/app/agents/__init__.py`

3. Use in API route:
```python
agent = YourAgent()
result = agent.process(data)
```

### Add New API Endpoint

1. Create route in `backend/app/api/`:
```python
@router.post("/your-endpoint")
def your_endpoint(data: YourSchema, db: Session = Depends(get_db)):
    # Logic here
    return {"result": "..."}
```

2. Import in `backend/app/api/__init__.py`

3. Include in `backend/app/main.py`:
```python
app.include_router(your_module.router, prefix="/api/your-prefix", tags=["Your Tag"])
```

## Troubleshooting

### OpenAI API Not Working
- Check `OPENAI_API_KEY` in `.env`
- System will use deterministic fallbacks automatically

### Sandbox Tests Failing
- Ensure Docker is running
- Check Docker images exist: `docker images | grep optura-sandbox`
- Build images: `docker-compose build sandbox-python sandbox-node`

### Database Issues
- Delete `optura.db` and restart to recreate schema
- Check SQLAlchemy models match schemas

### CORS Errors
- Update `CORS_ORIGINS` in `.env`
- Restart backend after changes

## License

MIT License

## Contributing

See main README.md for contribution guidelines.
