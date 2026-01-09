"""Stream event schemas for SSE"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StreamEventType(str, Enum):
    """Stream event types"""

    # Workflow lifecycle events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_ERROR = "workflow_error"

    # Step events
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_ERROR = "step_error"

    # Loop events (for section generation progress)
    LOOP_STARTED = "loop_started"
    LOOP_ITERATION_STARTED = "loop_iteration_started"
    LOOP_ITERATION_COMPLETED = "loop_iteration_completed"
    LOOP_COMPLETED = "loop_completed"

    # Content events
    CONTENT_GENERATED = "content_generated"

    # Progress events
    PROGRESS = "progress"


class StreamEvent(BaseModel):
    """Base stream event"""

    event: StreamEventType = Field(..., description="Event type")
    data: dict[str, Any] | None = Field(default=None, description="Event data")
    message: str | None = Field(default=None, description="Human-readable message")


class WorkflowStartedEvent(BaseModel):
    """Event sent when workflow starts"""

    event: str = Field(default=StreamEventType.WORKFLOW_STARTED.value)
    workflow_name: str | None = Field(default=None, description="Workflow name")
    run_id: str | None = Field(default=None, description="Run ID")
    message: str = Field(default="Workflow started")


class WorkflowCompletedEvent(BaseModel):
    """Event sent when workflow completes"""

    event: str = Field(default=StreamEventType.WORKFLOW_COMPLETED.value)
    content: str | None = Field(default=None, description="Generated content")
    message: str = Field(default="Workflow completed")


class WorkflowErrorEvent(BaseModel):
    """Event sent when workflow fails"""

    event: str = Field(default=StreamEventType.WORKFLOW_ERROR.value)
    error: str = Field(..., description="Error message")
    message: str = Field(default="Workflow failed")


class StepStartedEvent(BaseModel):
    """Event sent when a step starts"""

    event: str = Field(default=StreamEventType.STEP_STARTED.value)
    step_name: str = Field(..., description="Step name")
    step_index: int | None = Field(default=None, description="Step index")
    message: str | None = Field(default=None, description="Step description")


class StepCompletedEvent(BaseModel):
    """Event sent when a step completes"""

    event: str = Field(default=StreamEventType.STEP_COMPLETED.value)
    step_name: str = Field(..., description="Step name")
    step_index: int | None = Field(default=None, description="Step index")
    content: str | None = Field(default=None, description="Step output content")
    message: str | None = Field(default=None, description="Completion message")


class StepErrorEvent(BaseModel):
    """Event sent when a step fails"""

    event: str = Field(default=StreamEventType.STEP_ERROR.value)
    step_name: str = Field(..., description="Step name")
    error: str = Field(..., description="Error message")


class LoopProgressEvent(BaseModel):
    """Event sent during loop iteration (for section generation progress)"""

    event: str = Field(default=StreamEventType.LOOP_ITERATION_COMPLETED.value)
    iteration: int = Field(..., description="Current iteration (0-indexed)")
    total: int = Field(..., description="Total expected iterations")
    section_title: str | None = Field(default=None, description="Current section title")
    content: str | None = Field(default=None, description="Generated content for this section")
    message: str | None = Field(default=None, description="Progress message")


class ContentGeneratedEvent(BaseModel):
    """Event sent when content is generated"""

    event: str = Field(default=StreamEventType.CONTENT_GENERATED.value)
    content_type: str = Field(..., description="Content type (outline, section, etc.)")
    content: str = Field(..., description="Generated content")
    message: str | None = Field(default=None, description="Description")


class ProgressEvent(BaseModel):
    """General progress event"""

    event: str = Field(default=StreamEventType.PROGRESS.value)
    stage: str = Field(..., description="Current stage")
    progress: float = Field(..., description="Progress percentage (0-100)")
    message: str | None = Field(default=None, description="Progress message")


# Type alias for all possible stream events
StreamEventT = (
    ProgressEvent
    | StepStartedEvent
    | StepCompletedEvent
    | WorkflowStartedEvent
    | WorkflowCompletedEvent
    | WorkflowErrorEvent
    | ContentGeneratedEvent
    | LoopProgressEvent
)
