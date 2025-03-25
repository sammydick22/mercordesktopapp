"""
Helper module to use MCP tools from Python scripts.
This provides a clean interface to the MCP tools for other scripts.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

async def use_mcp_tool(server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Use an MCP tool with the provided arguments.
    
    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool to use
        arguments: Arguments to pass to the tool
        
    Returns:
        Any: Result of the tool execution
    """
    try:
        # Import Claude's MCP tool function - this needs to be imported dynamically
        # as it's not available in the standard Python environment
        from claude_dev.mcp.use_mcp_tool import use_mcp_tool as dev_mcp_tool
        
        # Convert arguments to JSON string and back to ensure proper formatting
        args_json = json.dumps(arguments)
        args_dict = json.loads(args_json)
        
        # Call the tool
        result = await dev_mcp_tool(server_name, tool_name, args_dict)
        
        return result
    except ImportError:
        # If we're not in the Claude environment, provide a mock for testing
        logger.warning("Claude MCP environment not available - using mock implementation")
        return await mock_mcp_tool(server_name, tool_name, arguments)
    except Exception as e:
        logger.error(f"Error using MCP tool: {str(e)}")
        raise

async def mock_mcp_tool(server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Mock implementation of MCP tool for testing outside Claude environment.
    
    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool to use
        arguments: Arguments to pass to the tool
        
    Returns:
        Any: Mock result
    """
    logger.info(f"Mock MCP tool call: {server_name}.{tool_name}({arguments})")
    
    # Supabase specific mocks
    if server_name == "github.com/alexander-zuev/supabase-mcp-server":
        if tool_name == "get_schemas":
            return [
                {"name": "public", "table_count": 10, "size_bytes": 1024000},
                {"name": "auth", "table_count": 5, "size_bytes": 512000}
            ]
        elif tool_name == "get_tables":
            return [
                {"table_name": "users", "type": "table", "row_count": 100},
                {"table_name": "projects", "type": "table", "row_count": 50},
                {"table_name": "clients", "type": "table", "row_count": 20}
            ]
        elif tool_name == "get_table_schema":
            return {
                "columns": [
                    {"column_name": "id", "data_type": "uuid", "is_nullable": "NO", "column_default": "uuid_generate_v4()", "is_primary_key": True},
                    {"column_name": "name", "data_type": "text", "is_nullable": "NO", "column_default": None, "is_primary_key": False},
                    {"column_name": "created_at", "data_type": "timestamp with time zone", "is_nullable": "NO", "column_default": "now()", "is_primary_key": False}
                ]
            }
        elif tool_name == "execute_postgresql":
            return {"data": [], "metadata": {"command": "SELECT", "rows_affected": 0}}
    
    # Default mock response for unknown tools
    return {"mock": True, "server": server_name, "tool": tool_name, "args": arguments}
