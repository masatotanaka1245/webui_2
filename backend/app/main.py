from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import get_current_development_user
from .open_webui import MockOpenWebUIClient
from .repositories import get_project, list_projects
from .schemas import DevelopmentUser, HealthResponse, ProjectDetail, ProjectListResponse

app = FastAPI(title="Open WebUI Business Portal API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=[],
)
app.state.open_webui_client = MockOpenWebUIClient()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", open_webui_client="mock")


@app.get("/api/v1/projects", response_model=ProjectListResponse)
def projects(_: DevelopmentUser = Depends(get_current_development_user)) -> ProjectListResponse:
    return ProjectListResponse(items=list_projects())


@app.get("/api/v1/projects/{project_id}", response_model=ProjectDetail)
def project_detail(
    project_id: str,
    _: DevelopmentUser = Depends(get_current_development_user),
) -> ProjectDetail:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
