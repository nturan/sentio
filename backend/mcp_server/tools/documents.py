"""
MCP Tools for Document operations.
"""

import json
import uuid
from datetime import datetime

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


async def document_create(
    project_id: str,
    filename: str,
    content: str,
    content_type: str = "text/markdown"
) -> str:
    """Create a document from text content and ingest into knowledge base."""
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    doc_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    content_bytes = len(content.encode('utf-8'))

    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify project exists
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Project not found", "project_id": project_id})

        # Save document metadata to database
        cursor.execute("""
            INSERT INTO documents (id, project_id, filename, file_size, content_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (doc_id, project_id, filename, content_bytes, content_type, now))

    # Ingest into vector store
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = Chroma(
            collection_name="sentio_knowledge",
            embedding_function=embeddings,
            persist_directory="./chroma_db"
        )
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )

        metadata = {
            "projectId": project_id,
            "source": filename,
            "documentId": doc_id
        }

        docs = [Document(page_content=content, metadata=metadata)]
        chunks = text_splitter.split_documents(docs)

        if chunks:
            vector_store.add_documents(chunks)

        return json.dumps({
            "success": True,
            "document_id": doc_id,
            "filename": filename,
            "chunks_indexed": len(chunks),
            "message": f"Document '{filename}' created and indexed successfully"
        })

    except Exception as e:
        return json.dumps({
            "success": True,
            "document_id": doc_id,
            "filename": filename,
            "warning": f"Document saved but indexing failed: {str(e)}"
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
    },
    "document_create": {
        "description": "Create a new document from text content and ingest it into the knowledge base. Use this to save research results, reports, or other text content as project documents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID to create the document for"
                },
                "filename": {
                    "type": "string",
                    "description": "Filename for the document (e.g., 'Research_ChangeManagement.md')"
                },
                "content": {
                    "type": "string",
                    "description": "The document content (markdown supported)"
                },
                "content_type": {
                    "type": "string",
                    "description": "MIME type (default: text/markdown)"
                }
            },
            "required": ["project_id", "filename", "content"]
        },
        "handler": document_create
    }
}
