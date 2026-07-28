"""
Tool definitions for FactoryOps AI Level 2 Agent.
Provides tool implementations for machine status checking, error code lookup,
maintenance ticket creation via MCP, and technician availability checking.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from langchain_core.tools import tool
from pydantic import BaseModel, Field, validator
from enum import Enum

# Import MCP ticket server
from src.mcp_ticket_server import (
    create_ticket as mcp_create_ticket,
    get_tickets_by_machine,
    get_all_tickets,
    ticket_summary,
    update_ticket,
    search_tickets,
    get_tickets_by_priority,
    get_tickets_by_status,
    get_open_tickets,
    get_ticket_stats,
    format_ticket_for_display,
    format_tickets_list,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Guardrails: Priority Enum & Input Validation Models
# ============================================================================

class PriorityLevel(str, Enum):
    """Ticket priority levels - guardrail enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MachineStatusInput(BaseModel):
    """Validated input for check_machine_status tool."""
    machine_id: str = Field(
        ...,
        description="Machine ID (e.g., MX-204)",
        min_length=4,
        max_length=10,
        pattern=r"^[A-Z]{2,3}-\d{3}$"
    )

    class Config:
        json_schema_extra = {
            "example": {"machine_id": "MX-204"}
        }


class ErrorCodeInput(BaseModel):
    """Validated input for lookup_error_code tool."""
    error_code: str = Field(
        ...,
        description="Error code (e.g., E17)",
        min_length=2,
        max_length=5,
        pattern=r"^[A-Z]\d{1,3}$"
    )

    class Config:
        json_schema_extra = {
            "example": {"error_code": "E17"}
        }


class ApprovalInput(BaseModel):
    """Validated input for request_approval tool."""
    machine_id: str = Field(
        ...,
        description="Machine ID",
        min_length=4,
        max_length=10,
        pattern=r"^[A-Z]{2,3}-\d{3}$"
    )
    description: str = Field(
        ...,
        description="Ticket description",
        min_length=10,
        max_length=500
    )
    priority: PriorityLevel = Field(
        ...,
        description="Ticket priority level"
    )

    @validator('description')
    def validate_description(cls, v):
        if not v or v.isspace():
            raise ValueError("Description cannot be empty or whitespace")
        if len(v) < 10:
            raise ValueError("Description must be at least 10 characters")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "MX-204",
                "description": "Hydraulic pressure loss detected, error E17",
                "priority": "high"
            }
        }


class TicketInput(BaseModel):
    """Validated input for create_maintenance_ticket tool."""
    machine_id: str = Field(
        ...,
        description="Machine ID",
        min_length=4,
        max_length=10,
        pattern=r"^[A-Z]{2,3}-\d{3}$"
    )
    description: str = Field(
        ...,
        description="Ticket description",
        min_length=10,
        max_length=500
    )
    priority: PriorityLevel = Field(
        ...,
        description="Ticket priority level"
    )

    @validator('description')
    def validate_description(cls, v):
        if not v or v.isspace():
            raise ValueError("Description cannot be empty or whitespace")
        if len(v) < 10:
            raise ValueError("Description must be at least 10 characters")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "MX-204",
                "description": "Hydraulic pressure loss detected, error E17",
                "priority": "high"
            }
        }


# ============================================================================
# Data Loading Utilities
# ============================================================================

def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load JSON data from file with error handling.

    Args:
        file_path: Path to JSON file

    Returns:
        List of dictionaries from JSON file, empty list if file not found

    Raises:
        json.JSONDecodeError: If file contains invalid JSON
    """
    try:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Data file not found: {file_path}")
            return []

        with open(path, "r") as f:
            data = json.load(f)
            logger.debug(f"Loaded {len(data)} records from {file_path}")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error loading {file_path}: {str(e)}")
        raise


def save_json_data(file_path: str, data: List[Dict[str, Any]]) -> None:
    """
    Save JSON data to file with pretty formatting.

    Args:
        file_path: Path to JSON file
        data: List of dictionaries to save

    Raises:
        IOError: If file cannot be written
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(data)} records to {file_path}")
    except Exception as e:
        logger.error(f"Error saving {file_path}: {str(e)}")
        raise


# ============================================================================
# Input Validation Functions
# ============================================================================

def validate_machine_id(machine_id: str) -> bool:
    """
    Validate machine ID format and existence.

    Machine IDs follow pattern: [2-3 uppercase letters]-[3 digits]
    Examples: MX-201, WD-105, PK-089

    Args:
        machine_id: Machine ID to validate

    Returns:
        True if machine exists and format is valid

    Raises:
        ValueError: If machine_id format is invalid or machine not found
    """
    if not machine_id or not isinstance(machine_id, str):
        raise ValueError("Machine ID must be a non-empty string")

    # Validate format
    parts = machine_id.split("-")
    if len(parts) != 2 or not parts[1].isdigit() or len(parts[1]) != 3:
        raise ValueError(
            f"Invalid machine ID format: {machine_id}. "
            f"Expected format: XYZ-###, e.g., MX-201"
        )

    # Check if machine exists
    machines = load_json_data("data/machines.json")
    machine_ids = [m["id"] for m in machines]
    if machine_id not in machine_ids:
        raise ValueError(
            f"Machine {machine_id} not found. "
            f"Available machines: {', '.join(machine_ids)}"
        )

    return True


def validate_error_code(error_code: str) -> bool:
    """
    Validate error code format and existence.

    Error codes follow pattern: E + 2 digits
    Examples: E01, E17, E99

    Args:
        error_code: Error code to validate

    Returns:
        True if error code exists and format is valid

    Raises:
        ValueError: If error_code format is invalid or not found
    """
    if not error_code or not isinstance(error_code, str):
        raise ValueError("Error code must be a non-empty string")

    if not (error_code.startswith("E") and len(error_code) == 3 and error_code[1:].isdigit()):
        raise ValueError(
            f"Invalid error code format: {error_code}. "
            f"Expected format: E## (e.g., E17)"
        )

    # Check if error code exists
    error_codes = load_json_data("data/error_codes.json")
    error_code_values = [ec["code"] for ec in error_codes]
    if error_code not in error_code_values:
        raise ValueError(
            f"Error code {error_code} not found in database. "
            f"Available codes: {', '.join(sorted(error_code_values))}"
        )

    return True


def validate_priority(priority: str) -> bool:
    """
    Validate maintenance ticket priority level.

    Args:
        priority: Priority level (low, medium, high, critical)

    Returns:
        True if priority is valid

    Raises:
        ValueError: If priority is invalid
    """
    valid_priorities = ["low", "medium", "high", "critical"]
    if priority.lower() not in valid_priorities:
        raise ValueError(
            f"Invalid priority: {priority}. "
            f"Must be one of: {', '.join(valid_priorities)}"
        )
    return True


def validate_specialty(specialty: str) -> bool:
    """
    Validate technician specialty.

    Args:
        specialty: Technician specialty (electrical, hydraulic, mechanical, general)

    Returns:
        True if specialty is valid

    Raises:
        ValueError: If specialty is invalid
    """
    valid_specialties = ["electrical", "hydraulic", "mechanical", "general"]
    if specialty.lower() not in valid_specialties:
        raise ValueError(
            f"Invalid specialty: {specialty}. "
            f"Must be one of: {', '.join(valid_specialties)}"
        )
    return True


# ============================================================================
# Tool: check_machine_status
# ============================================================================

@tool(args_schema=MachineStatusInput)
def check_machine_status(machine_id: str) -> Dict[str, Any]:
    """
    Check the current operational status of a machine.

    This tool retrieves real-time or near-real-time machine status including
    operational state, temperature, runtime hours, and any active error codes.

    Args:
        machine_id: ID of the machine (e.g., MX-201, WD-105)

    Returns:
        Dictionary containing:
            - id: Machine identifier
            - name: Human-readable machine name
            - type: Machine type/category
            - location: Physical location in plant
            - status: Current status (operational, idle, error, maintenance)
            - temperature: Current operating temperature (°C/°F)
            - runtime_hours: Total accumulated runtime
            - error_code: Active error code (if status=error)
            - last_maintenance: Date of last maintenance
            - maintenance_interval_days: Days until next maintenance due

    Raises:
        ValueError: If machine_id is invalid or not found

    Example:
        >>> check_machine_status("MX-201")
        {
            'id': 'MX-201',
            'name': 'CNC Milling Machine A',
            'status': 'operational',
            'temperature': 72,
            ...
        }
    """
    try:
        # Input validation via Pydantic guardrail (args_schema)
        validated = MachineStatusInput(machine_id=machine_id)
        machine_id = validated.machine_id

        # Load machine data
        machines = load_json_data("data/machines.json")

        # Find machine
        for machine in machines:
            if machine["id"] == machine_id:
                logger.info(f"Machine status retrieved: {machine_id} - {machine['status']}")
                return machine

        # Should not reach here if validate_machine_id works correctly
        raise ValueError(f"Machine {machine_id} not found")

    except ValueError as e:
        logger.warning(f"Machine status check failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking machine {machine_id}: {str(e)}")
        raise


# ============================================================================
# Tool: lookup_error_code
# ============================================================================

@tool(args_schema=ErrorCodeInput)
def lookup_error_code(error_code: str) -> Dict[str, Any]:
    """
    Look up detailed information about a machine error code.

    This tool provides comprehensive error diagnostics including severity level,
    symptom description, and recommended corrective actions.

    Args:
        error_code: Error code to look up (e.g., E17, E34)

    Returns:
        Dictionary containing:
            - code: Error code identifier
            - severity: Severity level (low, medium, high, critical)
            - description: Technical description of the error
            - symptom: Observable symptoms indicating this error
            - recommended_action: Maintenance action to resolve the error

    Raises:
        ValueError: If error_code is invalid or not found

    Example:
        >>> lookup_error_code("E17")
        {
            'code': 'E17',
            'severity': 'high',
            'description': 'Hydraulic pressure loss in main cylinder',
            'symptom': 'Machine unable to generate full clamping force',
            'recommended_action': 'Inspect hydraulic lines...'
        }
    """
    try:
        # Validate error code
        validate_error_code(error_code)

        # Load error codes
        error_codes = load_json_data("data/error_codes.json")

        # Find error code
        for ec in error_codes:
            if ec["code"] == error_code:
                logger.info(f"Error code retrieved: {error_code} - {ec['severity']}")
                return ec

        # Should not reach here if validate_error_code works correctly
        raise ValueError(f"Error code {error_code} not found")

    except ValueError as e:
        logger.warning(f"Error code lookup failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error looking up {error_code}: {str(e)}")
        raise


# ============================================================================
# Tool: create_maintenance_ticket
# ============================================================================

@tool(args_schema=TicketInput)
def create_maintenance_ticket(
    machine_id: str,
    description: str,
    priority: str
) -> Dict[str, Any]:
    """
    Create a new maintenance ticket for a machine via MCP.

    This tool generates a maintenance request that will be routed to appropriate
    technicians based on the machine type and required specialty. Uses Model Context
    Protocol (MCP) for data persistence and management.

    GUARDRAILS:
        - Does NOT forcibly shut down machines
        - Always requires human review for critical-severity actions
        - Logs all ticket creation for audit trail
        - Validates all inputs before ticket creation
        - MCP ensures data consistency and auditability

    Args:
        machine_id: ID of the machine requiring maintenance (e.g., MX-201)
        description: Detailed description of the maintenance issue
        priority: Priority level (low, medium, high, critical)

    Returns:
        Dictionary containing:
            - ticket_id: Unique ticket identifier (auto-generated via MCP)
            - machine_id: Associated machine
            - description: Issue description
            - priority: Ticket priority
            - created_at: Timestamp of creation
            - status: Current ticket status (open)
            - assigned_to: Assigned technician (if any)
            - source: MCP ticket creation

    Raises:
        ValueError: If inputs are invalid or validation fails

    Example:
        >>> create_maintenance_ticket("MX-204", "Hydraulic leak at main cylinder", "high")
        {
            'ticket_id': 'TKT-20260728120000',
            'machine_id': 'MX-204',
            'priority': 'high',
            'status': 'open',
            'created_at': '2026-07-28T12:00:00...',
            'source': 'mcp_approval'
        }
    """
    try:
        # Validate inputs
        validate_machine_id(machine_id)
        validate_priority(priority)

        if not description or len(description.strip()) < 10:
            raise ValueError(
                "Description must be at least 10 characters long and provide details"
            )

        if len(description) > 500:
            raise ValueError("Description cannot exceed 500 characters")

        # Create ticket via MCP
        ticket = mcp_create_ticket(
            machine_id=machine_id,
            description=description.strip(),
            priority=priority.lower(),
            assigned_to=None
        )

        logger.info(
            f"Maintenance ticket created via MCP: {ticket['ticket_id']} - "
            f"Machine: {machine_id}, Priority: {priority}"
        )

        return {
            "ticket_id": ticket["ticket_id"],
            "machine_id": ticket["machine_id"],
            "description": ticket["description"],
            "priority": ticket["priority"],
            "created_at": ticket["created_at"],
            "status": ticket["status"],
            "assigned_to": ticket.get("assigned_to"),
            "source": ticket.get("source", "mcp_approval")
        }

    except ValueError as e:
        logger.warning(f"MCP ticket creation failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating ticket via MCP: {str(e)}")
        raise


# ============================================================================
# Tool: check_technician_availability
# ============================================================================

@tool
def check_technician_availability(specialty: str) -> List[Dict[str, Any]]:
    """
    Check available technicians with a specific specialty.

    This tool queries the technician database to find maintenance staff
    currently available for assignment to maintenance tasks.

    Args:
        specialty: Required technician specialty (electrical, hydraulic, mechanical, general)

    Returns:
        List of available technicians with the requested specialty:
            - technician_id: Unique identifier
            - name: Technician name
            - specialties: List of specialties
            - status: Current status (available, busy, on_leave)
            - current_task: Currently assigned task (if busy)

    Raises:
        ValueError: If specialty is invalid

    Example:
        >>> check_technician_availability("hydraulic")
        [
            {
                'technician_id': 'T002',
                'name': 'Maria Garcia',
                'specialties': ['hydraulic', 'mechanical'],
                'status': 'available',
                'current_task': None
            }
        ]
    """
    try:
        # Validate specialty
        validate_specialty(specialty)

        # Load technicians
        technicians = load_json_data("data/technicians.json")

        # Filter for requested specialty and available status
        available = [
            tech for tech in technicians
            if (specialty.lower() in [s.lower() for s in tech.get("specialties", [])] or
                specialty.lower() == "general")
            and tech.get("status", "").lower() == "available"
        ]

        logger.info(
            f"Technician availability check: {specialty} - "
            f"Found {len(available)} available"
        )

        return available

    except ValueError as e:
        logger.warning(f"Technician availability check failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking technician availability: {str(e)}")
        raise


# ============================================================================
# ============================================================================
# Approval Tool (Human-in-the-loop)
# ============================================================================

@tool(args_schema=ApprovalInput)
def request_approval(machine_id: str, description: str, priority: str) -> Dict[str, Any]:
    """
    Request supervisor approval for a maintenance ticket via MCP.
    Pauses agent execution for human review before ticket creation.

    When user approves, agent will call create_maintenance_ticket with these details.

    Args:
        machine_id: ID of affected machine (e.g., MX-204)
        description: Detailed issue description
        priority: Priority level (low, medium, high, critical)

    Returns:
        Dictionary with approval request status and metadata for UI display
    """
    try:
        # Validate inputs
        validate_machine_id(machine_id)
        validate_priority(priority)

        if not description or len(description.strip()) < 10:
            raise ValueError("Description must be at least 10 characters")

        logger.info(f"Approval requested for {machine_id}: {priority} priority via MCP")

        # Return approval metadata that UI will display
        return {
            "machine_id": machine_id,
            "description": description.strip(),
            "priority": priority,
            "status": "pending_approval",
            "requested_at": datetime.now().isoformat(),
            "message": f"⚠️ Awaiting supervisor approval to create {priority} priority ticket for {machine_id}",
            "action": "create_ticket_on_approval"  # Signal agent to create ticket when approved
        }
    except Exception as e:
        logger.error(f"Approval request failed: {str(e)}")
        raise


# ============================================================================
# Memory/Context Management (MCP-compatible storage)
# ============================================================================

class ConversationMemory:
    """
    Simple in-memory conversation store for agent memory.
    Can be extended to use external MCP (Model Context Protocol) backends.
    """
    def __init__(self, max_messages: int = 50):
        self.messages: List[Dict[str, Any]] = []
        self.max_messages = max_messages
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "context": {}
        }

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to memory."""
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(msg)

        # Keep memory bounded
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        logger.debug(f"Added {role} message to memory (total: {len(self.messages)})")

    def get_context(self, num_messages: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation context messages as list."""
        return self.messages[-num_messages:]

    def save_to_file(self, file_path: str):
        """Save memory to JSON file (MCP backend)."""
        try:
            data = {
                "metadata": self.metadata,
                "messages": self.messages
            }
            save_json_data(file_path, data)
            logger.info(f"Saved conversation memory to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save memory: {str(e)}")

    def clear(self):
        """Clear conversation memory."""
        self.messages = []
        logger.info("Conversation memory cleared")


# ============================================================================
# Tool: Query Tickets via MCP
# ============================================================================

@tool
def get_machine_tickets(machine_id: str) -> str:
    """
    Get all maintenance tickets for a specific machine via MCP.

    This tool retrieves the complete ticket history for a machine,
    including open, in-progress, and resolved tickets.

    Args:
        machine_id: Machine ID (e.g., MX-204)

    Returns:
        Formatted list of tickets for the machine
    """
    try:
        validate_machine_id(machine_id)
        tickets = get_tickets_by_machine(machine_id)
        result = f"**Tickets for Machine {machine_id}:**\n\n"
        result += format_tickets_list(tickets)
        return result
    except Exception as e:
        logger.error(f"Error querying tickets for {machine_id}: {str(e)}")
        raise


@tool
def search_ticket_database(search_query: str) -> str:
    """
    Search ticket database by description or machine ID via MCP.

    This tool performs a full-text search across all tickets to find
    relevant maintenance records.

    Args:
        search_query: Search term (e.g., "hydraulic", "MX-204", "leak")

    Returns:
        Formatted list of matching tickets
    """
    try:
        if not search_query or len(search_query.strip()) < 2:
            raise ValueError("Search query must be at least 2 characters")

        tickets = search_tickets(search_query)
        result = f"**Search Results for '{search_query}':**\n\n"
        result += format_tickets_list(tickets)
        return result
    except Exception as e:
        logger.error(f"Error searching tickets: {str(e)}")
        raise


@tool
def get_open_maintenance_tickets() -> str:
    """
    Get all open (unresolved) maintenance tickets via MCP.

    Returns a list of all currently open tickets that need attention.

    Returns:
        Formatted list of open tickets
    """
    try:
        tickets = get_open_tickets()
        result = f"**Open Maintenance Tickets ({len(tickets)} total):**\n\n"
        result += format_tickets_list(tickets)
        return result
    except Exception as e:
        logger.error(f"Error retrieving open tickets: {str(e)}")
        raise


@tool
def get_high_priority_tickets() -> str:
    """
    Get all high and critical priority tickets via MCP.

    Returns all tickets marked as high or critical priority
    that require immediate attention.

    Returns:
        Formatted list of high-priority tickets
    """
    try:
        high_tickets = get_tickets_by_priority("high")
        critical_tickets = get_tickets_by_priority("critical")
        all_priority = high_tickets + critical_tickets

        result = f"**High/Critical Priority Tickets ({len(all_priority)} total):**\n\n"
        result += format_tickets_list(all_priority)
        return result
    except Exception as e:
        logger.error(f"Error retrieving high-priority tickets: {str(e)}")
        raise


@tool
def view_all_tickets() -> str:
    """
    Get all maintenance tickets via MCP with summary statistics.

    Returns all tickets in the database along with statistical breakdown.

    Returns:
        Formatted list of all tickets with stats
    """
    try:
        tickets = get_all_tickets()
        stats = get_ticket_stats()

        result = f"**All Maintenance Tickets ({tickets.__len__()} total):**\n\n"

        # Show statistics
        result += "**Statistics:**\n"
        result += f"- By Status: {stats['by_status']}\n"
        result += f"- By Priority: {stats['by_priority']}\n"
        result += f"- By Machine: {stats['by_machine']}\n\n"

        # Show all tickets
        result += "**Ticket List:**\n\n"
        result += format_tickets_list(tickets)

        return result
    except Exception as e:
        logger.error(f"Error retrieving all tickets: {str(e)}")
        raise


@tool
def get_ticket_details(ticket_id: str) -> str:
    """
    Get detailed information about a specific ticket via MCP.

    Args:
        ticket_id: Ticket ID (e.g., TKT-20260728120000)

    Returns:
        Detailed ticket summary
    """
    try:
        return ticket_summary(ticket_id)
    except Exception as e:
        logger.error(f"Error retrieving ticket {ticket_id}: {str(e)}")
        raise


@tool
def get_machine_ticket_statistics(machine_id: str) -> str:
    """
    Get ticket statistics for a specific machine via MCP.

    Args:
        machine_id: Machine ID (e.g., MX-204)

    Returns:
        Statistics about tickets for the machine
    """
    try:
        validate_machine_id(machine_id)
        tickets = get_tickets_by_machine(machine_id)

        # Calculate stats
        by_status = {}
        by_priority = {}

        for ticket in tickets:
            status = ticket.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

            priority = ticket.get("priority", "unknown")
            by_priority[priority] = by_priority.get(priority, 0) + 1

        result = f"**Ticket Statistics for {machine_id}:**\n\n"
        result += f"Total Tickets: {len(tickets)}\n"
        result += f"By Status: {by_status}\n"
        result += f"By Priority: {by_priority}\n"

        return result
    except Exception as e:
        logger.error(f"Error getting ticket stats for {machine_id}: {str(e)}")
        raise


# ============================================================================
# Tool Definition Export
# ============================================================================

def get_all_tools() -> List:
    """
    Get all available tools for agent registration.

    Returns:
        List of tool functions for AgentExecutor
        Includes MCP tools for ticket management and comprehensive retrieval
    """
    return [
        # Machine & error tools
        check_machine_status,
        lookup_error_code,
        check_technician_availability,
        request_approval,

        # MCP Ticket Creation
        create_maintenance_ticket,  # Creates tickets via MCP

        # MCP Ticket Retrieval & Search
        get_machine_tickets,              # Get all tickets for a machine
        search_ticket_database,           # Search tickets by keyword
        get_open_maintenance_tickets,     # Get all open tickets
        get_high_priority_tickets,        # Get high/critical tickets
        view_all_tickets,                 # Get all tickets with stats
        get_ticket_details,               # Get specific ticket details
        get_machine_ticket_statistics,    # Get stats for a machine
    ]
