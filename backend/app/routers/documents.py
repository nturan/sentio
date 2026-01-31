from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from ..database import get_connection, dict_from_row
from ..agents.knowledge import KnowledgeAgent

router = APIRouter(prefix="/api", tags=["documents"])

# Share the knowledge agent instance
knowledge_agent = KnowledgeAgent()


class Document(BaseModel):
    id: str
    project_id: str
    filename: str
    file_size: Optional[int]
    content_type: Optional[str]
    created_at: str


@router.get("/projects/{project_id}/documents", response_model=List[Document])
async def list_documents(project_id: str):
    """List all documents for a project."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, project_id, filename, file_size, content_type, created_at
            FROM documents
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,)
        )
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@router.post("/projects/{project_id}/documents", response_model=Document)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...)
):
    """Upload a document and ingest it into the knowledge base."""
    doc_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Reset file position for knowledge agent
    await file.seek(0)

    # Ingest into vector store
    metadata = {"projectId": project_id, "source": file.filename, "documentId": doc_id}
    result = await knowledge_agent.ingest_document(file, metadata)

    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail="Failed to process document")

    # Save to database
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO documents (id, project_id, filename, file_size, content_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (doc_id, project_id, file.filename, file_size, file.content_type, now)
        )

    return {
        "id": doc_id,
        "project_id": project_id,
        "filename": file.filename,
        "file_size": file_size,
        "content_type": file.content_type,
        "created_at": now
    }


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if document exists
        cursor.execute(
            "SELECT id FROM documents WHERE id = ?",
            (document_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from database (vector store entries remain but won't cause issues)
        cursor.execute(
            "DELETE FROM documents WHERE id = ?",
            (document_id,)
        )

        return {"message": "Document deleted"}
