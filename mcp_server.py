"""
Unified MCP server exposing search_records, create_record, update_record.
All tools accept action_plan (MCP style).

- Run standalone: python mcp_server.py (stdio, for external MCP clients).
- In-process: use inprocess_mcp_streams() so the agent talks to this server
  over in-memory streams (avoids Windows subprocess "Connection closed" issues).
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

import anyio

from mcp.server.fastmcp import FastMCP

from tools.search import search_records_impl
from tools.create import create_record_impl
from tools.update import update_record_impl

mcp = FastMCP(
    name="CM Tools",
    instructions="Content Manager: search, create, update records (action_plan interface)",
)


@mcp.tool()
async def search_records(action_plan: dict) -> dict:
    """
    Search records in Content Manager.
    Args:
        action_plan: Action plan with path, method GET, parameters (query params).
    """
    return await search_records_impl(action_plan)


@mcp.tool()
async def create_record(action_plan: dict) -> dict:
    """
    Create a record in Content Manager.
    Args:
        action_plan: Action plan with method POST, parameters (RecordRecordType, RecordTitle, etc.).
    """
    return await create_record_impl(action_plan)


@mcp.tool()
async def update_record(action_plan: dict) -> dict:
    """
    Update record(s) in Content Manager.
    Args:
        action_plan: Action plan with parameters_to_search and/or parameters_to_update.
    """
    return await update_record_impl(action_plan)


@asynccontextmanager
async def inprocess_mcp_streams() -> AsyncIterator[tuple]:
    """
    Yield (read_stream, write_stream) for an MCP client in the same process.
    Use with ClientSession(read_stream, write_stream) so the agent can call
    tools without spawning a subprocess (avoids Windows stdio "Connection closed").
    """
    # Client writes -> a_send; server reads <- a_receive
    # Server writes -> b_send; client reads <- b_receive
    a_send, a_receive = anyio.create_memory_object_stream(0)
    b_send, b_receive = anyio.create_memory_object_stream(0)

    init_options = mcp._mcp_server.create_initialization_options()

    async def run_server() -> None:
        try:
            await mcp._mcp_server.run(a_receive, b_send, init_options)
        except anyio.ClosedResourceError:
            pass
        finally:
            await b_send.aclose()

    async with anyio.create_task_group() as tg:
        tg.start_soon(run_server)
        try:
            yield b_receive, a_send
        finally:
            await a_send.aclose()


if __name__ == "__main__":
    mcp.run()
