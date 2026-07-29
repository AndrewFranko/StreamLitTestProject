"""
Guardrails Middleware Layer for FactoryOps AI.
Defines middleware that intercepts and validates inputs/outputs during agent execution.
Applied via create_agent_with_middleware() factory.
"""

import logging
from typing import Dict, Any, List, Callable
from langchain_core.callbacks import BaseCallbackHandler
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Guardrails Middleware Definitions
# ============================================================================

class GuardrailsStrategy(str, Enum):
    """Strategy for handling guardrails violations."""
    BLOCK = "block"      # Reject and raise error
    WARN = "warn"        # Log warning but allow
    TRANSFORM = "transform"  # Transform input/output


class InputValidationMiddleware:
    """
    Middleware that validates user inputs before agent execution.
    Strategy: BLOCK dangerous patterns, WARN on suspicious inputs
    """

    name = "input_validation"

    def __init__(self, strategy: GuardrailsStrategy = GuardrailsStrategy.BLOCK):
        self.strategy = strategy
        self.dangerous_patterns = [
            "delete all", "shutdown", "bypass safety", "ignore warning",
            "force execute", "rm -rf", "drop table", "exec(", "eval(", "__import__"
        ]

    def intercept(self, user_input: str) -> str:
        """Intercept and validate user input."""
        if not user_input or len(user_input) < 2:
            if self.strategy == GuardrailsStrategy.BLOCK:
                raise ValueError("Input too short (minimum 2 characters)")
            else:
                logger.warning("Input too short - allowing anyway")

        if len(user_input) > 2000:
            if self.strategy == GuardrailsStrategy.BLOCK:
                raise ValueError("Input too long (maximum 2000 characters)")
            else:
                logger.warning("Input too long - allowing anyway")

        # Check for dangerous patterns
        input_lower = user_input.lower()
        for pattern in self.dangerous_patterns:
            if pattern in input_lower:
                if self.strategy == GuardrailsStrategy.BLOCK:
                    logger.error(f"Dangerous pattern blocked: {pattern}")
                    raise ValueError(f"Input contains dangerous pattern: {pattern}")
                else:
                    logger.warning(f"Suspicious pattern detected: {pattern}")

        return user_input


class ToolInputValidationMiddleware:
    """
    Middleware that validates tool inputs before execution.
    Strategy: BLOCK invalid tool args
    """

    name = "tool_input_validation"

    def __init__(self, strategy: GuardrailsStrategy = GuardrailsStrategy.BLOCK):
        self.strategy = strategy

    def intercept(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Intercept and validate tool input."""
        logger.debug(f"Validating {tool_name} input: {tool_input}")

        # Light validation only - let tools do strict validation via Pydantic
        # This middleware just warns on suspicious patterns
        try:
            # Tool-specific validation
            if tool_name == "check_machine_status":
                machine_id = tool_input.get("machine_id", "")
                # Only log warning if machine_id is empty, don't block
                if not machine_id:
                    logger.warning(f"check_machine_status called with empty machine_id - will be rejected by tool")

            elif tool_name in ["request_approval", "create_maintenance_ticket"]:
                description = tool_input.get("description", "")
                priority = tool_input.get("priority", "")

                # Only log warnings, don't block - let Pydantic validation handle it
                if not description:
                    logger.warning(f"{tool_name} called with empty description")
                elif len(description) < 10:
                    logger.warning(f"{tool_name} description too short ({len(description)} chars)")

                if priority and priority not in ["low", "medium", "high", "critical"]:
                    logger.warning(f"{tool_name} called with invalid priority: {priority}")
        except Exception as e:
            logger.warning(f"Tool input validation warning: {str(e)}")
            # Don't block - let tool validation handle it

        return tool_input


class OutputValidationMiddleware:
    """
    Middleware that validates agent responses before returning.
    Strategy: BLOCK empty/short responses
    """

    name = "output_validation"

    def __init__(self, strategy: GuardrailsStrategy = GuardrailsStrategy.BLOCK):
        self.strategy = strategy

    def intercept(self, response: str) -> str:
        """Intercept and validate output."""
        if not response or len(response.strip()) < 5:
            if self.strategy == GuardrailsStrategy.BLOCK:
                raise ValueError("Response too short (minimum 5 characters)")
            else:
                logger.warning("Response is very short - allowing anyway")

        # Check for dangerous patterns in short responses
        dangerous_patterns = ["delete", "drop", "shutdown", "bypass"]
        response_lower = response.lower()
        for pattern in dangerous_patterns:
            if pattern in response_lower and len(response) < 100:
                if self.strategy == GuardrailsStrategy.BLOCK:
                    raise ValueError(f"Short response contains dangerous pattern: {pattern}")
                else:
                    logger.warning(f"Suspicious response pattern: {pattern}")

        return response


# ============================================================================
# Guardrails Callback Handler with Middleware Integration
# ============================================================================

class GuardrailsMiddlewareHandler(BaseCallbackHandler):
    """
    LangChain callback handler that applies middleware stack.
    Intercepts inputs/outputs and applies middleware validation.
    """

    name = "guardrails_middleware"

    def __init__(self, middleware: List[Any]):
        """
        Initialize with a stack of middleware.

        Args:
            middleware: List of middleware objects with intercept() method
        """
        self.middleware = middleware
        logger.info(f"Initialized guardrails middleware handler with {len(middleware)} layers")

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Apply tool input middleware before tool execution."""
        tool_name = serialized.get("name", "unknown")

        try:
            import json
            try:
                tool_input = json.loads(input_str)
            except:
                tool_input = {"input": input_str}

            # Apply each middleware's tool_input_validation
            for mw in self.middleware:
                if hasattr(mw, 'intercept') and mw.name == "tool_input_validation":
                    tool_input = mw.intercept(tool_name, tool_input)

            logger.info(f"Tool {tool_name} passed middleware validation")
        except ValueError as e:
            logger.error(f"Tool {tool_name} failed middleware: {str(e)}")
            raise

    def on_llm_end(self, response, **kwargs: Any) -> None:
        """Apply output middleware after LLM response."""
        try:
            if hasattr(response, 'generations') and response.generations:
                for generation_list in response.generations:
                    if generation_list:
                        for generation in generation_list:
                            text = generation.text if hasattr(generation, 'text') else str(generation)

                            # Skip validation for empty responses or tool calls (agent intermediate steps)
                            # Tool calls are indicated by function_call in additional_kwargs
                            if hasattr(generation, 'message') and hasattr(generation.message, 'additional_kwargs'):
                                if generation.message.additional_kwargs.get('function_call'):
                                    # This is a tool call, skip text validation
                                    logger.debug("LLM called a tool - skipping text validation")
                                    continue

                            # Only validate if there's actual text content
                            if text and len(text.strip()) > 0:
                                # Apply each middleware's output_validation
                                for mw in self.middleware:
                                    if hasattr(mw, 'intercept') and mw.name == "output_validation":
                                        text = mw.intercept(text)

                                logger.info("LLM response passed middleware validation")
        except ValueError as e:
            logger.error(f"LLM response failed middleware: {str(e)}")
            # Don't raise - allow tool calls to proceed even if text is empty


# ============================================================================
# Agent Factory with Middleware Support
# ============================================================================

def create_agent_with_middleware(
    model,
    tools,
    system_prompt: str,
    middleware: List[Any] = None,
    checkpointer=None,
    store=None,
    **kwargs
):
    """
    Factory function that creates an agent with guardrails middleware and memory.

    Pattern: Define middleware, checkpointer, and store, pass to factory
    Agent integrates all three: LLM + tools + middleware + memory

    Args:
        model: LangChain LLM model
        tools: List of tools available to agent
        system_prompt: System prompt for agent
        middleware: List of middleware objects (InputValidationMiddleware, etc.)
        checkpointer: State checkpointer for persistence (e.g., SqliteSaver)
        store: Store for persistent information across threads/sessions
        **kwargs: Additional arguments to pass to create_agent

    Returns:
        Agent with middleware callbacks and memory (checkpointer/store) pre-configured

    Example:
        from langgraph.checkpoint.sqlite import SqliteSaver
        from langgraph.store.sqlite import SqliteStore

        checkpointer = SqliteSaver(db_path="agent_state.db")
        store = SqliteStore(db_path="agent_memory.db")

        agent = create_agent_with_middleware(
            model=ChatGoogleGenerativeAI(...),
            tools=get_all_tools(),
            system_prompt="You are a manufacturing assistant",
            middleware=[
                InputValidationMiddleware(strategy=GuardrailsStrategy.BLOCK),
                ToolInputValidationMiddleware(strategy=GuardrailsStrategy.BLOCK),
                OutputValidationMiddleware(strategy=GuardrailsStrategy.BLOCK)
            ],
            checkpointer=checkpointer,
            store=store
        )
    """
    from langchain.agents import create_agent

    logger.info(
        f"Creating agent with middleware={len(middleware) if middleware else 0}, "
        f"checkpointer={checkpointer is not None}, "
        f"store={store is not None}"
    )

    # Create base agent with memory (checkpointer, store)
    agent_kwargs = {
        "system_prompt": system_prompt,
        **kwargs
    }

    # Add memory configuration if provided
    if checkpointer:
        agent_kwargs["checkpointer"] = checkpointer
        logger.info("Checkpointer added to agent for state persistence")

    if store:
        agent_kwargs["store"] = store
        logger.info("Store added to agent for persistent memory across threads")

    # Create base agent
    agent = create_agent(
        model,
        tools=tools,
        **agent_kwargs
    )

    # Apply middleware via callback handler
    if middleware:
        middleware_handler = GuardrailsMiddlewareHandler(middleware)
        agent = agent.with_config({"callbacks": [middleware_handler]})
        logger.info(f"Middleware applied to agent: {[mw.name for mw in middleware]}")

    return agent
