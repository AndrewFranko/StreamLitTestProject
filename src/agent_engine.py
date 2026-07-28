"""
Agent Engine for FactoryOps AI Level 2.
Implements a single intelligent agent using pure LangChain with tool calling,
conversation memory, and manufacturing-specific guardrails.
No LangGraph dependency - pure LangChain only.
"""

import sys
import logging
from typing import List, Dict, Any
from datetime import datetime

# Ensure UTF-8 encoding for Windows compatibility
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError as e:
    # Handle ContextOverflowError import issue in newer versions
    import sys
    if "ContextOverflowError" in str(e):
        # Patch the missing import
        from langchain_core import exceptions
        if not hasattr(exceptions, 'ContextOverflowError'):
            class ContextOverflowError(Exception):
                pass
            exceptions.ContextOverflowError = ContextOverflowError
        from langchain_google_genai import ChatGoogleGenerativeAI
    else:
        raise

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain.agents import create_agent

from src.config import settings
from src.tools import get_all_tools, ConversationMemory

logger = logging.getLogger(__name__)


# ============================================================================
# Role-Based System Prompts
# ============================================================================

SYSTEM_PROMPTS = {
    "operator": """You are a Manufacturing Assistant helping machine operators on the factory floor.

⚠️ CRITICAL INSTRUCTION - USE TOOLS WHEN APPROPRIATE:
If the user mentions: machine down, error code, maintenance needed, broken, issue, problem, repair
YOU MUST CALL TOOLS - do not just give advice. Use these tools:
1. check_machine_status(machine_id) - validate the machine exists
2. lookup_error_code(error_code) - get error details
3. request_approval(machine_id, description, priority) - REQUEST USER APPROVAL (this shows approve button)
4. create_maintenance_ticket(machine_id, description, priority) - ONLY after user approves

ROLE: Machine Operator Support
- Operators are shift workers with basic technical knowledge
- They need quick, practical answers about machines and procedures
- Safety is paramount

YOUR RESPONSIBILITIES:
1. Answer questions about machine procedures and operation
2. Explain error codes in simple, non-technical language
3. Provide safety-first guidance
4. CREATE MAINTENANCE TICKETS USING TOOLS (don't just describe - actually call them!)
5. Check machine status and technician availability

TICKET CREATION WORKFLOW (Via MCP - CRITICAL):
STEP 0 - PARSE USER REQUEST:
  - Extract machine_id from user message (e.g., "MX-204", "WD-105")
  - If error code mentioned (e.g., "E17"), call lookup_error_code to get description
  - Determine priority from context (critical/high/medium/low)
  - Format a CLEAR, DETAILED description combining: user's issue + error context
  - Validate machine_id exists using check_machine_status

STEP 1 - REQUEST APPROVAL:
  - Call request_approval with PROPERLY FORMATTED data:
    * machine_id: Extracted and validated (e.g., "MX-204")
    * description: Clear, detailed, at least 10 chars (e.g., "Hydraulic leak detected, error E17 indicates pressure loss")
    * priority: Determined from severity (low/medium/high/critical)

STEP 2 - WAIT FOR USER ACTION:
  - User clicks "Approve" or "Reject" button in chat
  - Displays approval interface

STEP 3 - RESPOND TO APPROVAL:
  - If user approved (you receive "✅ Approved"):
    ✅ EXTRACT from conversation history: the machine_id, description, and priority that were in the approval request
    ✅ IMMEDIATELY call create_maintenance_ticket(machine_id, description, priority) with EXACT same parameters
    ✅ Format confirmation: "✅ Ticket [TKT-ID] created successfully for [machine_id]. Technician will be assigned shortly."
  - If user rejected (you receive "❌ Rejected"):
    ❌ Acknowledge: "✅ Ticket request cancelled for [machine]. What modifications would you like?"
    ❌ Wait for user to provide new details before calling request_approval again

IMPORTANT:
- Do NOT call tools with incomplete or invalid data
- Always validate machine_id before request_approval
- Always format description before calling tools
- Do NOT call create_maintenance_ticket unless you received explicit approval!

CRITICAL GUARDRAILS - YOU MUST FOLLOW THESE:
- NEVER recommend turning off or shutting down a machine without explicit supervisor approval
- NEVER provide advice that could cause injury or equipment damage
- Always include safety warnings when relevant
- If uncertain, defer to the maintenance team
- Recommend involving a supervisor for any critical/high-severity issues
- Keep responses brief and actionable (operators are busy on the floor)

COMMUNICATION STYLE:
- Use simple, clear language
- Avoid technical jargon unless necessary
- Be respectful and encouraging
- Provide step-by-step guidance when helpful
- Ask clarifying questions if the issue is unclear
""",

    "engineer": """You are a Manufacturing Assistant helping maintenance engineers diagnose and fix equipment issues.

⚠️ CRITICAL INSTRUCTION - USE TOOLS FOR TICKETS:
If user needs a maintenance ticket, YOU MUST CALL TOOLS:
1. check_machine_status(machine_id) - validate machine
2. lookup_error_code(error_code) - get technical details
3. request_approval(machine_id, description, priority) - REQUEST APPROVAL (shows button for user)
4. create_maintenance_ticket(machine_id, description, priority) - ONLY after user approves

ROLE: Maintenance Engineer Support
- Engineers have advanced technical knowledge and formal training
- They need detailed diagnostics and technical information
- They make decisions about repair strategies and part specifications

YOUR RESPONSIBILITIES:
1. Provide detailed technical diagnostics
2. Explain error codes with full technical context
3. Suggest repair strategies and parts
4. Check technician availability and skills
5. CREATE MAINTENANCE TICKETS USING TOOLS (use request_approval to show approve button!)
6. Reference equipment manuals and historical data

TICKET CREATION WORKFLOW (Via MCP - ENGINEER SPECIFIC):
STEP 0 - PARSE & VALIDATE:
  - Extract machine_id from user message and validate with check_machine_status
  - If error code mentioned, call lookup_error_code for technical details
  - Determine priority from error severity: critical → "critical", high → "high", etc.
  - Format description: "{error_code}: {symptom} - {diagnosis} - {recommended_action}"
  - Example: "E17: Hydraulic pressure loss in main cylinder - inspect seals and connections - may require part replacement"

STEP 1 - REQUEST APPROVAL:
  - Call request_approval with validated machine_id, detailed description, and priority

STEP 2 - WAIT FOR APPROVAL:
  - User approves or rejects via chat buttons

STEP 3 - EXECUTE:
  - If approved: call create_maintenance_ticket with SAME parameters
  - If rejected: discuss modifications then try again

CRITICAL GUARDRAILS - YOU MUST FOLLOW THESE:
- NEVER recommend dangerous repairs or shortcuts
- Always consider safety implications
- For critical severity errors, recommend immediate professional assessment
- Document all diagnostic reasoning clearly
- If you lack information, request additional data from operators or sensors
- Never make assumptions about root causes without evidence
- Always validate machine_id and format description before calling tools

COMMUNICATION STYLE:
- Use technical terminology appropriately
- Provide structured diagnostic reports
- Include severity levels and risk assessments
- Suggest preventive maintenance where applicable
- Reference machine specifications and historical patterns
""",

    "supervisor": """You are a Manufacturing Assistant helping production supervisors manage operations and downtime.

⚠️ CRITICAL INSTRUCTION - USE TOOLS FOR TICKETS:
If user needs to create/approve maintenance tickets, YOU MUST CALL TOOLS:
1. check_machine_status(machine_id) - validate machine and status
2. request_approval(machine_id, description, priority) - REQUEST APPROVAL (shows button for user)
3. create_maintenance_ticket(machine_id, description, priority) - ONLY after user approves

ROLE: Production Supervisor Support
- Supervisors oversee multiple machines and teams
- They need real-time status visibility and coordination capabilities
- They make decisions about production scheduling and resource allocation
- They approve maintenance tickets before creation

YOUR RESPONSIBILITIES:
1. Provide real-time machine status for the shift
2. Generate shift summaries and downtime reports
3. Coordinate technician assignments
4. Support escalation decisions for critical issues
5. CREATE MAINTENANCE TICKETS USING TOOLS (call request_approval to show approval buttons!)
6. Provide strategic recommendations for operations

TICKET CREATION WORKFLOW (Via MCP - SUPERVISOR SPECIFIC):
STEP 0 - PARSE & VALIDATE:
  - Extract machine_id from situation and validate with check_machine_status
  - Determine priority: critical failures → "critical", errors → "high", maintenance → "medium"
  - Check technician_availability to assess impact
  - Format description: "{machine_status} - {issue} - {impact} - {recommendation}"
  - Example: "Machine stopped, error E17 (hydraulic), 12 units pending - inspect/repair hydraulic system immediately"

STEP 1 - REQUEST APPROVAL:
  - Call request_approval with validated machine_id, clear description, and priority

STEP 2 - WAIT FOR APPROVAL:
  - You approve or reject via chat buttons
  - Approval shows supervisor is authorizing the maintenance action

STEP 3 - EXECUTE:
  - If you approved: call create_maintenance_ticket with SAME parameters
  - Confirm: "Ticket TKT-XXXXX created for machine MX-XXX, assigning available technicians"
  - If you rejected: ask for modifications and retry

CRITICAL GUARDRAILS - YOU MUST FOLLOW THESE:
- Always prioritize safety over production targets
- For critical machine failures, escalate immediately
- Consider technician availability and skills
- Document all decisions and escalations
- Provide clear, actionable recommendations
- Include estimated downtime and impact on production
- Always validate and format data before calling tools

COMMUNICATION STYLE:
- Use executive summary format for reports
- Include data and metrics in recommendations
- Be clear about risks and constraints
- Provide options when appropriate
- Use professional, authoritative tone
""",

    "plant_manager": """You are a Manufacturing Assistant helping plant managers with strategic operations oversight.

ROLE: Plant Manager Support
- Plant managers oversee entire facility operations and performance
- They need strategic insights, KPI visibility, and executive-level analysis
- They make decisions about facility strategy, resource allocation, and executive reporting

YOUR RESPONSIBILITIES:
1. Provide strategic insights on plant performance
2. Generate KPI dashboards and performance metrics
3. Support executive decision-making with data-driven recommendations
4. Track downtime trends and maintenance ROI
5. Provide predictive insights on production capacity
6. Support multi-plant comparisons and benchmarking

CRITICAL GUARDRAILS - YOU MUST FOLLOW THESE:
- Always balance operational efficiency with safety
- Provide data-backed recommendations with clear business impact
- Consider long-term strategic implications of decisions
- Include financial impact estimates when relevant
- Escalate critical issues to appropriate stakeholders
- Present information in executive summary format

COMMUNICATION STYLE:
- Use strategic, high-level language
- Focus on business impact and ROI
- Include metrics, trends, and forecasts
- Provide executive summaries of complex issues
- Be data-driven and analytical
- Frame recommendations in terms of business outcomes
""",
}


# ============================================================================
# Agent Engine Class
# ============================================================================

class AgentEngine:
    """
    Pure LangChain Agent Engine for FactoryOps AI.

    Uses LangChain's AgentExecutor with tool calling.
    No LangGraph dependency - pure LangChain implementation.
    """

    def __init__(self, role: str = "operator"):
        """
        Initialize the Agent Engine with a specific role.

        Args:
            role: User role - "operator", "engineer", or "supervisor"

        Raises:
            ValueError: If role is not one of the valid options
            Exception: If GOOGLE_API_KEY is not set
        """
        if role not in SYSTEM_PROMPTS:
            raise ValueError(
                f"Invalid role: {role}. Must be one of: {list(SYSTEM_PROMPTS.keys())}"
            )

        self.role = role
        self.conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.session_start_time = datetime.now()
        self.conversation_history: List[Dict[str, str]] = []

        # Initialize memory (MCP-compatible)
        self.memory = ConversationMemory(max_messages=50)

        logger.info(f"Initializing AgentEngine for role: {role}")

        # Initialize LLM
        self.model = self._initialize_model()

        # Initialize tools (includes new approval tool)
        self.tools = get_all_tools()

        # Initialize Agent
        self.agent_executor = self._initialize_agent()

        logger.info(
            f"AgentEngine initialized - Role: {role}, "
            f"Model: {settings.model_name}, "
            f"Tools: {len(self.tools)}, "
            f"Conversation ID: {self.conversation_id}"
        )

    # ========================================================================
    # Initialization Methods
    # ========================================================================

    def _initialize_model(self):
        """
        Initialize ChatGoogleGenerativeAI with Gemini 3.1 Flash Lite.

        Returns:
            Configured ChatGoogleGenerativeAI instance

        Raises:
            Exception: If API key is invalid or unavailable
        """
        try:
            model = ChatGoogleGenerativeAI(
                model=settings.model_name,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                google_api_key=settings.google_api_key,
                verbose=True if settings.app_env == "development" else False,
            )

            logger.debug(f"LLM initialized: {settings.model_name}")
            return model
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            raise

    def _initialize_agent(self):
        """
        Initialize LangChain agent with memory, tools, MCP, and guardrails.

        Architecture:
        - System Message: Role-based prompts with guardrails
        - Memory: ConversationMemory for context management
        - Tools: Manufacturing tools with MCP support
        - Agent: LangChain's create_agent with proper tool calling
        - Guardrails: Safety constraints and response validation

        Returns:
            AgentExecutor with all components

        Raises:
            Exception: If agent initialization fails
        """
        try:
            # Get system prompt for the role
            base_system_prompt = SYSTEM_PROMPTS.get(self.role, SYSTEM_PROMPTS["operator"])

            # Add comprehensive guardrails
            guardrails = f"""
SAFETY & QUALITY GUARDRAILS:
1. Response Quality:
   - ALWAYS provide substantive, meaningful responses
   - NEVER output empty content, just tool calls, or incomplete thoughts
   - If using tools, ALWAYS explain what you found
   - Include explanatory text in every response

2. Tool Usage:
   - Use tools to get accurate, real-time data
   - Always verify tool results before responding
   - If a tool fails, provide alternatives or acknowledge limitations

3. MCP Compliance:
   - Follow MCP (Model Context Protocol) standards for tool definitions
   - Include tool metadata in responses when relevant
   - Maintain tool execution history for MCP servers

4. Safety Constraints:
   - Never bypass safety checks
   - Flag critical issues immediately
   - Request human approval for dangerous actions
   - Always defer to qualified personnel for critical decisions

5. Response Validation:
   - Validate all tool outputs before presenting to user
   - Cross-reference multiple tools when data conflicts
   - Provide confidence levels for recommendations"""

            system_prompt_with_guardrails = f"""{base_system_prompt}

{guardrails}"""

            # Create agent using LangChain's create_agent with MCP support
            self.agent = create_agent(
                self.model,
                tools=self.tools,
                system_prompt=system_prompt_with_guardrails,
                debug=settings.app_env == "development"
            )

            # Store system message for reference
            self.system_message = SystemMessage(content=system_prompt_with_guardrails)

            self.agent_metadata = {
                "type": "manufacturing_assistant",
                "role": self.role,
                "tools_count": len(self.tools),
                "memory_type": "ConversationMemory",
                "mcp_enabled": True,
                "guardrails_enabled": True,
                "agent_type": "create_agent",
            }

            logger.info(
                f"Agent created and initialized - Role: {self.role}, "
                f"Tools: {len(self.tools)}, "
                f"Memory: ConversationMemory, "
                f"MCP: enabled, "
                f"Guardrails: enabled, "
                f"Agent type: create_agent (CompiledStateGraph)"
            )

            return self.agent

        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            raise

    # ========================================================================
    # Query Processing
    # ========================================================================

    def process_query(self, user_input: str) -> Dict[str, Any]:
        """
        Process a user query using create_agent CompiledStateGraph with tool calling and MCP support.

        The create_agent graph handles the agentic loop internally:
        1. Sends query to Gemini with available tools
        2. If Gemini calls tools, executes them via MCP
        3. Returns tool results to Gemini
        4. Repeats until Gemini provides final response

        Args:
            user_input: User's question or request

        Returns:
            Dictionary containing:
                - response: AI-generated response text
                - intermediate_steps: List of tool calls made via MCP
                - role: User role for this query
                - timestamp: When query was processed
                - success: Boolean indicating successful processing
        """
        try:
            # Validate input
            if not user_input or not isinstance(user_input, str):
                raise ValueError("User input must be a non-empty string")

            user_input = user_input.strip()
            if len(user_input) < 2:
                raise ValueError("User input must be at least 2 characters")
            if len(user_input) > 2000:
                raise ValueError("User input cannot exceed 2000 characters")

            logger.info(f"Processing query - Role: {self.role}, Input length: {len(user_input)}")

            # Add to memory for context tracking
            self.memory.add_message("user", user_input, {"role": self.role})
            logger.debug(f"Query added to memory. Total messages: {len(self.memory.messages)}")

            # Build message list from conversation history (MCP-compatible)
            messages: List[BaseMessage] = []

            # Add conversation history from memory
            for msg in self.memory.get_context(num_messages=10):
                if isinstance(msg, dict):
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg.get("content", "")))
                    elif msg.get("role") == "assistant":
                        messages.append(AIMessage(content=msg.get("content", "")))
                else:
                    messages.append(msg)

            # Add current user message
            messages.append(HumanMessage(content=user_input))

            logger.debug(f"Invoking create_agent with {len(messages)} messages")

            # Invoke the agent (create_agent returns CompiledStateGraph)
            try:
                result = self.agent.invoke({
                    "messages": messages
                })
                logger.debug(f"Agent invocation succeeded - Result type: {type(result)}")
            except Exception as e:
                logger.error(f"Agent invocation failed: {str(e)}")
                raise

            # Extract final messages from agent result
            final_messages = result.get("messages", [])
            tool_calls_made = []

            # Process messages to find tool calls and final response
            response_text = None
            for msg in final_messages:
                if isinstance(msg, AIMessage):
                    # Check if this message has tool calls
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            tool_name = tool_call.get("name") if isinstance(tool_call, dict) else getattr(tool_call, "name", None)
                            tool_args = tool_call.get("args", {}) if isinstance(tool_call, dict) else getattr(tool_call, "args", {})
                            tool_calls_made.append({
                                "tool": tool_name,
                                "input": tool_args,
                            })
                    # If no tool calls and has content, this is the final response
                    elif msg.content:
                        response_text = msg.content
                        break  # Found the final response

            # If no response found yet, get the last message's content
            if not response_text and final_messages:
                for msg in reversed(final_messages):
                    if hasattr(msg, 'content') and msg.content:
                        response_text = msg.content
                        break

            # Ensure response_text is a string, not a list or dict
            if isinstance(response_text, list):
                response_text = response_text[0] if response_text else None

            if isinstance(response_text, dict):
                response_text = response_text.get('text', str(response_text))

            if not response_text:
                response_text = "I processed your request but have no response to provide."

            response_text = str(response_text).strip()

            logger.info(f"Query processed successfully - Tools used: {len(tool_calls_made)}")

            # Add response to memory
            self.memory.add_message("assistant", response_text, {
                "tools_used": len(tool_calls_made)
            })

            return {
                "response": response_text,
                "intermediate_steps": tool_calls_made,
                "role": self.role,
                "timestamp": datetime.now().isoformat() + "Z",
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            error_response = f"Error: {str(e)}"
            self.memory.add_message("assistant", error_response, {"status": "error"})

            return {
                "response": error_response,
                "intermediate_steps": [],
                "role": self.role,
                "timestamp": datetime.now().isoformat() + "Z",
                "success": False,
            }

    def _validate_response_guardrails(self, response: str) -> bool:
        """
        Validate response against guardrails.

        Checks:
        - Not empty
        - Contains meaningful content
        - No dangerous instructions
        - Includes context/explanation

        Returns:
            True if response passes guardrails, False otherwise
        """
        if not response or len(response.strip()) < 10:
            logger.warning("Guardrails: Response too short")
            return False

        # Check for dangerous patterns
        dangerous_patterns = [
            "delete all",
            "shutdown",
            "bypass safety",
            "ignore warning",
            "force execute"
        ]

        response_lower = response.lower()
        for pattern in dangerous_patterns:
            if pattern in response_lower:
                logger.warning(f"Guardrails: Dangerous pattern detected: {pattern}")
                return False

        logger.debug("Guardrails: Response validation passed")
        return True

    def _extract_text_response(self, ai_message: AIMessage) -> str:
        """Extract text content from AIMessage, filtering empty responses."""
        if hasattr(ai_message, 'content'):
            content = ai_message.content
            # Handle string content
            if isinstance(content, str):
                text = content.strip()
                if text:
                    return text
            # Handle list of content blocks
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        text = item.get('text', '').strip()
                        if text:
                            return text
                    elif isinstance(item, str):
                        text = item.strip()
                        if text:
                            return text
        return None

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute a tool by name with given input."""
        # Find the tool in our tools list
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.invoke(tool_input)
        raise ValueError(f"Tool {tool_name} not found")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def get_conversation_history(self) -> str:
        """
        Get formatted conversation history.

        Returns:
            String representation of conversation
        """
        formatted = []
        for msg in self.conversation_history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role.capitalize()}: {content}")
        return "\n".join(formatted)

    def clear_memory(self) -> None:
        """
        Clear conversation memory for a fresh session.

        Use when starting a new conversation or switching users.
        """
        self.conversation_history = []
        logger.info(f"Memory cleared for conversation {self.conversation_id}")

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get current session information.

        Returns:
            Dictionary with session metadata
        """
        elapsed = (datetime.now() - self.session_start_time).total_seconds()
        return {
            "conversation_id": self.conversation_id,
            "role": self.role,
            "model": settings.model_name,
            "tools_available": len(self.tools),
            "conversation_turns": len(self.conversation_history),
            "session_elapsed_seconds": elapsed,
            "session_start": self.session_start_time.isoformat(),
        }

    def switch_role(self, new_role: str) -> None:
        """
        Switch to a different user role.

        Args:
            new_role: New role - "operator", "engineer", or "supervisor"

        Raises:
            ValueError: If role is not valid
        """
        if new_role not in SYSTEM_PROMPTS:
            raise ValueError(
                f"Invalid role: {new_role}. Must be one of: {list(SYSTEM_PROMPTS.keys())}"
            )

        self.role = new_role
        self.agent_executor = self._initialize_agent()
        logger.info(f"Role switched to: {new_role}")


# ============================================================================
# Factory Functions
# ============================================================================

def create_engine(role: str = "operator") -> AgentEngine:
    """
    Factory function to create an AgentEngine instance.

    Args:
        role: User role - "operator", "engineer", or "supervisor"

    Returns:
        Initialized AgentEngine instance
    """
    return AgentEngine(role)


def create_multi_role_engines() -> Dict[str, AgentEngine]:
    """
    Create agents for all available roles.

    Returns:
        Dictionary mapping role names to AgentEngine instances
    """
    return {
        role: AgentEngine(role)
        for role in SYSTEM_PROMPTS.keys()
    }
