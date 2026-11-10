from dataclasses import dataclass
from app.entity.project import Project


@dataclass(frozen=True)
class ProjectMetrics:
    project: Project
    shortlist_count: int
