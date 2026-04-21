import asyncio

from sqlalchemy import select

from app.db.models import Document
from app.db.session import AsyncSessionLocal
from app.services.rag.service import rag_service


async def main() -> None:
    print("Reindex embeddings started")
    print(
        f"embedding_provider={rag_service.embedding_provider}, "
        f"embedding_model={rag_service.embedding_model}"
    )

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).order_by(Document.id.asc()))
        docs = result.scalars().all()
        print(f"documents={len(docs)}")

        for idx, doc in enumerate(docs, start=1):
            emb = await rag_service.get_embedding(doc.content or "")
            doc.embedding = emb
            if idx % 20 == 0:
                await db.commit()
                print(f"processed={idx}")

        await db.commit()
        print("Reindex embeddings done")


if __name__ == "__main__":
    asyncio.run(main())
