"""
Document Ingestion and Embedding Script for RAG Pipeline.

This script reads policy statements from text files, treats each line as a
separate piece of information, generates embeddings, and stores them in ChromaDB.

Usage:
    python embed_engine.py
"""

import argparse
from pathlib import Path
import traceback

from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.schema import TextNode

from sentence_transformers import SentenceTransformer
import numpy as np
import chromadb

# Custom Embedder compatible with LlamaIndex v0.10+
class LocalMiniLMEmbedder:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")

    def get_text_embedding(self, text: str) -> list[float]:
        return self.model.encode(text, convert_to_numpy=True).tolist()

    def get_text_embedding_batch(self, texts: list[str], **kwargs) -> list[list[float]]:
        return self.model.encode(texts, convert_to_numpy=True).tolist()

Settings.embed_model = LocalMiniLMEmbedder()


def main():
    parser = argparse.ArgumentParser(description="Ingest and embed documents into a ChromaDB vector store.")
    parser.add_argument("--data-folder", type=Path, default=Path("./data"), help="Path to the folder containing policy documents.")
    parser.add_argument("--db-path", type=Path, default=Path("./vector_db"), help="Path to the directory where the vector database will be stored.")
    parser.add_argument("--collection-name", type=str, default="policy_control_embeddings", help="Name of the collection within ChromaDB.")
    args = parser.parse_args()

    try:
        print(f"Checking for data folder at: {args.data_folder.resolve()}")
        if not args.data_folder.exists() or not args.data_folder.is_dir():
            raise FileNotFoundError(f"Data folder not found at the specified path: {args.data_folder.resolve()}")

        print("Loading embedding model: sentence-transformers/all-MiniLM-L12-v2")

        print(f"Loading policy statements from text files in '{args.data_folder}'...")
        policy_files = list(args.data_folder.glob("*.txt"))
        if not policy_files:
            raise ValueError(f"No .txt files found in '{args.data_folder}'. Please provide a text file with one policy statement per line.")

        all_statements = []
        for file_path in policy_files:
            with open(file_path, "r", encoding="utf-8") as f:
                statements = [line.strip() for line in f if line.strip()]
                all_statements.extend(statements)

        if not all_statements:
            raise ValueError("The policy files are empty or contain no valid statements.")

        nodes = [TextNode(text=stmt) for stmt in all_statements]
        print(f"Created {len(nodes)} individual text nodes from policy statements.")

        print(f"Setting up ChromaDB at '{args.db_path}'...")
        args.db_path.mkdir(parents=True, exist_ok=True)
        chroma_client = chromadb.PersistentClient(path=str(args.db_path))

        print(f"Resetting collection: '{args.collection_name}'...")
        existing_collections = [c.name for c in chroma_client.list_collections()]
        if args.collection_name in existing_collections:
            print(f"Old collection '{args.collection_name}' found. Deleting it.")
            chroma_client.delete_collection(name=args.collection_name)
        else:
            print(f"No old collection named '{args.collection_name}' found. Creating a new one.")

        chroma_collection = chroma_client.create_collection(name=args.collection_name)
        print(f"New empty collection '{args.collection_name}' created.")

        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        print(f"Generating and storing embeddings for {len(nodes)} nodes...")
        index = VectorStoreIndex(nodes, storage_context=storage_context)

        print("Success.")
        print(f"Stored {chroma_collection.count()} embeddings in the '{args.collection_name}' collection.")
        print(f"Database is located at: {args.db_path.resolve()}")

    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
    except Exception as e:
        print("An unexpected error occurred.")
        traceback.print_exc()


if __name__ == "__main__":
    main()
