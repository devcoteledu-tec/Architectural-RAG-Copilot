# 🏢 Architectural RAG Copilot

A highly customized Retrieval-Augmented Generation (RAG) platform uniquely engineered to deeply parse structural documentation, preserve Markdown tables, and run native Semantic PGVector searches tuned for Architecture, Engineering, and Construction (AEC) professionals.

This platform completely bypasses common LangChain wrapper bugs by interacting directly with the Google Gemini ecosystem natively while leveraging Supabase `pgvector` for enterprise tenant isolation.

## 🌟 Key Features
- **Structural Chunking Engine:** Integrates `pymupdf4llm` to physically parse grids and architectural specs directly into Markdown before breaking them down.
- **REST Implementation:** Explicit HTTP `requests` logic linking backend to Gemini APIs to firmly prevent random wrapper/version `404 Not Found` conflicts.
- **Tenant Isolation:** Postgres Row Level Security (RLS) ensures that companies (tenant IDs) cannot access each other's proprietary blueprints natively at the database level.
- **Graphical Dashboard:** Launch a beautiful, responsive Streamlit dashboard locally to interact with specifications directly.

---

## 🚀 Setup & Installation

### 1. Requirements
Ensure your Python environment is ready by installing the necessary core dependencies.
```bash
pip install streamlit requests pymupdf4llm supabase python-dotenv langchain-text-splitters
```

### 2. Environment Setup
Create a `.env` file within the root directory matching your credentials:
```env
SUPABASE_URL="https://[YOUR_INSTANCE].supabase.co"
SUPABASE_SERVICE_ROLE_KEY="sb_publishable_..."
GEMINI_API_KEY="your_api_key_here"
```

### 3. Supabase Postgres Initialization
You must configure your Supabase instance to hold your specific data layouts and `pgvector` logic. Open your Supabase SQL Editor and run these in this specific order:
1. `supabase_schema.sql` (Creates your Tenant / Document architecture + Match function)
2. `update_dimensions.sql` (Ensures dimensions run at `3072` matching Gemini bounds, without crashing HNSW limits)
3. `update_rls.sql` (Bypasses local RLS Auth blocks via Anon keys and spins up the Demo Tenant mapping)

---

## 🎮 How to Run

### Streamlit Graphical Dashboard (Recommended)
This launches a beautiful local web view mimicking ChatGPT to drag, drop, and analyze PDFs graphically.
```bash
python -m streamlit run app.py
```

### Command Line Interface (CLI)
You can directly parse and test outputs aggressively using the automated CLI tester file.
```bash
# Ingest an architectural PDF:
python run_demo.py --pdf my_structural_codes.pdf

# Ask Gemini a natively embedded semantic question:
python run_demo.py --query "What is the maximum electrical output allowed here?"
```

---

## 🏗️ Technical Architecture
* **`app.py`:** The primary Graphical Interface rendering the Streamlit DOM.
* **`pdf_processor.py`:** Reads incoming Document bits, retains markdown tables natively, slices it contextually, sends HTTP requests to Gemini to vectorize them, and inserts rows into `Supabase`.
* **`rag_agent.py`:** Triggers the Supabase RPC `match_documents` Postgres function logic and synthesizes context into highly deterministic LLM responses using `Gemini 1.5 Pro`.
