"""
Pydantic v2 models for FactoryOps AI Manufacturing Assistant.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class PriorityEnum(str, Enum):
    """Priority levels for maintenance tickets."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatusEnum(str, Enum):
    """Status of a maintenance ticket."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MachineStatusEnum(str, Enum):
    """Operating status of a machine."""
    RUNNING = "running"
    IDLE = "idle"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    STOPPED = "stopped"


class SeverityEnum(str, Enum):
    """Severity level for error codes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Ticket(BaseModel):
    """
    Maintenance ticket model.

    Attributes:
        id: Unique ticket identifier (optional for new tickets)
        machine_id: ID of the affected machine
        description: Description of the issue
        priority: Priority level (low, medium, high, critical)
        status: Current ticket status
        created_at: Timestamp when ticket was created
        updated_at: Timestamp when ticket was last updated
        created_by: User who created the ticket
        assigned_to: Technician assigned to the ticket (optional)
    """
    id: Optional[str] = Field(default=None, description="Ticket ID")
    machine_id: str = Field(..., description="Machine ID")
    description: str = Field(..., description="Issue description")
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM, description="Priority level")
    status: TicketStatusEnum = Field(default=TicketStatusEnum.PENDING, description="Ticket status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    created_by: str = Field(default="system", description="Creator user ID")
    assigned_to: Optional[str] = Field(default=None, description="Assigned technician")

    class Config:
        use_enum_values = False


class MachineStatus(BaseModel):
    """
    Current status of a manufacturing machine.

    Attributes:
        machine_id: Unique machine identifier
        status: Operating status (running, idle, maintenance, error, stopped)
        location: Physical location in plant
        last_maintenance: Date of last maintenance
        current_error_codes: List of active error codes
        uptime_percentage: Percentage of time machine is running
        last_seen: Timestamp of last status update
    """
    machine_id: str = Field(..., description="Machine ID")
    status: MachineStatusEnum = Field(..., description="Operating status")
    location: str = Field(..., description="Physical location")
    last_maintenance: datetime = Field(..., description="Date of last maintenance")
    current_error_codes: list[str] = Field(default_factory=list, description="Active error codes")
    uptime_percentage: float = Field(default=100.0, description="Uptime percentage")
    last_seen: datetime = Field(default_factory=datetime.utcnow, description="Last status update")

    class Config:
        use_enum_values = False


class ErrorCode(BaseModel):
    """
    Manufacturing error code reference.

    Attributes:
        code: Error code identifier (e.g., E01, E17)
        description: Human-readable error description
        severity: Severity level (low, medium, high)
        recommended_fix: Recommended action to resolve error
        common_causes: List of common causes (optional)
        requires_shutdown: Whether machine should be stopped immediately
    """
    code: str = Field(..., description="Error code")
    description: str = Field(..., description="Error description")
    severity: SeverityEnum = Field(..., description="Severity level")
    recommended_fix: str = Field(..., description="Recommended action")
    common_causes: Optional[list[str]] = Field(default=None, description="Common causes")
    requires_shutdown: bool = Field(default=False, description="Requires immediate shutdown")

    class Config:
        use_enum_values = False


class ToolResult(BaseModel):
    """
    Result of a tool invocation.

    Attributes:
        tool_name: Name of the tool that was invoked
        success: Whether the tool call succeeded
        data: Returned data from the tool (optional)
        error_message: Error message if tool call failed (optional)
        execution_time_ms: Time taken to execute tool in milliseconds
    """
    tool_name: str = Field(..., description="Tool name")
    success: bool = Field(..., description="Success status")
    data: Optional[Any] = Field(default=None, description="Returned data")
    error_message: Optional[str] = Field(default=None, description="Error message")
    execution_time_ms: float = Field(default=0.0, description="Execution time in milliseconds")


class ConversationMessage(BaseModel):
    """
    A message in the conversation history.

    Attributes:
        role: Role of message sender (user, assistant, system)
        content: Message content
        timestamp: When message was created
        metadata: Optional metadata (tool calls, etc.)
    """
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Optional metadata")
