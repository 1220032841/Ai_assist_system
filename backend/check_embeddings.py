import asyncio

from sqlalchemy import select

from app.db.models import Document
from app.db.session import AsyncSessionLocal


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).order_by(Document.id.asc()).limit(10))
        docs = result.scalars().all()
        for doc in docs:
            emb = [] if doc.embedding is None else list(doc.embedding)
            nz = sum(1 for x in emb if abs(float(x)) > 1e-12)
            abs_sum = sum(abs(float(x)) for x in emb)
            print(f"id={doc.id} non_zero={nz} abs_sum={abs_sum:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
