# Gap Analysis Agent: Built with RAG, LLMs and Real-World Compliance Controls

> **Subtitle**: Trained on CMMC controls. Adaptable to ISO, NIST, and GRC frameworks.

---

## Overview

**Gap Analysis Agent** is a lightweight, local AI tool for evaluating cybersecurity policy compliance using:
- Retrieval-Augmented Generation (RAG)
- MiniLM embeddings
- ChromaDB vector search
- Local LLM reasoning

Designed for **CMMC 2.0 Level 1 & Level 2**, this agent compares your policy documents against official control sets — identifying where you're Fully Met, Partially Met, or Not Met with clear justifications.

---

## Project Structure

```
gap-analysis-agent-cmmc/
├── controls/ → CMMC controls (JSON format)
├── data/ → Your sample policy file
├── embeddings/ → Stores vectorized policy chunks
├── outputs/ → Final gap reports (JSON/CSV)
├── parser/ → (Optional) Text preprocessors
├── ui/ → Streamlit app for UI
├── vector_db/ → ChromaDB for vector search
├── embed_engine.py → Chunk + embed policy (Phase 2)
├── rag_engine.py → Control reasoning + matching (Phase 3)
├── main.py → Loads and validates input files
├── export_gap_to_csv.py → CSV report exporter
├── run_dashboard.bat → Launches Streamlit UI
├── requirements.txt → Dependency list
└── README.md → You're here!
```

---

## How It Works

1. **Load Controls & Policy**
   - `main.py` ensures both files are clean and valid.

2. **Embed Policy**
   - `embed_engine.py` chunks and stores the sample policy in vector format using `MiniLM`.

3. **Gap Analysis**
   - `rag_engine.py` fetches semantically similar chunks and evaluates each control with an LLM.

4. **Export Report**
   - Results are saved to `gap_report.json` and can be exported as `.csv`.

5. **Visualize UI**
   - Streamlit app shows analysis, filters by match level, and lets users download reports.

---

## Output Sample (`gap_report.json`)

```json
{
  "control_id": "AC.L1-3.1.1",
  "status": "Partially Met",
  "matched_text": "All system users must authenticate using MFA...",
  "confidence_score": 0.78,
  "explanation": "The policy enforces MFA, but doesn't specify authorized user limitations."
}
```

## Why This Project Matters

- **Fast, local analysis** with zero API keys or cloud use
- **Transparent**: Each result shows score, reason, and supporting text
- **Runs on mid-tier systems** (8 GB RAM / 4 GB VRAM)
- **Mimics auditor-style reasoning** logic
- **Adaptable** for NIST 800-171, ISO 27001, India's DPDP, and more

## Future Roadmap

- Bulk upload support for controls via CSV/YAML
- Role-based access in Streamlit UI
- UI enhancements for control grouping and sorting
- Explore Mistral 7B and Mixtral for improved reasoning

## Built With

- Python 3.11+
- all-MiniLM-L6-v2 (HuggingFace)
- ChromaDB
- LlamaIndex
- Streamlit
- Ollama (for Gemma 2B inference)

## License

This project is intended for educational and compliance demonstration purposes.

---

### What You Should Do Next:

1. Clone or download this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the main analysis: `python main.py`
4. Launch the UI: `streamlit run ui/dashboard.py`

### Commands to Update Your Repository:

```bash
git add README.md
git commit -m "Fix README formatting: proper JSON blocks, improved structure"
git push origin main
```

