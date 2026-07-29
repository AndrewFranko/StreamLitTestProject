"""
MCP Server for Maintenance Ticket Management
Provides tools for creating, reading, updating, and deleting maintenance tickets
via the Model Context Protocol. Includes RAG pipeline for finding similar tickets.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, List, Dict

logger = logging.getLogger(__name__)

# Import RAG pipeline
try:
    from rag_pipeline import find_similar_tickets, refresh_rag_pipeline
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("RAG pipeline not available")

# Data file for tickets
TICKETS_FILE = Path("data/maintenance_tickets.json")
TICKETS_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_tickets() -> List[Dict[str, Any]]:
    """Load all maintenance tickets from file."""
    if not TICKETS_FILE.exists():
        return []

    try:
        with open(TICKETS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading tickets: {str(e)}")
        return []


def save_tickets(tickets: List[Dict[str, Any]]) -> None:
    """Save maintenance tickets to file and refresh RAG pipeline."""
    try:
        TICKETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TICKETS_FILE, "w", encoding="utf-8") as f:
            json.dump(tickets, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(tickets)} tickets")

        # Refresh RAG pipeline when tickets change
        if RAG_AVAILABLE:
            refresh_rag_pipeline()
    except Exception as e:
        logger.error(f"Error saving tickets: {str(e)}")
        raise


def get_similar_tickets(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """Find similar past tickets using RAG pipeline."""
    if not RAG_AVAILABLE:
        logger.warning("RAG pipeline not available")
        return []

    try:
        similar = find_similar_tickets(query, k=k)
        logger.info(f"Found {len(similar)} similar tickets for query: {query[:50]}...")
        return similar
    except Exception as e:
        logger.error(f"Error finding similar tickets: {e}")
        return []


def create_ticket(
    machine_id: str,
    description: str,
    priority: str = "medium",
    assigned_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new maintenance ticket.

    Args:
        machine_id: Machine ID (e.g., MX-204)
        description: Ticket description
        priority: Priority level (low, medium, high, critical)
        assigned_to: Optional technician name

    Returns:
        Created ticket with ID
    """
    # Validate priority
    valid_priorities = ["low", "medium", "high", "critical"]
    if priority.lower() not in valid_priorities:
        raise ValueError(f"Invalid priority. Must be one of: {', '.join(valid_priorities)}")

    # Validate description
    if not description or len(description.strip()) < 10:
        raise ValueError("Description must be at least 10 characters")

    # Load existing tickets
    tickets = load_tickets()

    # Create new ticket
    ticket = {
        "ticket_id": f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "machine_id": machine_id.upper(),
        "description": description.strip(),
        "priority": priority.lower(),
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "assigned_to": assigned_to,
        "notes": [],
        "source": "mcp_approval",
    }

    # Append and save
    tickets.append(ticket)
    save_tickets(tickets)

    # Find similar past tickets using RAG
    similar_tickets = get_similar_tickets(description, k=3)

    logger.info(f"Created ticket {ticket['ticket_id']} for {machine_id}")
    return {
        **ticket,
        "similar_tickets": similar_tickets
    }


def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific ticket by ID."""
    tickets = load_tickets()
    return next((t for t in tickets if t["ticket_id"] == ticket_id), None)


def get_tickets_by_machine(machine_id: str) -> List[Dict[str, Any]]:
    """Get all tickets for a specific machine."""
    tickets = load_tickets()
    return [t for t in tickets if t["machine_id"].upper() == machine_id.upper()]


def get_tickets_by_status(status: str) -> List[Dict[str, Any]]:
    """Get all tickets with a specific status."""
    tickets = load_tickets()
    return [t for t in tickets if t["status"].lower() == status.lower()]


def update_ticket(ticket_id: str, **updates) -> Dict[str, Any]:
    """Update a ticket with new data."""
    tickets = load_tickets()

    # Find and update ticket
    for i, ticket in enumerate(tickets):
        if ticket["ticket_id"] == ticket_id:
            # Update allowed fields
            allowed_fields = ["status", "assigned_to", "priority", "description"]
            for field in allowed_fields:
                if field in updates:
                    ticket[field] = updates[field]

            ticket["updated_at"] = datetime.now().isoformat()
            tickets[i] = ticket

            save_tickets(tickets)
            logger.info(f"Updated ticket {ticket_id}")
            return ticket

    raise ValueError(f"Ticket {ticket_id} not found")


def delete_ticket(ticket_id: str) -> bool:
    """Delete a ticket by ID."""
    tickets = load_tickets()
    original_count = len(tickets)

    tickets = [t for t in tickets if t["ticket_id"] != ticket_id]

    if len(tickets) == original_count:
        raise ValueError(f"Ticket {ticket_id} not found")

    save_tickets(tickets)
    logger.info(f"Deleted ticket {ticket_id}")
    return True


def get_all_tickets() -> List[Dict[str, Any]]:
    """Get all tickets."""
    return load_tickets()


def ticket_summary(ticket_id: str) -> str:
    """Get a human-readable summary of a ticket."""
    ticket = get_ticket(ticket_id)
    if not ticket:
        return f"Ticket {ticket_id} not found"

    return (
        f"**Ticket {ticket['ticket_id']}**\n"
        f"Machine: {ticket['machine_id']}\n"
        f"Status: {ticket['status'].upper()}\n"
        f"Priority: {ticket['priority'].upper()}\n"
        f"Description: {ticket['description']}\n"
        f"Created: {ticket['created_at']}\n"
        f"Assigned to: {ticket['assigned_to'] or 'Unassigned'}"
    )


def search_tickets(query: str) -> List[Dict[str, Any]]:
    """
    Search tickets by description or machine ID.

    Args:
        query: Search term (case-insensitive)

    Returns:
        List of matching tickets
    """
    tickets = load_tickets()
    query_lower = query.lower()

    results = [
        t for t in tickets
        if query_lower in t["description"].lower()
        or query_lower in t["machine_id"].lower()
        or query_lower in t.get("ticket_id", "").lower()
    ]

    return results


def get_tickets_by_priority(priority: str) -> List[Dict[str, Any]]:
    """Get all tickets with a specific priority level."""
    tickets = load_tickets()
    return [t for t in tickets if t.get("priority", t.get("severity", "")).lower() == priority.lower()]


def get_open_tickets() -> List[Dict[str, Any]]:
    """Get all open tickets."""
    return get_tickets_by_status("open")


def get_ticket_stats() -> Dict[str, Any]:
    """Get statistics about all tickets."""
    tickets = load_tickets()

    stats = {
        "total_tickets": len(tickets),
        "by_status": {},
        "by_priority": {},
        "by_machine": {}
    }

    for ticket in tickets:
        # By status
        status = ticket.get("status", "unknown")
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        # By priority
        priority = ticket.get("priority", "unknown")
        stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1

        # By machine
        machine = ticket.get("machine_id", "unknown")
        stats["by_machine"][machine] = stats["by_machine"].get(machine, 0) + 1

    return stats


def format_ticket_for_display(ticket: Dict[str, Any]) -> str:
    """Format a single ticket for display."""
    # Handle both 'priority' and 'severity' fields
    priority = ticket.get('priority') or ticket.get('severity', 'unknown')
    assigned = ticket.get('assigned_to') or ticket.get('assigned_technician') or 'Unassigned'

    return (
        f"🎫 **{ticket['ticket_id']}** | "
        f"Machine: {ticket['machine_id']} | "
        f"Status: {ticket['status'].upper()} | "
        f"Priority: {priority.upper()}\n"
        f"   Description: {ticket['description'][:80]}...\n"
        f"   Created: {ticket['created_at'][:10]} | "
        f"   Assigned: {assigned}"
    )


def format_tickets_list(tickets: List[Dict[str, Any]]) -> str:
    """Format multiple tickets for display."""
    if not tickets:
        return "No tickets found."

    result = f"Found {len(tickets)} ticket(s):\n\n"
    for ticket in tickets:
        result += format_ticket_for_display(ticket) + "\n"

    return result
