from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from .api import projects, tasks, artifacts, orchestrator

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Optura API",
    description="AI-Powered Development Orchestration Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(artifacts.router, prefix="/api/artifacts", tags=["Artifacts"])
app.include_router(orchestrator.router, prefix="/api/orchestrator", tags=["Orchestrator"])


@app.get("/")
async def root():
    return {"message": "Welcome to Optura API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
