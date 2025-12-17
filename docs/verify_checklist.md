# verify_checklist.md

## Doel
Een reproduceerbare stap-voor-stap checklist waarmee de coding-agent of engineer de volledige implementatie valideert: functionaliteit, tests, security, sandbox-verificatie, orchestrator en governance.

## 0 Voorwaarden
- Toegang tot repo, CI-omgeving en sandbox-runner.
- Test-account met reviewer-rechten (niet productie-admin).
- Verwachte tools: git, docker, docker-compose (of podman), python/node, pytest/jest, mypy/eslint, bandit/snyk of vergelijkbaar.

## 1 Clone en start
- git clone <repo-url> && cd <repo-dir>
- git checkout <feature-branch> of main voor baseline
- Start dev stack:
  - docker-compose up --build -d
- Controleer services:
  - docker ps
  - curl -sS http://localhost:8000/health
  - curl -sS http://localhost:3000 (frontend)
Verwacht: health endpoints OK; frontend bereikbaar.

## 2 Unit lint type checks
- Installeer deps:
  - pip install -r backend/requirements.txt
  - cd frontend && npm ci
- Run unit tests:
  - cd backend && pytest -q
  - cd frontend && npm test --silent
- Run linters/type checks:
  - mypy backend/app/ || echo "mypy not configured"
  - flake8 backend/app/ || cd frontend && npx eslint src/
Verwacht: exit code 0; noteer aantal tests en coverage.

## 3 Spec binding en JSON schema validatie
- Open backend/app/schemas/ voor Pydantic schemas
- Valideer dat ProjectCreate, TaskCreate schemas correct zijn
- Test via API:
  - curl -X POST http://localhost:8000/api/projects -H "Content-Type: application/json" -d '{"name": "Test", "goal": "Test goal"}'
Verwacht: validatie OK; response bevat project met id.

## 4 Intake → Plan flow end-to-end
- Maak nieuwe project via API:
  - curl -X POST http://localhost:8000/api/projects -H "Content-Type: application/json" -d '{"name": "Test Project", "goal": "Build a REST API", "acceptance_criteria": ["All tests pass", "Documentation complete"]}'
- Genereer plan:
  - curl -X POST http://localhost:8000/api/projects/<project_id>/generate-plan
- Controleer response: JSON met tasks, dependencies
- Inspecteer plan in UI: taken, tests, artifacts zichtbaar
Verwacht: plan bevat machine-readable tasks met tests en security_checks.

## 5 Test-first TDD verificatie
- Maak taak en genereer spec:
  - curl -X POST http://localhost:8000/api/tasks/<task_id>/generate-spec
- Controleer dat spec tests bevat
- Probeer taak te approven zonder spec - moet falen (guardrail)
- Probeer taak te completen zonder passing tests - moet falen (guardrail)
Verwacht: guardrails werken; test-first flow afdwingbaar.

## 6 Upload endpoint en artifact handling
- Upload sample artifact:
  - curl -F "file=@tests/fixtures/sample.py" http://localhost:8000/api/artifacts/task/<task_id>
- Controleer response: id, file_hash, status
- Verify artifact:
  - curl -X POST http://localhost:8000/api/artifacts/<artifact_id>/verify
Verwacht: file opgeslagen, checksum match, verification result aanwezig.

## 7 Sandbox runner en test-execution
- Run tests voor taak:
  - curl -X POST http://localhost:8000/api/tasks/<task_id>/run-tests
- Controleer output: test_results met passed/failed status
Verwacht: tests uitgevoerd in sandbox; resultaten opgeslagen.

## 8 Static analysis en security scans
- Run static security:
  - bandit -r backend/app/ || snyk test
  - cd frontend && npm audit --audit-level=high
- Secret scan:
  - trufflehog filesystem --path .
- Upload sanitization test:
  - Upload bestand met naam ../../etc/passwd en controleer server response (moet rejected worden)
Verwacht: geen secrets; upload sanitized; path traversal geblokkeerd.

## 9 Orchestrator en dynamic replanning
- Bekijk critical path:
  - curl http://localhost:8000/api/orchestrator/project/<project_id>/critical-path
- Bekijk dependency graph:
  - curl http://localhost:8000/api/orchestrator/project/<project_id>/dependency-graph
- Bekijk next actions:
  - curl http://localhost:8000/api/orchestrator/project/<project_id>/next-actions
- Reprioritize na status change:
  - curl -X POST http://localhost:8000/api/orchestrator/project/<project_id>/reprioritize
Verwacht: dependency graph correct, herplanning zichtbaar.

## 10 Human approval en audit logs
- Approve taak:
  - curl -X POST http://localhost:8000/api/tasks/<task_id>/approve -H "Content-Type: application/json" -d '{"approved_by": "reviewer@example.com"}'
- Query audit logs:
  - curl http://localhost:8000/api/projects/<project_id>/audit-log
- Controleer entries: plan generation, uploads, test runs, approvals met user ids en timestamps
Verwacht: volledige audit trail; approvals gelogd.

## 11 Status summary
- Bekijk project status:
  - curl http://localhost:8000/api/orchestrator/project/<project_id>/status-summary
Verwacht: totaal, pending, in_progress, completed, failed counts correct.

## 12 Governance checks
- Controleer confidence thresholds in backend/app/config.py
- Controleer dat low confidence (<0.5) taken flagged worden voor review
- Test rejection flow:
  - curl -X POST http://localhost:8000/api/tasks/<task_id>/reject -H "Content-Type: application/json" -d '{"rejected_by": "reviewer@example.com", "reason": "Needs more tests"}'

## 13 Eindacceptatie
- Demo: intake → plan → generate-spec → upload artifact → run-tests → approve → complete
- Documenteer afwijkingen en open remediation tickets

## Notities
- Scripts (`dev_start.sh`, `create_pr.sh`, `rollback.sh`) gepland voor v1.1
- Metrics endpoint en Grafana dashboard gepland voor v1.1
- Alert systeem (email/Slack) gepland voor v1.1
