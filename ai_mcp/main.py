# main.py

import sys
import json
from pathlib import Path
from dotenv import load_dotenv



ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")

from ingestion.loader import load_documents

from ingestion.chunker import chunk_documents
from config.settings import RAW_DOCS_PATH, PROCESSED_DOCS_PATH

import json
from config.settings import PROCESSED_DOCS_PATH
from embeddings.embedder import LocalEmbedder


def run_chatbot():
    print("MCP Hospital Chatbot - type 'exit' to quit\n")

    from config.settings import PROCESSED_DOCS_PATH
    from vector_store.store import LocalVectorStore
    from embeddings.embedder import LocalEmbedder
    from rag.retriever import Retriever
    from rag.context_builder import ContextBuilder
    from llm.gemini_llm import GeminiLLM
    from mcp.controller import MCPController
    from mcp.executor import MCPExecutor
    # ---------------- MCP ----------------
    mcp = MCPController()
    mcp_executor = MCPExecutor()

    # ---------------- RAG STACK (MD FILES ONLY) ----------------
    store = LocalVectorStore(
        embeddings_path=PROCESSED_DOCS_PATH / "embeddings.json",
        chunks_path=PROCESSED_DOCS_PATH / "chunks.json"
    )

    embedder = LocalEmbedder()
    embedder.load(PROCESSED_DOCS_PATH / "tfidf_vectorizer.pkl")

    retriever = Retriever(store, embedder)
    context_builder = ContextBuilder(max_chars=2000)

    # ---------------- LLM ----------------
    llm = GeminiLLM()

    # ================= CHAT LOOP =================
    while True:
        query = input("\nYou: ").strip()

        if not query:
            continue

        if query.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        action = mcp.decide(query)

        if action == "RUN_RAG":
            chunks = retriever.retrieve(query, top_k=5)

            if not chunks:
                print("\nBot:\nI do not have that information.")
                continue

            context = context_builder.build_context(chunks)
            answer = llm.generate(context, query)

            print("\nBot:\n")
            print(answer)

        elif action == "RUN_MCP":
            result = mcp_executor.execute(
                intent=mcp.intent_classifier.classify(query),
                query=query
            )
            if isinstance(result, dict) and "human_response" in result:
                print(f"\nBot:\n{result['human_response']}\n")
            else:
                print("\nBot:\n")
                print(json.dumps(result, indent=2))

        else:
            print("\nBot:\nI cannot handle that request yet.")


if __name__ == "__main__":
    run_chatbot()
