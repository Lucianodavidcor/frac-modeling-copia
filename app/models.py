from typing import Optional
from sqlmodel import SQLModel, Field

class ProjectBase(SQLModel):
    name: str
    description: Optional[str] = None

class Project(ProjectBase, table=True):
    """Representa un sector de reservorio cerrado[cite: 30, 91]."""
    id: Optional[int] = Field(default=None, primary_key=True)