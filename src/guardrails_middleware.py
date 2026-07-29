"""
Guardrails Middleware for FactoryOps AI Agent.
Implements input/output validation as middleware using LangChain callbacks.
"""

import logging
from typing import Dict, Any, Optional, List
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

logger = logging.getLogger(__name__)


# ============================================================================
# Input Guardrails Middleware
# ============================================================================

class InputGuardrailsMiddleware:
    """
    Validates user inputs before they reach the agent.
    Enforces constraints on:
    - Input length (2-2000 characters)
    - Content safety (no dangerous patterns)
    - Format validity
    """

    # Dangerous patterns that should be blocked
    DANGEROUS_PATTERNS = [
        "delete all",
        "shutdown",
        "bypass safety",
        "ignore warning",
        "force execute",
        "rm -rf",
        "drop table",
        "exec(",
        "eval(",
        "__import__",
    ]

    # Allowed machine ID pattern
    MACHINE_ID_PATTERN = r"^[A-Z]{2,3}-\d{3}$"

    @staticmethod
    def validate_user_input(user_input: str) -> Dict[str, Any]:
        """
        Middleware validation for user input.

        Args:
            user_input: Raw user input

        Returns:
            Dict with validated input and status

        Raises:
            ValueError: If input fails validation
        """
        if not user_input or not isinstance(user_input, str):
            raise ValueError("Input must be a non-empty string")

        user_input = user_input.strip()

        # Length validation
        if len(user_input) < 2:
            raise ValueError("Input too short (minimum 2 characters)")
        if len(user_input) > 2000:
            raise ValueError("Input too long (maximum 2000 characters)")

        # Content safety validation
        input_lower = user_input.lower()
        for pattern in InputGuardrailsMiddleware.DANGEROUS_PATTERNS:
            if pattern in input_lower:
                logger.warning(f"Dangerous pattern detected in input: {pattern}")
                raise ValueError(f"Input contains dangerous pattern: {pattern}")

        logger.info(f"Input passed guardrails validation ({len(user_input)} chars)")
        return {
            "status": "valid",
            "input": user_input,
            "length": len(user_input)
        }


# ============================================================================
# Tool Input Guardrails Middleware
# ============================================================================

class ToolInputGuardrailsMiddleware:
    """
    Validates tool inputs during agent execution.
    Enforces constraints on tool-specific parameters.
    """

    @staticmethod
    def validate_tool_input(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Middleware validation for tool inputs.

        Args:
            tool_name: Name of the tool being called
            tool_input: Input arguments to the tool

        Returns:
            Validated tool input

        Raises:
            ValueError: If tool input fails validation
        """
        logger.debug(f"Validating {tool_name} input: {tool_input}")

        if tool_name == "check_machine_status":
            return ToolInputGuardrailsMiddleware._validate_machine_status(tool_input)
        elif tool_name == "lookup_error_code":
            return ToolInputGuardrailsMiddleware._validate_error_code(tool_input)
        elif tool_name == "request_approval":
            return ToolInputGuardrailsMiddleware._validate_approval(tool_input)
        elif tool_name == "create_maintenance_ticket":
            return ToolInputGuardrailsMiddleware._validate_ticket(tool_input)
        else:
            logger.warning(f"Unknown tool: {tool_name}")
            return tool_input

    @staticmethod
    def _validate_machine_status(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate check_machine_status input."""
        machine_id = tool_input.get("machine_id", "")
        if not machine_id or len(machine_id) > 10:
            raise ValueError(f"Invalid machine_id: {machine_id}")
        logger.debug(f"Machine status input validated: {machine_id}")
        return tool_input

    @staticmethod
    def _validate_error_code(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate lookup_error_code input."""
        error_code = tool_input.get("error_code", "")
        if not error_code or len(error_code) > 5:
            raise ValueError(f"Invalid error_code: {error_code}")
        logger.debug(f"Error code input validated: {error_code}")
        return tool_input

    @staticmethod
    def _validate_approval(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate request_approval input."""
        machine_id = tool_input.get("machine_id", "")
        description = tool_input.get("description", "")
        priority = tool_input.get("priority", "")

        if not machine_id:
            raise ValueError("machine_id is required")
        if not description or len(description) < 10:
            raise ValueError("description must be at least 10 characters")
        if priority not in ["low", "medium", "high", "critical"]:
            raise ValueError(f"invalid priority: {priority}")

        logger.debug(f"Approval input validated: {machine_id} ({priority})")
        return tool_input

    @staticmethod
    def _validate_ticket(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate create_maintenance_ticket input."""
        machine_id = tool_input.get("machine_id", "")
        description = tool_input.get("description", "")
        priority = tool_input.get("priority", "")

        if not machine_id:
            raise ValueError("machine_id is required")
        if not description or len(description) < 10:
            raise ValueError("description must be at least 10 characters")
        if priority not in ["low", "medium", "high", "critical"]:
            raise ValueError(f"invalid priority: {priority}")

        logger.debug(f"Ticket input validated: {machine_id} ({priority})")
        return tool_input


# ============================================================================
# Output Guardrails Middleware
# ============================================================================

class OutputGuardrailsMiddleware:
    """
    Validates agent responses before returning to user.
    Enforces response quality and safety.
    """

    @staticmethod
    def validate_response(response: str) -> Dict[str, Any]:
        """
        Middleware validation for agent responses.

        Args:
            response: Agent response text

        Returns:
            Dict with validated response and status

        Raises:
            ValueError: If response fails validation
        """
        if not response:
            raise ValueError("Response is empty")

        response = str(response).strip()

        # Minimum length
        if len(response) < 5:
            raise ValueError("Response too short (minimum 5 characters)")

        # Dangerous patterns in response
        dangerous_patterns = [
            "delete",
            "drop",
            "shutdown",
            "bypass",
        ]
        response_lower = response.lower()
        for pattern in dangerous_patterns:
            if pattern in response_lower and len(response) < 100:
                logger.warning(f"Dangerous pattern in short response: {pattern}")
                raise ValueError(f"Response contains dangerous pattern: {pattern}")

        logger.info(f"Response passed guardrails validation ({len(response)} chars)")
        return {
            "status": "valid",
            "response": response,
            "length": len(response)
        }


# ============================================================================
# LangChain Callback Handler (Middleware Integration)
# ============================================================================

class GuardrailsCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler that enforces guardrails during agent execution.
    Validates inputs before tool calls and outputs after LLM responses.
    """

    name = "guardrails_middleware"

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Called before tool execution - validate tool input."""
        tool_name = serialized.get("name", "unknown")
        try:
            # Parse tool input
            import json
            try:
                tool_input = json.loads(input_str)
            except:
                tool_input = {"input": input_str}

            # Validate tool input
            ToolInputGuardrailsMiddleware.validate_tool_input(tool_name, tool_input)
            logger.info(f"Tool {tool_name} input passed guardrails")
        except ValueError as e:
            logger.error(f"Tool {tool_name} input failed guardrails: {str(e)}")
            raise

    def on_llm_end(self, response, **kwargs: Any) -> None:
        """Called after LLM response - validate output."""
        try:
            if hasattr(response, 'generations') and response.generations:
                for generation_list in response.generations:
                    if generation_list:
                        for generation in generation_list:
                            text = generation.text if hasattr(generation, 'text') else str(generation)
                            OutputGuardrailsMiddleware.validate_response(text)
                            logger.info("LLM response passed guardrails")
        except ValueError as e:
            logger.error(f"LLM response failed guardrails: {str(e)}")
            raise

    def on_agent_action(self, action, **kwargs: Any) -> None:
        """Called when agent selects an action - validate tool call."""
        try:
            tool_name = action.tool
            tool_input = action.tool_input
            ToolInputGuardrailsMiddleware.validate_tool_input(tool_name, tool_input)
            logger.info(f"Agent action {tool_name} passed guardrails")
        except ValueError as e:
            logger.error(f"Agent action failed guardrails: {str(e)}")
            raise
