"""
Compare the schema between the local SQLite database and Supabase PostgreSQL database.
This script helps verify that both databases have compatible structures.
"""
import os
import asyncio
import logging
import json
import sqlite3
from typing import Dict, List, Any, Set, Tuple
import getpass
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Make sure we load environment variables
load_dotenv()

def get_sqlite_schema() -> Dict[str, List[Dict[str, str]]]:
    """
    Extract schema information from the local SQLite database.
    
    Returns:
        dict: Table structures with column information
    """
    # Initialize result dictionary
    schema = {}
    
    # Get database path from environment or use default
    # Get database file path
    db_dir = os.path.expanduser("~/AppData/Roaming/TimeTracker/db")
    db_path = os.path.join(db_dir, "timetracker.db")
    
    if not os.path.exists(db_path):
        logger.error(f"SQLite database not found at {db_path}")
        return schema
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Format column information
            schema[table_name] = []
            for col in columns:
                col_id, col_name, col_type, col_notnull, col_default, col_pk = col
                schema[table_name].append({
                    "column_name": col_name,
                    "data_type": col_type,
                    "is_nullable": "NO" if col_notnull else "YES",
                    "column_default": col_default,
                    "is_primary_key": col_pk == 1
                })
        
        # Close the connection
        conn.close()
        
        return schema
        
    except Exception as e:
        logger.error(f"Error reading SQLite schema: {str(e)}")
        return schema

async def get_supabase_schema():
    """
    Use the Supabase MCP server to get the schema of the remote database.
    
    Returns:
        dict: Table structures with column information
    """
    # Import the MCP use_mcp_tool function
    from services.supabase_auth import SupabaseAuthService
    
    auth_service = SupabaseAuthService()
    
    # Check if authenticated
    if not auth_service.is_authenticated():
        logger.info("Not authenticated, starting login process...")
        session_path = os.path.expanduser("~/TimeTracker/data/session.json")
        if os.path.exists(session_path):
            logger.info("Found saved session, attempting to load...")
            if auth_service.load_session(session_path):
                logger.info("Session loaded successfully")
                if auth_service.is_authenticated():
                    logger.info("Session is valid")
                else:
                    logger.info("Session is expired or invalid")
                    return {}
        else:
            logger.error("No session found and authentication required")
            return {}
    
    try:
        # We'll use a direct SQL query via the Supabase MCP server to get the schema
        import sys
        from use_mcp_tool import use_mcp_tool

        # First, get all schema names
        schemas_result = await use_mcp_tool(
            server_name="github.com/alexander-zuev/supabase-mcp-server",
            tool_name="get_schemas",
            arguments={}
        )
        
        schema = {}
        
        # For each schema, get tables info
        for schema_info in schemas_result:
            schema_name = schema_info.get("name")
            
            # Skip system schemas
            if schema_name in ['pg_toast', 'pg_temp_1', 'pg_toast_temp_1', 'pg_catalog', 'information_schema']:
                continue
                
            # Get tables in this schema
            tables_result = await use_mcp_tool(
                server_name="github.com/alexander-zuev/supabase-mcp-server",
                tool_name="get_tables",
                arguments={"schema_name": schema_name}
            )
            
            for table_info in tables_result:
                table_name = table_info.get("table_name")
                full_table_name = f"{schema_name}.{table_name}"
                
                # Get table schema
                table_schema = await use_mcp_tool(
                    server_name="github.com/alexander-zuev/supabase-mcp-server",
                    tool_name="get_table_schema",
                    arguments={"schema_name": schema_name, "table": table_name}
                )
                
                # Extract column information
                columns = table_schema.get("columns", [])
                
                # Format column information
                schema[full_table_name] = []
                for col in columns:
                    schema[full_table_name].append({
                        "column_name": col.get("column_name"),
                        "data_type": col.get("data_type"),
                        "is_nullable": col.get("is_nullable"),
                        "column_default": col.get("column_default"),
                        "is_primary_key": col.get("is_primary_key", False)
                    })
        
        return schema
        
    except Exception as e:
        logger.error(f"Error reading Supabase schema: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {}

def map_sqlite_to_pg_type(sqlite_type: str) -> str:
    """
    Map SQLite data types to PostgreSQL data types for comparison.
    
    Args:
        sqlite_type: SQLite data type
        
    Returns:
        str: Equivalent PostgreSQL data type
    """
    sqlite_type = sqlite_type.lower()
    
    # Common SQLite to PostgreSQL type mappings
    type_mapping = {
        'integer': 'integer',
        'int': 'integer',
        'real': 'double precision',
        'float': 'double precision',
        'text': 'text',
        'blob': 'bytea',
        'boolean': 'boolean',
        'date': 'date',
        'timestamp': 'timestamp without time zone',
        'datetime': 'timestamp without time zone',
        'varchar': 'character varying',
        'char': 'character',
    }
    
    # Check for types with parameters (e.g., varchar(255))
    for base_type, pg_type in type_mapping.items():
        if sqlite_type.startswith(base_type):
            # If it has parameters, try to preserve them
            if '(' in sqlite_type:
                param_part = sqlite_type[sqlite_type.find('('):]
                return f"{pg_type}{param_part}"
            return pg_type
    
    # Default to the original type if no mapping is found
    return sqlite_type

def compare_schemas(local_schema: Dict[str, List[Dict[str, str]]], 
                   remote_schema: Dict[str, List[Dict[str, str]]]) -> Dict[str, Any]:
    """
    Compare local SQLite schema with remote PostgreSQL schema.
    
    Args:
        local_schema: Local SQLite schema
        remote_schema: Remote PostgreSQL schema
        
    Returns:
        dict: Comparison results with differences
    """
    result = {
        "matching_tables": [],
        "only_in_local": [],
        "only_in_remote": [],
        "column_differences": {}
    }
    
    # First, clean up schema names to match between SQLite and PostgreSQL
    # Postgres typically uses schema.table_name format
    pg_table_mapping = {}
    for full_name in remote_schema:
        # Split schema.table_name
        parts = full_name.split('.')
        if len(parts) == 2:
            schema_name, table_name = parts
            # Map schema-qualified table names to their simple names for comparison
            # Focus primarily on the "public" schema
            if schema_name == 'public':
                pg_table_mapping[table_name] = full_name
        else:
            # If there's no schema, just use the table name
            pg_table_mapping[full_name] = full_name
    
    # Compare table names
    local_tables = set(local_schema.keys())
    remote_tables_simple = set(pg_table_mapping.keys())
    
    # Find matching tables, tables only in local, and tables only in remote
    for table in local_tables:
        if table in remote_tables_simple:
            # Check columns for this table
            local_columns = local_schema[table]
            remote_columns = remote_schema[pg_table_mapping[table]]
            
            # Compare columns
            column_diffs = compare_columns(local_columns, remote_columns)
            
            if column_diffs:
                result["column_differences"][table] = column_diffs
                # If there are column differences, it's not an exact match
            else:
                result["matching_tables"].append(table)
        else:
            result["only_in_local"].append(table)
    
    # Find tables only in remote
    for remote_table in remote_tables_simple:
        if remote_table not in local_tables:
            result["only_in_remote"].append(pg_table_mapping[remote_table])
    
    return result

def compare_columns(local_columns: List[Dict[str, str]], 
                    remote_columns: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Compare columns between local and remote tables.
    
    Args:
        local_columns: Columns in local table
        remote_columns: Columns in remote table
        
    Returns:
        dict: Column differences
    """
    result = {
        "only_in_local": [],
        "only_in_remote": [],
        "type_differences": [],
        "constraint_differences": []
    }
    
    # Create dictionaries of columns by name for easier comparison
    local_cols_dict = {col["column_name"]: col for col in local_columns}
    remote_cols_dict = {col["column_name"]: col for col in remote_columns}
    
    # Find columns only in local and type differences
    for col_name, local_col in local_cols_dict.items():
        if col_name in remote_cols_dict:
            remote_col = remote_cols_dict[col_name]
            
            # Map SQLite type to PostgreSQL for comparison
            local_type = map_sqlite_to_pg_type(local_col["data_type"])
            remote_type = remote_col["data_type"]
            
            # Compare types after normalization
            if not types_are_compatible(local_type, remote_type):
                result["type_differences"].append({
                    "column": col_name,
                    "local_type": local_col["data_type"],
                    "remote_type": remote_col["data_type"]
                })
            
            # Compare constraints
            if local_col["is_nullable"] != remote_col["is_nullable"]:
                result["constraint_differences"].append({
                    "column": col_name,
                    "difference": "nullability",
                    "local": local_col["is_nullable"],
                    "remote": remote_col["is_nullable"]
                })
            
            if local_col["is_primary_key"] != remote_col["is_primary_key"]:
                result["constraint_differences"].append({
                    "column": col_name,
                    "difference": "primary_key",
                    "local": local_col["is_primary_key"],
                    "remote": remote_col["is_primary_key"]
                })
        else:
            result["only_in_local"].append(col_name)
    
    # Find columns only in remote
    for col_name in remote_cols_dict:
        if col_name not in local_cols_dict:
            result["only_in_remote"].append(col_name)
    
    # Remove empty categories
    for key in list(result.keys()):
        if not result[key]:
            del result[key]
    
    return result

def types_are_compatible(local_type: str, remote_type: str) -> bool:
    """
    Check if two data types are compatible for synchronization.
    
    Args:
        local_type: Local data type
        remote_type: Remote data type
        
    Returns:
        bool: True if compatible, False otherwise
    """
    # Normalize types for comparison
    local_type = local_type.lower().strip()
    remote_type = remote_type.lower().strip()
    
    # Direct matches
    if local_type == remote_type:
        return True
    
    # Remove any parameters for comparison
    local_base = local_type.split('(')[0].strip()
    remote_base = remote_type.split('(')[0].strip()
    
    if local_base == remote_base:
        return True
    
    # Common compatibility pairs
    compatible_pairs = [
        # Integers
        {'integer', 'int', 'int4', 'smallint', 'bigint', 'int2', 'int8', 'serial'},
        # Floating point
        {'real', 'float', 'double', 'double precision', 'numeric', 'decimal'},
        # Text
        {'text', 'varchar', 'character varying', 'char', 'character', 'string'},
        # Boolean
        {'boolean', 'bool'},
        # Binary
        {'blob', 'bytea', 'binary'},
        # Dates and times
        {'date', 'timestamp', 'datetime', 'timestamp without time zone', 'timestamp with time zone', 'timestamptz'},
    ]
    
    # Check if both types belong to the same compatibility group
    for group in compatible_pairs:
        if local_base in group and remote_base in group:
            return True
    
    return False

def print_schema_comparison(comparison: Dict[str, Any]):
    """
    Print the schema comparison results in a human-readable format.
    
    Args:
        comparison: Comparison results
    """
    print("\n===== DATABASE SCHEMA COMPARISON =====\n")
    
    # Print matching tables
    print(f"✅ MATCHING TABLES: {len(comparison['matching_tables'])}")
    for table in sorted(comparison['matching_tables']):
        print(f"  - {table}")
    
    # Print tables only in local
    if comparison['only_in_local']:
        print(f"\n❌ TABLES ONLY IN LOCAL: {len(comparison['only_in_local'])}")
        for table in sorted(comparison['only_in_local']):
            print(f"  - {table}")
    
    # Print tables only in remote
    if comparison['only_in_remote']:
        print(f"\n⚠️ TABLES ONLY IN REMOTE: {len(comparison['only_in_remote'])}")
        for table in sorted(comparison['only_in_remote']):
            print(f"  - {table}")
    
    # Print column differences
    if comparison.get('column_differences'):
        print(f"\n🔄 TABLES WITH COLUMN DIFFERENCES: {len(comparison['column_differences'])}")
        for table, diffs in comparison['column_differences'].items():
            print(f"\n  TABLE: {table}")
            
            if diffs.get('only_in_local'):
                print(f"    ➖ Columns only in local: {', '.join(diffs['only_in_local'])}")
            
            if diffs.get('only_in_remote'):
                print(f"    ➕ Columns only in remote: {', '.join(diffs['only_in_remote'])}")
            
            if diffs.get('type_differences'):
                print("    🔢 Type differences:")
                for diff in diffs['type_differences']:
                    print(f"      - {diff['column']}: Local({diff['local_type']}) vs Remote({diff['remote_type']})")
            
            if diffs.get('constraint_differences'):
                print("    🔒 Constraint differences:")
                for diff in diffs['constraint_differences']:
                    print(f"      - {diff['column']}: {diff['difference']} - Local({diff['local']}) vs Remote({diff['remote']})")
    
    print("\n======================================\n")

def save_comparison_to_file(comparison: Dict[str, Any], filepath: str) -> None:
    """
    Save the schema comparison results to a Markdown file.
    
    Args:
        comparison: Comparison results
        filepath: Path to save the results
    """
    with open(filepath, 'w') as f:
        f.write("# Database Schema Comparison\n\n")
        
        # Write matching tables
        f.write(f"## ✅ Matching Tables ({len(comparison['matching_tables'])})\n\n")
        if comparison['matching_tables']:
            for table in sorted(comparison['matching_tables']):
                f.write(f"- {table}\n")
        else:
            f.write("No matching tables found.\n")
        
        # Write tables only in local
        f.write(f"\n## ❌ Tables Only in Local Database ({len(comparison['only_in_local'])})\n\n")
        if comparison['only_in_local']:
            for table in sorted(comparison['only_in_local']):
                f.write(f"- {table}\n")
        else:
            f.write("No tables found only in local database.\n")
        
        # Write tables only in remote
        f.write(f"\n## ⚠️ Tables Only in Remote Database ({len(comparison['only_in_remote'])})\n\n")
        if comparison['only_in_remote']:
            for table in sorted(comparison['only_in_remote']):
                f.write(f"- {table}\n")
        else:
            f.write("No tables found only in remote database.\n")
        
        # Write column differences
        if comparison.get('column_differences'):
            f.write(f"\n## 🔄 Tables with Column Differences ({len(comparison['column_differences'])})\n\n")
            for table, diffs in comparison['column_differences'].items():
                f.write(f"### Table: {table}\n\n")
                
                if diffs.get('only_in_local'):
                    f.write("#### Columns Only in Local\n\n")
                    for col in diffs['only_in_local']:
                        f.write(f"- {col}\n")
                
                if diffs.get('only_in_remote'):
                    f.write("\n#### Columns Only in Remote\n\n")
                    for col in diffs['only_in_remote']:
                        f.write(f"- {col}\n")
                
                if diffs.get('type_differences'):
                    f.write("\n#### Type Differences\n\n")
                    f.write("| Column | Local Type | Remote Type |\n")
                    f.write("|--------|------------|-------------|\n")
                    for diff in diffs['type_differences']:
                        f.write(f"| {diff['column']} | {diff['local_type']} | {diff['remote_type']} |\n")
                
                if diffs.get('constraint_differences'):
                    f.write("\n#### Constraint Differences\n\n")
                    f.write("| Column | Difference | Local | Remote |\n")
                    f.write("|--------|------------|-------|--------|\n")
                    for diff in diffs['constraint_differences']:
                        f.write(f"| {diff['column']} | {diff['difference']} | {diff['local']} | {diff['remote']} |\n")
                
                f.write("\n")
        else:
            f.write("\n## 🔄 Tables with Column Differences\n\nNo column differences found.\n")
        
        f.write("\n\n*Report generated on " + 
                import_time().strftime("%Y-%m-%d %H:%M:%S") + 
                "*\n")

def import_time():
    """
    Import datetime and return current time.
    This avoids importing datetime at module level.
    """
    from datetime import datetime
    return datetime.now()

async def main():
    """Main entry point."""
    try:
        print("===== Database Schema Comparison Tool =====")
        print("Comparing local SQLite schema with remote Supabase PostgreSQL schema...")
        
        # Get local schema
        print("\nExtracting local SQLite schema...")
        local_schema = get_sqlite_schema()
        print(f"Found {len(local_schema)} tables in local database")
        
        # Get remote schema
        print("\nExtracting remote Supabase schema...")
        remote_schema = await get_supabase_schema()
        print(f"Found {len(remote_schema)} tables in remote database")
        
        # Compare schemas
        if not local_schema or not remote_schema:
            print("Cannot compare schemas - one or both schemas are empty")
            return
        
        print("\nComparing schemas...")
        comparison = compare_schemas(local_schema, remote_schema)
        
        # Print results
        print_schema_comparison(comparison)
        
        # Save results to file
        output_path = "schema_comparison.md"
        save_comparison_to_file(comparison, output_path)
        print(f"Comparison results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())
