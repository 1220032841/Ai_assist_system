import asyncio

from app.db.session import AsyncSessionLocal
from app.services.rag.service import rag_service


async def main() -> None:
    queries = [
        "dynamic programming",
        "linked list reverse",
        "time complexity",
    ]

    print(
        f"provider={rag_service.provider} "
        f"embedding_provider={rag_service.embedding_provider} "
        f"embedding_model={rag_service.embedding_model}"
    )

    async with AsyncSessionLocal() as db:
        for query in queries:
            query_vec = await rag_service.get_embedding(query)
            query_nz = sum(1 for x in query_vec if abs(float(x)) > 1e-12)
            print(f"query_non_zero_dims={query_nz}")
            docs = await rag_service.retrieve(db, query, limit=3)
            print(f"\nquery={query}")
            for idx, doc in enumerate(docs, start=1):
                snippet = (doc.content or "").replace("\n", " ")[:120]
                print(f"  {idx}. {doc.title} :: {snippet}")


if __name__ == "__main__":
    asyncio.run(main())
