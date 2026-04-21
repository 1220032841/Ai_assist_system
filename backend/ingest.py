import asyncio
import os
import argparse
from app.db.session import AsyncSessionLocal
from app.services.rag.service import rag_service
from sqlalchemy import delete
from app.db.models import Document

async def ingest_directory(directory: str):
    """
    Ingest all text files from a directory into the RAG system.
    """
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' not found.")
        return

    async with AsyncSessionLocal() as session:
        for filename in os.listdir(directory):
            if filename.endswith(".txt") or filename.endswith(".md"):
                file_path = os.path.join(directory, filename)
                print(f"Ingesting {filename}...")
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Avoid duplicate chunks when re-ingesting the same source file.
                    await session.execute(
                        delete(Document).where(Document.title.like(f"{filename} - Part %"))
                    )
                    await session.commit()
                        
                    await rag_service.ingest_document(
                        session, 
                        title=filename, 
                        content=content,
                        metadata={"source": "file_ingestion", "filename": filename}
                    )
                    print(f"Successfully ingested {filename}")
                except Exception as e:
                    print(f"Failed to ingest {filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into RAG system")
    parser.add_argument("--dir", type=str, required=True, help="Directory containing text/markdown files")
    
    args = parser.parse_args()
    
    asyncio.run(ingest_directory(args.dir))
