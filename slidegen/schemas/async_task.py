"""Async task response schemas"""

from typing import Any

from pydantic import BaseModel, Field


class AsyncTaskResponse(BaseModel):
    """Response for async task submission"""

    task_id: str = Field(..., description="Unique task ID")
    status: str = Field(..., description="Task status (e.g., 'pending', 'processing', 'completed', 'failed')")
    message: str = Field(..., description="Status message")
    result: dict[str, Any] | None = Field(default=None, description="Task result (available when completed)")
