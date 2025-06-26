"""
Gap Detection Engine for CMMC Controls using RAG + LLM Reasoning

Inputs:
- controls/sample_controls.json : List of controls
- vector_db/ : ChromaDB vector store of embedded policies

Output:
- outputs/gap_report.json : Gap analysis results

Usage:
    python rag_engine.py
"""

import json
import traceback
from pathlib import Path

from llama_index.core import Settings, VectorStoreIndex, StorageContext, QueryBundle
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama

import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np

# ----------------------------
# LLM: Deterministic Inference (Gemma 2B via Ollama)
# ----------------------------
Settings.llm = Ollama(
    model="gemma:2b",
    temperature=0.1,
    request_timeout=60.0
)

# ----------------------------
# Embedding: Local MiniLM Model w/ All Required Methods
# ----------------------------
class LocalMiniLMEmbedder:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")

    def get_text_embedding(self, text: str) -> list[float]:
        return self.model.encode(text, convert_to_numpy=True).tolist()

    def get_text_embedding_batch(self, texts: list[str], **kwargs) -> list[list[float]]:
        return self.model.encode(texts, convert_to_numpy=True).tolist()

    def get_agg_embedding_from_queries(self, queries, **kwargs) -> list[float]:
        embeddings = self.model.encode(queries, convert_to_numpy=True)
        return np.mean(embeddings, axis=0).tolist()

Settings.embed_model = LocalMiniLMEmbedder()

# ----------------------------
# Paths
# ----------------------------
CONTROL_FILE = Path("controls/sample_controls.json")
VECTOR_DB_PATH = Path("vector_db")
OUTPUT_FILE = Path("outputs/gap_report.json")
COLLECTION_NAME = "policy_control_embeddings"

# ----------------------------
# Confidence Heuristic
# ----------------------------
def score_confidence(response: str) -> float:
    response = response.lower()
    if "fully met" in response:
        return 0.9
    elif "partially met" in response:
        return 0.6
    elif "not met" in response:
        return 0.3
    return 0.5

# ----------------------------
# Output Parser
# ----------------------------
def parse_output(control_id, llm_response, matched_text):
    llm_response = llm_response.strip().lower()
    if "fully met" in llm_response:
        status = "Fully Met"
    elif "partially met" in llm_response:
        status = "Partially Met"
    else:
        status = "Not Met"

    confidence_score = score_confidence(llm_response)
    explanation = (
        llm_response.replace("fully met", "")
        .replace("partially met", "")
        .replace("not met", "")
        .strip()
    )
    if not explanation:
        explanation = "LLM did not provide detailed reasoning."

    return {
        "control_id": control_id,
        "status": status,
        "matched_text": matched_text,
        "confidence_score": round(confidence_score, 2),
        "explanation": explanation
    }

# ----------------------------
# Main Gap Analysis Logic
# ----------------------------
def main():
    try:
        if not CONTROL_FILE.exists():
            raise FileNotFoundError(f"Control file not found: {CONTROL_FILE}")
        if not VECTOR_DB_PATH.exists():
            raise FileNotFoundError(f"Vector database not found: {VECTOR_DB_PATH}")

        with open(CONTROL_FILE, "r", encoding="utf-8") as f:
            controls = json.load(f)

        print(f"\nLoaded {len(controls)} controls from {CONTROL_FILE}")

        chroma_client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_vector_store(vector_store)

        results = []

        for control in controls:
            control_id = control.get("control_id")
            description = control.get("description")

            print(f"\nEvaluating Control: {control_id}")

            query = QueryBundle(description)
            retriever = index.as_retriever(similarity_top_k=3)
            nodes = retriever.retrieve(query)

            matched_text = "\n---\n".join([n.text for n in nodes])
            prompt = (
                f"You are a compliance auditor evaluating a CMMC policy document. "
                f"Based on the following policy excerpts:\n\n{matched_text}\n\n"
                f"Does the organization fully meet, partially meet, or not meet the following requirement?\n\n"
                f"Requirement: {description}\n\n"
                f"Respond with 'Fully Met', 'Partially Met', or 'Not Met' and provide a one-line explanation."
            )

            llm_response = Settings.llm.complete(prompt).text
            result = parse_output(control_id, llm_response, matched_text)
            results.append(result)

        # Save to JSON
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        # Print Terminal Summary
        print("\n=== GAP ANALYSIS SUMMARY ===")
        for r in results:
            line = f"{r['control_id']} → {r['status']} ({r['confidence_score']})"
            if r['explanation']:
                line += f" - {r['explanation']}"
            print("✔ " + line)

        print(f"\nGap analysis complete. Results saved to: {OUTPUT_FILE}")

    except Exception as e:
        print("ERROR during gap analysis:")
        traceback.print_exc()

if __name__ == "__main__":
    main()

