# rag_engine.py (Final Corrected Version for Compatibility)

import json
import argparse
from datetime import datetime
from pathlib import Path
import re
import traceback

# LlamaIndex Imports
from llama_index.core import VectorStoreIndex, Settings, PromptTemplate
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.query_engine import RetrieverQueryEngine

# ChromaDB Import
from chromadb import PersistentClient

def validate_paths(controls_path: Path, vector_db_path: Path):
    """Ensure that necessary files and directories exist."""
    if not controls_path.is_file():
        raise FileNotFoundError(f"ERROR: Controls file not found: {controls_path}")
    if not vector_db_path.is_dir():
        raise FileNotFoundError(f"ERROR: Vector database directory not found: {vector_db_path}")

def setup_models(llm_model_name: str):
    """Configure the embedding model and the language model."""
    print("Setting up models...")
    Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    try:
        Settings.llm = Ollama(model=llm_model_name, request_timeout=120.0)
        Settings.llm.complete("Hi")
        print(f"SUCCESS: Ollama model '{llm_model_name}' configured successfully.")
    except Exception as e:
        raise ConnectionError(f"ERROR: Failed to connect to Ollama. Is the server running? Error: {e}")

def setup_vector_store(vector_db_path: Path, collection_name: str) -> VectorStoreIndex:
    """Connect to the ChromaDB vector store and load the index."""
    print("Connecting to vector database...")
    chroma_client = PersistentClient(path=str(vector_db_path))
    try:
        chroma_collection = chroma_client.get_collection(name=collection_name)
    except ValueError:
        raise ValueError(f"ERROR: Collection '{collection_name}' not found. Please run the embed_engine.py script first.")
    
    embedding_count = chroma_collection.count()
    if embedding_count == 0:
        raise ValueError("ERROR: Vector database collection is empty. Please run the embed_engine.py script first.")
    
    print(f"SUCCESS: Connected to '{collection_name}' with {embedding_count} embeddings.")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    return index

def load_controls(controls_path: Path) -> list:
    """Load control descriptions from a JSON file."""
    print("Loading controls...")
    try:
        with open(controls_path, "r", encoding="utf-8") as f:
            controls = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"ERROR: Invalid JSON format in controls file: {e}")
    if not isinstance(controls, list) or not controls:
        raise ValueError("ERROR: Controls file must be a non-empty list of control objects.")
    print(f"SUCCESS: Loaded {len(controls)} control(s).")
    return controls

def determine_status(score: float, llm_answer: str) -> str:
    """Determine control status based on a combination of retrieval score and LLM answer."""
    answer_lower = llm_answer.lower()
    
    fully_met_keywords = ["fully implemented", "fully met", "is in place", "compliant", "satisfied", "is addressed"]
    partially_met_keywords = ["partially", "some aspects", "incomplete", "part of", "lacks", "needs improvement"]
    not_met_keywords = ["no evidence", "not found", "does not mention", "not addressed", "not implemented"]

    if any(phrase in answer_lower for phrase in not_met_keywords):
        return "Not Met"
    if any(phrase in answer_lower for phrase in fully_met_keywords):
        return "Fully Met"
    if any(phrase in answer_lower for phrase in partially_met_keywords):
        return "Partially Met"
    
    if score > 0.35:
        return "Partially Met"

    return "Not Met"

def process_control(control: dict, i: int, query_engine: RetrieverQueryEngine) -> dict:
    """Query the RAG engine for a single control and format the result."""
    control_id = control.get("control_id", f"UNKNOWN_{i}")
    query = control.get("description", "")

    if not query:
        return { "control_id": control_id, "status": "Not Met", "confidence_score": 0.0, "matched_text": "N/A", "llm_explanation": "No description provided for this control."}

    try:
        response = query_engine.query(query)
        llm_explanation = str(response.response).strip()
        llm_explanation = re.sub(r'\s+', ' ', llm_explanation)

        if response.source_nodes:
            top_score = response.source_nodes[0].score or 0.0
            all_context = "\n---\n".join([node.node.get_content(metadata_mode="llm") for node in response.source_nodes])
            context_summary = all_context[:1500] + "..." if len(all_context) > 1500 else all_context
        else:
            top_score = 0.0
            context_summary = "N/A"
            llm_explanation = "No relevant documents were found in the vector store."

        status = determine_status(top_score, llm_explanation)
        
        result = { "control_id": control_id, "status": status, "confidence_score": round(top_score, 4), "matched_text": context_summary, "llm_explanation": llm_explanation }
        print(f"SUCCESS: {control_id} -> {status} (Score: {top_score:.3f})")
        return result
    except Exception as e:
        print(f"ERROR for control {control_id}: An unexpected error occurred.")
        traceback.print_exc()
        return { "control_id": control_id, "status": "Not Met", "confidence_score": 0.0, "matched_text": "N/A", "llm_explanation": f"An error occurred during processing: {e}"}

def save_report(results: list, output_path: Path):
    """Save the final analysis to a JSON file and return the summary."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = { "fully_met": sum(1 for r in results if r["status"] == "Fully Met"), "partially_met": sum(1 for r in results if r["status"] == "Partially Met"), "not_met": sum(1 for r in results if r["status"] == "Not Met")}
    report_data = { "metadata": { "report_title": "Compliance Gap Analysis Report", "total_controls_analyzed": len(results), "generated_at": datetime.now().isoformat(), "summary": summary }, "results": results}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    return summary

def print_summary(summary: dict, total_controls: int, output_path: Path):
    """Print a formatted summary of the analysis to the console."""
    print(f"\nSUCCESS: Gap report saved to: {output_path.resolve()}")
    if total_controls == 0: return
    print(f"INFO: Analyzed {total_controls} control(s).")
    print("\n--- Analysis Summary ---")
    print(f"  Fully Met:     {summary['fully_met']:>3} ({summary['fully_met']/total_controls*100:5.1f}%)")
    print(f"  Partially Met: {summary['partially_met']:>3} ({summary['partially_met']/total_controls*100:5.1f}%)")
    print(f"  Not Met:       {summary['not_met']:>3} ({summary['not_met']/total_controls*100:5.1f}%)")
    print("------------------------")

def main():
    """Main function to run the gap analysis pipeline."""
    parser = argparse.ArgumentParser(description="Run a compliance gap analysis using a RAG pipeline.")
    parser.add_argument("--controls", type=Path, default=Path("controls/sample_controls.json"), help="Path to the controls JSON file.")
    parser.add_argument("--db-path", type=Path, default=Path("./vector_db"), help="Path to the ChromaDB vector database directory.")
    parser.add_argument("--output", type=Path, default=Path("outputs/gap_report.json"), help="Path to save the output report.")
    parser.add_argument("--collection", type=str, default="policy_control_embeddings", help="Name of the ChromaDB collection.")
    parser.add_argument("--llm", type=str, default="gemma:2b", help="Name of the Ollama model to use.")
    parser.add_argument("--top-k", type=int, default=3, help="Number of similar documents to retrieve.")
    args = parser.parse_args()

    qa_prompt_template = ( "You are a compliance audit assistant. Your task is to determine if the provided context " "satisfies the given control requirement.\n" "---------------------\n" "CONTEXT: {context_str}\n" "---------------------\n" "CONTROL REQUIREMENT: {query_str}\n" "---------------------\n" "Based *only* on the provided context, analyze the control requirement. " "If the context explicitly shows the control is fully implemented, state that. " "If the context partially addresses the control, explain what is met and what is missing. " "If the context does not contain relevant information, state that no evidence was found. " "Be concise and do not add information not present in the context.\n" "ANSWER: ")
    qa_prompt = PromptTemplate(qa_prompt_template)

    try:
        validate_paths(args.controls, args.db_path)
        setup_models(args.llm)
        index = setup_vector_store(args.db_path, args.collection)
        controls = load_controls(args.controls)

        print("\nInitializing RAG engine...")

        # --- THIS IS THE FINAL, ROBUST, CORRECTED LOGIC ---
        # Use the high-level index.as_query_engine() factory method.
        # This correctly constructs the engine with our custom prompt
        # in a way that is compatible with multiple LlamaIndex versions.
        query_engine = index.as_query_engine(
            similarity_top_k=args.top_k,
            text_qa_template=qa_prompt,
        )
        # --- END OF CORRECTED LOGIC ---
        
        print(f"Analyzing {len(controls)} controls (using top_k={args.top_k})...\n")
        results = [process_control(control, i, query_engine) for i, control in enumerate(controls, 1)]
        
        summary = save_report(results, args.output)
        print_summary(summary, len(controls), args.output)

    except (FileNotFoundError, ConnectionError, ValueError, IOError) as e:
        print(f"\nCRITICAL ERROR: {e}")
        if isinstance(e, ConnectionError):
            print("INFO: Please ensure the Ollama server is running. You can start it with: ollama serve")
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: An unexpected error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()