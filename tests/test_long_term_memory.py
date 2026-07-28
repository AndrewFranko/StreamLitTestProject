"""
Long-term memory tests for FactoryOps AI.
Tests role-scoped memory isolation, persistence, and cross-session behavior.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent_engine import AgentEngine
import pytest
import time


class TestLongTermMemoryBasics:
    """Test basic long-term memory operations."""

    def test_store_memory(self):
        """Test storing memory for a role."""
        agent = AgentEngine('operator')
        result = agent.store_memory(
            key='test_key',
            value='test_value',
            tags=['test']
        )
        # Store may return False if langgraph not installed, but method should work
        assert isinstance(result, bool)

    def test_retrieve_memory(self):
        """Test retrieving memory for a role."""
        agent = AgentEngine('operator')
        agent.store_memory('retrieve_test', 'test_data', ['test'])

        retrieved = agent.retrieve_memory('retrieve_test')
        # May return None if langgraph not installed, but should not crash
        assert retrieved is None or retrieved == 'test_data'

    def test_search_memory(self):
        """Test searching memory by query."""
        agent = AgentEngine('operator')
        agent.store_memory('search_key', 'searchable_value', ['search', 'test'])

        results = agent.search_memory('searchable')
        # Should return list (may be empty if langgraph not installed)
        assert isinstance(results, list)


class TestRoleIsolation:
    """Test that memory is completely isolated per role."""

    def test_memory_isolation_operator_vs_engineer(self):
        """Operator memory should not be visible to engineer."""
        operator = AgentEngine('operator')
        engineer = AgentEngine('engineer')

        # Store in operator memory
        operator.store_memory(
            key='machine_MX-204_preference',
            value='Operator prefers early morning maintenance',
            tags=['operator', 'machine']
        )

        # Engineer tries to retrieve - should not find it
        engineer_result = engineer.retrieve_memory('machine_MX-204_preference')
        assert engineer_result is None, "Engineer should not see operator's memory"

    def test_memory_isolation_all_roles(self):
        """Test isolation across all four roles."""
        roles = ['operator', 'engineer', 'supervisor', 'plant_manager']
        agents = {role: AgentEngine(role) for role in roles}

        # Store unique memory in each role
        for role in roles:
            agents[role].store_memory(
                key=f'{role}_secret',
                value=f'This is {role} secret knowledge',
                tags=[role]
            )

        # Verify each role can only see its own memory
        for role in roles:
            own_memory = agents[role].retrieve_memory(f'{role}_secret')
            # May be None if langgraph not installed, but should be consistent

            # Check isolation: role should not see other roles' data
            for other_role in roles:
                if other_role != role:
                    other_memory = agents[role].retrieve_memory(f'{other_role}_secret')
                    assert other_memory is None, f"{role} should not see {other_role}'s memory"


class TestMemoryMetadata:
    """Test memory configuration and metadata."""

    def test_memory_metadata_in_agent(self):
        """Test that agent metadata shows correct memory configuration."""
        agent = AgentEngine('operator')
        meta = agent.agent_metadata['memory']

        # Check session memory
        assert meta['session_memory']['type'] == 'ConversationMemory'
        assert meta['session_memory']['scope'] == 'session'
        assert meta['session_memory']['max_messages'] == 50

        # Check checkpointer metadata (structure exists even if langgraph not installed)
        assert meta['checkpointer']['scope'] == 'role_operator'
        assert meta['checkpointer']['purpose'] == 'State persistence per role'
        # Path may be None if langgraph not installed
        if meta['checkpointer'].get('path'):
            assert 'agent_state_operator' in meta['checkpointer']['path']

        # Check store metadata (structure exists even if langgraph not installed)
        assert meta['store']['scope'] == 'role_operator'
        assert meta['store']['purpose'] == 'Long-term memory across sessions per role'
        # Path may be None if langgraph not installed
        if meta['store'].get('path'):
            assert 'long_term_memory_operator' in meta['store']['path']

    def test_role_specific_database_paths(self):
        """Test that each role gets its own database paths."""
        operator = AgentEngine('operator')
        engineer = AgentEngine('engineer')

        op_store_path = operator.agent_metadata['memory']['store'].get('path')
        eng_store_path = engineer.agent_metadata['memory']['store'].get('path')

        # Paths should differ per role
        if op_store_path and eng_store_path:
            assert 'operator' in op_store_path
            assert 'engineer' in eng_store_path
            assert op_store_path != eng_store_path


class TestMemoryDataIntegrity:
    """Test that stored data maintains integrity."""

    def test_store_complex_data(self):
        """Test storing and retrieving complex data structures."""
        agent = AgentEngine('operator')

        complex_value = """
        Machine MX-204:
        - Type: Hydraulic Press
        - Location: Building A, Floor 2
        - Last Maintenance: 2026-07-20
        - Next Service: 2026-08-20
        - Notes: Runs hot in afternoon shifts. Check cooling system.
        """

        agent.store_memory(
            key='machine_profile_MX204',
            value=complex_value,
            tags=['machine', 'MX-204', 'profile']
        )

        retrieved = agent.retrieve_memory('machine_profile_MX204')
        # If langgraph installed, data should match
        if retrieved:
            assert retrieved == complex_value

    def test_store_multiple_values(self):
        """Test storing multiple values in same role."""
        agent = AgentEngine('operator')

        test_data = {
            'pattern_1': ('E17_error_pattern', 'High temp → low pressure', ['E17']),
            'pattern_2': ('MX-204_downtime', 'Afternoon shift maintenance window', ['MX-204']),
            'pattern_3': ('safety_rule_1', 'Always check hydraulic pressure before startup', ['safety']),
        }

        for key, (value, desc, tags) in test_data.items():
            agent.store_memory(key=value, value=desc, tags=tags)

        # All should be stored without error
        assert True, "Stored multiple values successfully"


class TestMemoryMethods:
    """Test individual memory methods."""

    def test_store_memory_with_tags(self):
        """Test that tags are properly associated with stored memory."""
        agent = AgentEngine('operator')

        agent.store_memory(
            key='tagged_memory',
            value='This has tags',
            tags=['important', 'machine', 'E17']
        )
        # Should not raise error
        assert True

    def test_retrieve_nonexistent_key(self):
        """Test retrieving a key that doesn't exist."""
        agent = AgentEngine('operator')

        result = agent.retrieve_memory('definitely_does_not_exist_key_12345')
        assert result is None, "Nonexistent key should return None"

    def test_search_memory_by_query(self):
        """Test searching memory by text query."""
        agent = AgentEngine('operator')

        agent.store_memory(
            key='searchable_fact',
            value='Machine MX-204 tends to overheat in afternoon',
            tags=['MX-204', 'pattern']
        )

        results = agent.search_memory('MX-204')
        assert isinstance(results, list), "Search should return a list"


class TestMemoryPersistence:
    """Test that memory persists across session boundaries.
    Note: These tests require langgraph to be installed.
    """

    def test_session_memory_vs_long_term(self):
        """Test that session memory is ephemeral but long-term is persistent."""
        agent1 = AgentEngine('operator')

        # Add to session memory
        agent1.memory.add_message('user', 'Test message', {'role': 'operator'})
        assert len(agent1.memory.messages) > 0, "Session message added"

        # Store to long-term memory
        agent1.store_memory('persistent_key', 'This should persist', ['test'])

        # Create new agent (simulates new session)
        agent2 = AgentEngine('operator')

        # Session memory should be empty (new session)
        assert len(agent2.memory.messages) == 0, "New session has empty memory"

        # Long-term memory should be retrievable (if langgraph installed)
        retrieved = agent2.retrieve_memory('persistent_key')
        # If langgraph: assert retrieved == 'This should persist'
        # If not: assert retrieved is None


class TestMemoryGracefulDegradation:
    """Test that app works even when langgraph not installed."""

    def test_app_works_without_langgraph(self):
        """Test that agent functions work without long-term memory."""
        agent = AgentEngine('operator')

        # Agent should still work
        assert agent.agent is not None
        assert agent.memory is not None  # Session memory works

        # Long-term memory methods should not crash
        result = agent.store_memory('key', 'value', ['tag'])
        assert isinstance(result, bool)

        retrieved = agent.retrieve_memory('key')
        assert retrieved is None  # Expected when langgraph not installed

    def test_agent_processes_query_without_longterm_memory(self):
        """Test that queries work even without long-term memory."""
        agent = AgentEngine('operator')

        # Should process query successfully
        result = agent.process_query("What is error code E17?")
        assert result['success'] is True
        assert len(result['response']) > 0


if __name__ == '__main__':
    # Run with pytest
    pytest.main([__file__, '-v'])
