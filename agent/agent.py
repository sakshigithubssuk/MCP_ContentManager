from llm.intent_router import IntentRouter
from tools.ActionPlanGenerator import ActionPlanGenerator

from mcp import ClientSession

from mcp_server import inprocess_mcp_streams


def _parse_call_tool_result(result) -> str:
    """Extract response from MCP CallToolResult (content list, is_error)."""
    if getattr(result, "is_error", False):
        return f"Tool error: {result}"
    content = getattr(result, "content", None) or []
    parts = []
    for item in content:
        if hasattr(item, "text"):
            parts.append(item.text)
        elif isinstance(item, dict) and "text" in item:
            parts.append(item["text"])
    if parts:
        return "\n".join(parts)
    return str(result)


class Agent:

    def __init__(self):
        self.intent_router = IntentRouter()

    async def handle_query(self, user_query: str):
        print("inside agent before intent detection")

        intent = self.intent_router.detect_intent(user_query)
        print("Detected intent:", intent)

        # -----------------------
        # ACTION PLAN GENERATION
        # -----------------------

        action_plan = ActionPlanGenerator().run(user_query, intent)

        print("\nAction Plan Generated:")
        print(action_plan)

        # -----------------------
        # EXECUTION (MCP) — no direct tool calling; all via MCP server
        # -----------------------

        response = await self._execute_via_mcp(action_plan)

        print("\nFinal Response:")
        print(response)

        return response

    # -------------------------------------------------
    # MCP EXECUTOR — spawn MCP server via stdio, call tool by name
    # -------------------------------------------------

    async def _execute_via_mcp(self, action_plan: dict):
        method = action_plan.get("method")
        operation = action_plan.get("operation", "").upper()

        # Map action plan → MCP tool name (no direct Python calls)
        if method == "GET" or operation == "SEARCH":
            tool_name = "search_records"
        elif method == "POST" and (operation == "CREATE" or str(operation).lower() == "create"):
            tool_name = "create_record"
        elif method == "POST" and (operation == "UPDATE" or str(operation).lower() == "update"):
            tool_name = "update_record"
        else:
            return "Unsupported operation"

        print(f"\nCalling MCP tool → {tool_name} (MCP style, no direct tool call)")

        try:
            # In-process MCP: same process, in-memory streams (avoids Windows subprocess "Connection closed")
            async with inprocess_mcp_streams() as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(
                        tool_name,
                        arguments={"action_plan": action_plan},
                    )
                    return _parse_call_tool_result(result)
        except Exception as e:
            print(f"\n[MCP] Error calling tool: {e}")
            raise
