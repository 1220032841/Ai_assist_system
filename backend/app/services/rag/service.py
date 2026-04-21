import hashlib
import math
import re
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.db.models import Document
from app.core.config import settings
from openai import AsyncOpenAI
from pgvector.sqlalchemy import Vector

# Mock embedding for now if no API key, or use real one
# In production, we should handle this more gracefully.
# For this implementation, we assume OPENAI_API_KEY is set in env or config.

class RAGService:
    def __init__(self):
        self.provider = (settings.LLM_PROVIDER or "openai").lower()
        self.api_key = settings.LLM_API_KEY or settings.OPENAI_API_KEY
        self.base_url = settings.LLM_BASE_URL
        self.chat_model = settings.LLM_CHAT_MODEL
        self.fallback_chat_model = settings.LLM_FALLBACK_CHAT_MODEL
        self.embedding_model = settings.LLM_EMBEDDING_MODEL
        self.embedding_provider = (settings.EMBEDDING_PROVIDER or "auto").lower()
        self.embedding_api_key = settings.EMBEDDING_API_KEY or settings.OPENAI_API_KEY
        self.embedding_base_url = settings.EMBEDDING_BASE_URL
        self.retrieve_top_k = max(1, settings.RAG_RETRIEVE_TOP_K)

        if self.provider == "deepseek":
            if not self.base_url:
                self.base_url = "https://api.deepseek.com"
            if not self.chat_model:
                self.chat_model = "deepseek-chat"
            # DeepSeek plans may not include embedding APIs.
            # If no separate embedding credentials are set, we fallback to lexical retrieval.
            if (
                self.embedding_provider in ("auto", "remote")
                and self.embedding_model
                and not self.embedding_api_key
            ):
                self.embedding_model = None
        else:
            if not self.chat_model:
                self.chat_model = "gpt-4o-mini"

        if self.embedding_provider == "local" and not self.embedding_model:
            self.embedding_model = "BAAI/bge-small-en-v1.5"

        self.client = None
        self.embedding_client = None
        self.local_embedder = None
        if self.api_key:
            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            self.client = AsyncOpenAI(**client_kwargs)

        use_remote_embeddings = self.embedding_provider in ("auto", "remote")
        use_local_embeddings = self.embedding_provider == "local"

        if use_remote_embeddings and self.embedding_api_key and self.embedding_model:
            embed_kwargs = {"api_key": self.embedding_api_key}
            if self.embedding_base_url:
                embed_kwargs["base_url"] = self.embedding_base_url
            self.embedding_client = AsyncOpenAI(**embed_kwargs)

        if use_local_embeddings and self.embedding_model:
            try:
                from fastembed import TextEmbedding
                self.local_embedder = TextEmbedding(model_name=self.embedding_model)
            except Exception as e:
                print(f"Local embedding init failed: {e}")
                self.local_embedder = None

    def _hash_embedding(self, text: str, dim: int = 1536) -> List[float]:
        # Offline fallback: stable hashed bag-of-words embedding.
        tokens = re.findall(r"[A-Za-z0-9_]+", (text or "").lower())
        if not tokens:
            return [0.0] * dim

        vec = [0.0] * dim
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % dim
            sign = 1.0 if (digest[4] % 2 == 0) else -1.0
            vec[idx] += sign

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text.
        """
        if self.local_embedder is not None:
            try:
                vec = list(self.local_embedder.embed([text]))[0].tolist()
                # Keep DB vector dimension compatible with Vector(1536)
                if len(vec) < 1536:
                    vec = vec + [0.0] * (1536 - len(vec))
                elif len(vec) > 1536:
                    vec = vec[:1536]
                return vec
            except Exception as e:
                print(f"Error getting local embedding: {e}")
                return self._hash_embedding(text)

        if self.embedding_provider == "local":
            return self._hash_embedding(text)

        if not self.embedding_client or not self.embedding_model:
            # Fallback for testing or if key is missing
            return [0.0] * 1536
            
        try:
            response = await self.embedding_client.embeddings.create(
                input=text, 
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            # Fallback to avoid crashing on transient errors
            return [0.0] * 1536

    async def ingest_document(self, db: AsyncSession, title: str, content: str, metadata: dict = None):
        """
        Ingest a document into the vector store.
        """
        # 1. Chunking (Simple split by paragraphs or fixed size)
        chunks = self._chunk_text(content)
        
        for i, chunk in enumerate(chunks):
            embedding = await self.get_embedding(chunk)
            doc = Document(
                title=f"{title} - Part {i+1}",
                content=chunk,
                metadata_=metadata,
                embedding=embedding
            )
            db.add(doc)
        
        await db.commit()

    async def retrieve(self, db: AsyncSession, query: str, limit: int = 3) -> List[Document]:
        """
        Retrieve relevant documents using cosine distance.
        """
        actual_limit = max(1, limit or self.retrieve_top_k)

        if (self.embedding_client and self.embedding_model) or self.embedding_provider == "local":
            query_embedding = await self.get_embedding(query)
            candidate_limit = actual_limit if self.embedding_provider != "local" else actual_limit * 8
            # pgvector cosine distance: <=> operator
            stmt = (
                select(Document)
                .order_by(Document.embedding.cosine_distance(query_embedding))
                .limit(candidate_limit)
            )
            result = await db.execute(stmt)
            docs = result.scalars().all()

            if self.embedding_provider != "local":
                return docs[:actual_limit]

            terms = [t.strip().lower() for t in query.split() if t.strip()][:8]

            def lexical_score(doc: Document) -> int:
                if not terms:
                    return 0
                text = f"{doc.title or ''} {doc.content or ''}".lower()
                return sum(1 for term in terms if term in text)

            scored = [(lexical_score(doc), rank, doc) for rank, doc in enumerate(docs)]
            scored.sort(key=lambda item: (-item[0], item[1]))

            merged: List[Document] = []
            for score, _, doc in scored:
                if score <= 0:
                    continue
                merged.append(doc)
                if len(merged) >= actual_limit:
                    return merged

            for _, _, doc in scored:
                if doc in merged:
                    continue
                merged.append(doc)
                if len(merged) >= actual_limit:
                    break

            return merged

        # Lexical fallback retrieval when embedding service is unavailable.
        terms = [t.strip() for t in query.split() if t.strip()][:8]
        if not terms:
            stmt = select(Document).limit(actual_limit)
            result = await db.execute(stmt)
            return result.scalars().all()

        conditions = []
        for term in terms:
            conditions.append(Document.title.ilike(f"%{term}%"))
            conditions.append(Document.content.ilike(f"%{term}%"))

        stmt = select(Document).where(or_(*conditions)).limit(actual_limit)
        result = await db.execute(stmt)
        docs = result.scalars().all()

        if docs:
            return docs

        # Final fallback: return latest chunks when lexical match misses.
        stmt = select(Document).order_by(Document.id.desc()).limit(actual_limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """
        Simple text chunker.
        """
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

rag_service = RAGService()
