"""
Ticket Management Panel - View and analyze tickets via MCP
"""

import streamlit as st
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_ticket_server import (
    get_all_tickets,
    get_tickets_by_machine,
    get_open_tickets,
    get_tickets_by_priority,
    get_ticket_stats,
    search_tickets,
    ticket_summary,
)
import json

st.set_page_config(
    page_title="Ticket Management",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📋 Maintenance Tickets – MCP Management")
st.markdown("View, search, and analyze all maintenance tickets managed via MCP")
st.divider()

# Get all tickets
all_tickets = get_all_tickets()

if not all_tickets:
    st.info("No tickets found in the system. Tickets will appear here when created via MCP approval.")
else:
    # Summary statistics
    stats = get_ticket_stats()
    open_count = len(get_open_tickets())
    critical_count = len(get_tickets_by_priority("critical"))
    high_count = len(get_tickets_by_priority("high"))

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Tickets", len(all_tickets))

    with col2:
        st.metric("Open Tickets", open_count, delta=None)

    with col3:
        st.metric("🔴 Critical", critical_count)

    with col4:
        st.metric("🟠 High Priority", high_count)

    with col5:
        st.metric("Machines", len(stats["by_machine"]))

    st.divider()

    # View options
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🔍 Search",
        "🔴 Critical/High",
        "📖 Details",
        "📊 Statistics"
    ])

    # Tab 1: Overview
    with tab1:
        st.subheader("All Tickets")

        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                options=["All"] + sorted(stats["by_status"].keys()),
                key="status_filter"
            )

        with col2:
            priority_filter = st.selectbox(
                "Filter by Priority",
                options=["All"] + sorted(stats["by_priority"].keys()),
                key="priority_filter"
            )

        with col3:
            machine_filter = st.selectbox(
                "Filter by Machine",
                options=["All"] + sorted(stats["by_machine"].keys()),
                key="machine_filter"
            )

        # Apply filters
        filtered_tickets = all_tickets

        if status_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t["status"] == status_filter]

        if priority_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t["priority"] == priority_filter]

        if machine_filter != "All":
            filtered_tickets = [t for t in filtered_tickets if t["machine_id"] == machine_filter]

        # Display tickets
        if filtered_tickets:
            for i, ticket in enumerate(filtered_tickets):
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

                    with col1:
                        st.markdown(f"**🎫 {ticket['ticket_id']}**")
                        st.caption(f"Machine: {ticket['machine_id']}")

                    with col2:
                        priority_emoji = "🔴" if ticket["priority"] == "critical" else "🟠" if ticket["priority"] == "high" else "🟡" if ticket["priority"] == "medium" else "🟢"
                        st.markdown(f"{priority_emoji} **{ticket['priority'].upper()}**")
                        st.caption(f"Status: {ticket['status'].upper()}")

                    with col3:
                        st.markdown(f"**Created:**")
                        st.caption(ticket['created_at'][:10])

                    with col4:
                        if st.button("View", key=f"view_ticket_{i}"):
                            st.session_state[f"show_ticket_{i}"] = True

                    # Show description
                    st.caption(f"📝 {ticket['description']}")

                    # Show full details if requested
                    if st.session_state.get(f"show_ticket_{i}"):
                        st.divider()
                        st.markdown("### Full Details")
                        st.json(ticket)

                        # Export option
                        st.download_button(
                            "📥 Export as JSON",
                            data=json.dumps(ticket, indent=2),
                            file_name=f"ticket_{ticket['ticket_id']}.json",
                            mime="application/json",
                            key=f"export_{i}"
                        )
        else:
            st.info("No tickets match the selected filters.")

    # Tab 2: Search
    with tab2:
        st.subheader("Search Tickets")

        search_query = st.text_input(
            "Search by machine ID, description, or ticket ID:",
            placeholder="e.g., MX-204, hydraulic, TKT-2026..."
        )

        if search_query:
            results = search_tickets(search_query)

            if results:
                st.success(f"Found {len(results)} matching ticket(s)")

                for i, ticket in enumerate(results):
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.markdown(f"**🎫 {ticket['ticket_id']}** - {ticket['machine_id']}")
                            st.write(f"Priority: {ticket['priority'].upper()} | Status: {ticket['status'].upper()}")
                            st.write(f"Description: {ticket['description']}")

                        with col2:
                            if st.button("Details", key=f"search_details_{i}"):
                                st.session_state[f"search_show_{i}"] = True

                        if st.session_state.get(f"search_show_{i}"):
                            st.divider()
                            st.json(ticket)
            else:
                st.warning("No tickets found matching your search.")
        else:
            st.info("Enter a search term to find tickets.")

    # Tab 3: Critical/High Priority
    with tab3:
        st.subheader("🔴 Critical & 🟠 High Priority Tickets")

        critical = get_tickets_by_priority("critical")
        high = get_tickets_by_priority("high")

        if critical or high:
            if critical:
                st.markdown("### 🔴 Critical Priority")
                for i, ticket in enumerate(critical):
                    with st.container(border=True):
                        st.markdown(f"**{ticket['ticket_id']}** - {ticket['machine_id']}")
                        st.write(ticket['description'])
                        st.caption(f"Created: {ticket['created_at']} | Assigned: {ticket.get('assigned_to', 'Unassigned')}")

            if high:
                st.markdown("### 🟠 High Priority")
                for i, ticket in enumerate(high):
                    with st.container(border=True):
                        st.markdown(f"**{ticket['ticket_id']}** - {ticket['machine_id']}")
                        st.write(ticket['description'])
                        st.caption(f"Created: {ticket['created_at']} | Assigned: {ticket.get('assigned_to', 'Unassigned')}")
        else:
            st.success("✅ No critical or high priority tickets.")

    # Tab 4: Detailed View
    with tab4:
        st.subheader("Ticket Details")

        ticket_id = st.selectbox(
            "Select a ticket to view details:",
            options=[t["ticket_id"] for t in all_tickets],
            key="detail_select"
        )

        selected_ticket = next((t for t in all_tickets if t["ticket_id"] == ticket_id), None)

        if selected_ticket:
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"## {selected_ticket['ticket_id']}")
                st.markdown(f"**Machine:** {selected_ticket['machine_id']}")
                st.markdown(f"**Status:** {selected_ticket['status'].upper()}")
                st.markdown(f"**Priority:** {selected_ticket['priority'].upper()}")

            with col2:
                st.markdown("**Timeline**")
                st.write(f"Created: {selected_ticket['created_at']}")
                st.write(f"Updated: {selected_ticket['updated_at']}")

            st.divider()

            st.markdown("### Description")
            st.write(selected_ticket['description'])

            st.markdown("### Metadata")
            metadata = {
                "ticket_id": selected_ticket["ticket_id"],
                "machine_id": selected_ticket["machine_id"],
                "priority": selected_ticket["priority"],
                "status": selected_ticket["status"],
                "assigned_to": selected_ticket.get("assigned_to", "Unassigned"),
                "created_at": selected_ticket["created_at"],
                "updated_at": selected_ticket["updated_at"],
                "source": selected_ticket.get("source", "unknown"),
            }
            st.json(metadata)

            # Export
            st.divider()
            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    "📥 Export as JSON",
                    data=json.dumps(selected_ticket, indent=2),
                    file_name=f"ticket_{ticket_id}.json",
                    mime="application/json"
                )

            with col2:
                st.download_button(
                    "📄 Export as Text",
                    data=str(selected_ticket),
                    file_name=f"ticket_{ticket_id}.txt",
                    mime="text/plain"
                )

    # Tab 5: Statistics
    with tab5:
        st.subheader("Ticket Statistics")

        # Overall stats
        st.markdown("### Overall Statistics")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**By Status**")
            status_data = stats["by_status"]
            for status, count in status_data.items():
                st.write(f"{status.capitalize()}: {count}")

        with col2:
            st.markdown("**By Priority**")
            priority_data = stats["by_priority"]
            for priority, count in priority_data.items():
                emoji = "🔴" if priority == "critical" else "🟠" if priority == "high" else "🟡" if priority == "medium" else "🟢"
                st.write(f"{emoji} {priority.capitalize()}: {count}")

        with col3:
            st.markdown("**Top Machines**")
            machine_data = sorted(stats["by_machine"].items(), key=lambda x: x[1], reverse=True)[:5]
            for machine, count in machine_data:
                st.write(f"{machine}: {count}")

        st.divider()

        # Machine breakdown
        st.markdown("### Tickets by Machine")
        machine_stats = stats["by_machine"]

        machines_sorted = sorted(machine_stats.items(), key=lambda x: x[1], reverse=True)

        for machine, count in machines_sorted:
            machine_tickets = get_tickets_by_machine(machine)
            status_breakdown = {}
            for ticket in machine_tickets:
                status = ticket.get("status", "unknown")
                status_breakdown[status] = status_breakdown.get(status, 0) + 1

            with st.container(border=True):
                st.write(f"**{machine}**: {count} ticket(s)")
                st.write(f"Status: {status_breakdown}")

st.divider()
st.markdown("""
### 📋 MCP Ticket Management Features
- ✅ **Create Tickets** via MCP approval flow
- ✅ **Search Tickets** by machine, description, or ID
- ✅ **View Details** with full metadata
- ✅ **Filter** by status and priority
- ✅ **Statistics** across all machines
- ✅ **Export** tickets as JSON or text
- ✅ **Persistent** storage in `data/maintenance_tickets.json`
""")
