# Optura

**AI-Powered Development Orchestration Platform**

Optura is an intelligent agent + programming activity tracker that intakes user requests, breaks them into fool-proof testable steps, tracks progress dynamically, verifies code/artifacts at each step, and prevents endless AI loops and hallucinations through guardrails, human checkpoints, and automated tests.

## Core Design Principles

- **Human-in-the-loop by default** — every action that affects production or sensitive data requires explicit human approval
- **Test-first, incremental work** — require unit tests and acceptance tests before implementation (TDD)
- **Small, verifiable steps** — break requests into atomic tasks with clear inputs, outputs, and success criteria
- **Observable, auditable state** — immutable artifact storage, checksums, and audit trail
- **Fail-safe defaults** — idempotency, retries, and human rollback actions

## Architecture

### Backend (FastAPI)
- RESTful API service with SQLAlchemy ORM
- Agent layer: Planner, Spec Generator, Verifier
- Orchestrator with dependency graph and critical path calculation
- Sandboxed test runner using Docker containers

### Frontend (React + TypeScript)
- Guided intake form for project creation
- Visual plan canvas showing task dependencies
- Step inspector with diff views
- Human approval UI for review gates

### Guardrails
- **Spec binding**: No execution without machine-readable spec
- **Test gate**: No code accepted without passing tests
- **Human approval gates**: Risky actions require explicit sign-off
- **Confidence thresholds**: Low-confidence proposals route to human review

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/HANSKMIEL/Optura.git
cd Optura
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Start all services:
```bash
docker-compose up --build
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup (Development)

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

## Project Structure

```
optura/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── agents/         # AI agents (Planner, Verifier, etc.)
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── prompts/        # LLM prompt templates
│   └── tests/              # Backend tests
├── frontend/               # React frontend
│   └── src/
│       ├── components/     # React components
│       ├── pages/          # Page components
│       ├── services/       # API client
│       └── types/          # TypeScript types
├── sandbox/                # Sandboxed execution environments
├── docker-compose.yml      # Multi-container setup
└── README.md
```

## API Documentation

Once running, visit http://localhost:8000/docs for interactive Swagger documentation.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/projects` | Create new project |
| GET | `/api/projects/{id}` | Get project details |
| POST | `/api/projects/{id}/generate-plan` | Generate AI plan |
| POST | `/api/tasks/{id}/approve` | Approve task |
| POST | `/api/tasks/{id}/run-tests` | Run sandboxed tests |
| GET | `/api/projects/{id}/critical-path` | Get critical path |

## License

MIT License

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.
