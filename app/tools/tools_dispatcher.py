"""
Tool Dispatcher for LLM Function Calling
Centralized dispatcher for all appointment and external tools
"""

from typing import Any, Dict
from app.config.logging import app_logger
from app.tools.appointments import (
    get_available_slots,
    book_appointment,
    get_booking,
    reschedule_appointment,
    cancel_appointment,
)
from app.tools.external_tools import get_weather

logger = app_logger


# ═══════════════════════════════════════════════════════════════════
# TOOL DISPATCHER - LLM calls this automatically
# ═══════════════════════════════════════════════════════════════════

async def execute_tool(
    tool_name: str,
    tool_args: Dict[str, Any],
    session_id: str = None
) -> str:
    """
    Main dispatcher for LiveKit agent tool execution
    
    Handles all appointment and external tools with proper validation,
    error handling, and argument normalization.
    
    Args:
        tool_name: Name of the tool to execute (must match TOOLS_SCHEMA)
        tool_args: Dictionary of arguments to pass to the tool
        session_id: Optional LiveKit session ID for booking context
        
    Returns:
        str: Result from tool execution or error message
    """

    try:
        # ✅ STEP 1: Normalize and clean input arguments
        # ═══════════════════════════════════════════════════════════════
        
        # Normalize email if present (for appointment tools)
        if "email" in tool_args and tool_args["email"]:
            tool_args["email"] = tool_args["email"].strip().lower()

        # Remove booking_uid if LLM tries to send it
        # We will fetch booking_uid internally using email + session
        tool_args.pop("booking_uid", None)

        # Inject session_id automatically for appointment tools
        if session_id:
            tool_args["session_id"] = session_id

        # ✅ STEP 2: Create tool mapping
        # ═══════════════════════════════════════════════════════════════
        
        TOOL_MAP = {
            # Appointment tools
            "get_available_slots": get_available_slots,
            "book_appointment": book_appointment,
            "get_booking": get_booking,
            "reschedule_appointment": reschedule_appointment,
            "cancel_appointment": cancel_appointment,
            
            # External tools
            "get_weather": get_weather,
        }

        # ✅ STEP 3: Validate tool exists
        # ═══════════════════════════════════════════════════════════════
        
        tool_func = TOOL_MAP.get(tool_name)

        if not tool_func:
            logger.warning(f"❌ Unknown tool requested: {tool_name}")
            logger.warning(f"Available tools: {list(TOOL_MAP.keys())}")
            return "Sorry, I cannot perform that action. This tool is not available."

        # ✅ STEP 4: Log execution details
        # ═══════════════════════════════════════════════════════════════
        
        logger.info(f"🔧 Executing tool: {tool_name}")
        logger.debug(f"Tool arguments: {tool_args}")
        
        if session_id:
            logger.debug(f"LiveKit session: {session_id}")

        # ✅ STEP 5: Execute the tool
        # ═══════════════════════════════════════════════════════════════
        
        result = await tool_func(**tool_args)

        logger.info(f"✅ Tool '{tool_name}' executed successfully")
        
        return result

    except TypeError as e:
        # Invalid arguments passed to tool
        logger.error(f"❌ Invalid arguments for tool '{tool_name}': {str(e)}", exc_info=True)
        return f"Invalid arguments for this action. Please check your input and try again."
        
    except ValueError as e:
        # Validation errors (e.g., invalid date format, email)
        logger.error(f"❌ Validation error in tool '{tool_name}': {str(e)}", exc_info=True)
        return f"Invalid input: {str(e)}"
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"❌ Tool execution error in '{tool_name}': {str(e)}", exc_info=True)
        return "Something went wrong while processing your request. Please try again later."
