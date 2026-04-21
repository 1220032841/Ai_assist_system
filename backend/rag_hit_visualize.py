import argparse
import asyncio

from app.db.session import AsyncSessionLocal
from app.services.rag.service import rag_service


async def run_queries(queries: list[str], limit: int) -> None:
    print("RAG Retrieval Visualization")
    print("=" * 60)
    print(
        f"provider={rag_service.provider}, "
        f"chat_model={rag_service.chat_model}, "
        f"embedding_model={rag_service.embedding_model}, "
        f"top_k={limit}"
    )
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        for query in queries:
            docs = await rag_service.retrieve(db, query, limit=limit)
            print(f"\nQuery: {query}")
            if not docs:
                print("  -> No hits")
                continue

            for i, doc in enumerate(docs, start=1):
                snippet = (doc.content or "").replace("\n", " ")[:180]
                print(f"  [{i}] {doc.title}")
                print(f"      snippet: {snippet}...")


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize top RAG retrieval hits")
    parser.add_argument(
        "--query",
        action="append",
        required=True,
        help="Query text. Repeat --query for multiple checks.",
    )
    parser.add_argument("--limit", type=int, default=3, help="Top-K documents to display")
    args = parser.parse_args()

    limit = max(1, args.limit)
    asyncio.run(run_queries(args.query, limit))


if __name__ == "__main__":
    main()
