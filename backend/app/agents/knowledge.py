import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastapi import UploadFile

class KnowledgeAgent:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        # Persistent directory for vector store
        self.persist_directory = "./chroma_db"
        self.vector_store = Chroma(
            collection_name="sentio_knowledge",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )

    async def ingest_document(self, file: UploadFile, metadata: dict):
        """
        Ingests a document into the vector store.
        """
        content = await file.read()
        # Simple text decoding for now. For PDF/Docx, we'd need specialized loaders.
        text_content = content.decode("utf-8", errors="ignore")
        
        docs = [Document(page_content=text_content, metadata=metadata)]
        chunks = self.text_splitter.split_documents(docs)
        
        if chunks:
            self.vector_store.add_documents(chunks)
            return {"status": "success", "chunks_added": len(chunks)}
        return {"status": "no_content"}

    async def retrieve_context(self, query: str, project_id: str, k: int = 5):
        """
        Retrieves context relevant to the query, filtered by project_id.
        """
        # Filter by project_id if provided
        filter_dict = {"projectId": project_id} if project_id else None
        
        results = self.vector_store.similarity_search(
            query,
            k=k,
            filter=filter_dict
        )
        
        context_text = "\n\n".join([doc.page_content for doc in results])
        sources = list(set([doc.metadata.get("source", "unknown") for doc in results]))
        
        return {
            "context": context_text,
            "sources": sources
        }
