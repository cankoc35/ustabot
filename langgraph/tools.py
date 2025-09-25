import sys
import asyncio
from pathlib import Path

# Ensure project root is importable when running directly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from scraper.maps.extract import extract_from_google_maps

def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    return asyncio.run(coro)

@tool
def extract_from_google_maps_tool(city_name: str, count: int | None = 5):
    """Extract details about businesses in the specified city from Google Maps."""
    """If count is not specified, defaults to 5."""
    default_count = 5 if count is None else count
    return _run_async(extract_from_google_maps(city_name=city_name, count=default_count))

@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    """This tool is used when the AI needs help from a human to answer a query."""
    human_response = interrupt({"query": query})
    return human_response["data"]


tools = [
    extract_from_google_maps_tool,
    human_assistance
    # ... other tools can be added here
]

tool_node = ToolNode(tools)
