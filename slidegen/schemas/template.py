"""Template schemas"""

from pydantic import BaseModel, Field


class Template(BaseModel):
    """Presentation template information"""

    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template display name")
