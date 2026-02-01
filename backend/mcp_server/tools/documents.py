"""
MCP Tools for Document operations.
"""

import json

from app.database import get_connection, dict_from_row


async def document_list(project_id: str) -> str:
    """List all documents for a project."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, project_id, filename, file_size, content_type, created_at
            FROM documents
            WHERE project_id = ?
            ORDER BY created_at DESC
        """, (project_id,))

        documents = [dict_from_row(row) for row in cursor.fetchall()]
        return json.dumps(documents)


async def document_delete(document_id: str) -> str:
    """Delete a document record."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, filename FROM documents WHERE id = ?", (document_id,))
        row = cursor.fetchone()
        if not row:
            return json.dumps({"error": "Document not found", "document_id": document_id})

        doc = dict_from_row(row)
        cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))

        return json.dumps({
            "success": True,
            "message": "Document deleted",
            "document_id": document_id,
            "filename": doc["filename"]
        })


async def document_retrieve_context(project_id: str) -> str:
    """Get document context for a project."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get project info
        cursor.execute("SELECT id, name, goal FROM projects WHERE id = ?", (project_id,))
        project_row = cursor.fetchone()
        if not project_row:
            return json.dumps({"error": "Project not found", "project_id": project_id})

        project = dict_from_row(project_row)

        # Get documents
        cursor.execute("""
            SELECT id, filename, file_size, content_type, created_at
            FROM documents
            WHERE project_id = ?
            ORDER BY created_at DESC
        """, (project_id,))

        documents = [dict_from_row(row) for row in cursor.fetchall()]

        # Calculate statistics
        total_size = sum(d.get("file_size") or 0 for d in documents)
        content_types = {}
        for d in documents:
            ct = d.get("content_type") or "unknown"
            content_types[ct] = content_types.get(ct, 0) + 1

        return json.dumps({
            "project_id": project_id,
            "project_name": project["name"],
            "project_goal": project["goal"],
            "document_count": len(documents),
            "total_size_bytes": total_size,
            "content_types": content_types,
            "documents": documents
        })


# Tool definitions for the MCP server
TOOLS = {
    "document_list": {
        "description": "List all documents for a project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID to get documents for"
                }
            },
            "required": ["project_id"]
        },
        "handler": document_list
    },
    "document_delete": {
        "description": "Delete a document record. Note: This only deletes the database record. The actual file and vector store entries are managed by the KnowledgeAgent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "The unique identifier of the document"
                }
            },
            "required": ["document_id"]
        },
        "handler": document_delete
    },
    "document_retrieve_context": {
        "description": "Get document context for a project including metadata about all documents and summary statistics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID"
                }
            },
            "required": ["project_id"]
        },
        "handler": document_retrieve_context
    }
}
