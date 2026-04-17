import os
import tempfile
import requests
import pymupdf4llm
from dotenv import load_dotenv

load_dotenv()

from langchain_text_splitters import MarkdownTextSplitter
from supabase import create_client, Client

def get_gemini_embedding(text: str, api_key: str):
    """
    Directly hits the Google REST API for embeddings.
    This guarantees zero wrapper bugs/404 mismatches with SDK implementations!
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]}
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Google Native API Error {response.status_code}: {response.text}")
    
    return response.json()["embedding"]["values"]

def process_pdf_for_tenant(pdf_bytes: bytes, tenant_id: str, filename: str = "document.pdf"):
    """
    Processes highly structured PDF, preserves Markdown tables, 
    embeds text with Google REST API, and stores in Supabase pgvector.
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not all([supabase_url, supabase_key, gemini_key]):
        return {"status": "error", "message": "Missing environment variables."}

    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Extract PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_bytes)
        temp_pdf_path = temp_pdf.name

    try:
        markdown_text = pymupdf4llm.to_markdown(temp_pdf_path)
    finally:
        os.remove(temp_pdf_path)

    if not markdown_text.strip():
        return {"status": "error", "message": "No extractable text found in the PDF."}

    # Split using Markdown-aware boundaries
    text_splitter = MarkdownTextSplitter(chunk_size=1500, chunk_overlap=250)
    chunks = text_splitter.split_text(markdown_text)

    records = []
    
    # Generate Embeddings & Prep Database Upload
    for idx, chunk in enumerate(chunks):
        try:
            embedding = get_gemini_embedding(chunk, gemini_key)
        except Exception as e:
            return {"status": "error", "message": f"Embedding failed at chunk {idx}: {str(e)}"}
            
        records.append({
            "tenant_id": tenant_id,
            "content": chunk,
            "metadata": {
                "source": filename,
                "chunk_index": idx,
                "format": "markdown_tables"
            },
            "embedding": embedding
        })

    # Store in DB
    try:
        response = supabase.table("documents").insert(records).execute()
        return {
            "status": "success", 
            "message": f"Successfully processed and embedded {len(records)} structure-retained chunks."
        }
    except Exception as e:
        return {"status": "error", "message": f"Supabase Vector Upload failed: {str(e)}"}
