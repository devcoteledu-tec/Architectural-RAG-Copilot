import os
import requests
from dotenv import load_dotenv

load_dotenv()

from supabase import create_client, Client

def get_gemini_embedding(text: str, api_key: str):
    """Directly hits the REST API to fetch embeddings (bulletproof implementation)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]}
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Google Native API Error {response.status_code}: {response.text}")
    return response.json()["embedding"]["values"]

def get_gemini_generation(prompt: str, api_key: str):
    """Directly hits the Gemini 1.5 Pro REST API for deterministic answers."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.0 # Strict determinism for structured tables
        }
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Google Native GenAI Error {response.status_code}: {response.text}")
        
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]

def answer_query(query: str, tenant_id: str):
    """
    Agent that utilizes Supabase RPC match algorithm, and synthesizes answers natively.
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not all([supabase_url, supabase_key, gemini_key]):
        return {"status": "error", "message": "Missing environment variables."}

    supabase: Client = create_client(supabase_url, supabase_key)

    # 1. Direct Embed Vector Generation
    try:
        query_embedding = get_gemini_embedding(query, gemini_key)
    except Exception as e:
        return {"status": "error", "message": f"Failed embedding: {str(e)}"}

    # 2. Find closest semantic Match in Vector Database
    try:
        response = supabase.rpc("match_documents", {
            "query_embedding": query_embedding,
            "match_threshold": 0.5, 
            "match_count": 5,       
            "filter_tenant_id": tenant_id
        }).execute()
        
        matched_docs = response.data
    except Exception as e:
        return {"status": "error", "message": f"Vector search failed (Did you run the SQL migration?): {str(e)}"}

    context_text = "\n\n---\n\n".join([doc["content"] for doc in matched_docs]) if matched_docs else ""

    # 3. Inject into Prompt for Synthesis Synthesis
    prompt = f"""
You are an intelligent engineering/architectural assistant for a specific tenant.
Your goal is to answer the user's query accurately using ONLY the retrieved context provided below.

INSTRUCTIONS:
1. Review the Context, paying close attention to MARKDOWN TABLES and NUMERICAL SPECIFICATIONS. Structural dimensions, architectural tolerances, and material properties must be quoted EXACTLY as shown in the tables.
2. Answer the user's query using strictly the information found within the Context. Never mutate or round the numbers.
3. If analyzing structural or column data, summarize relationships carefully based on the table layouts.
4. If the Context DOES NOT contain enough numerical or structural information to answer confidently, DO NOT GUESS OR HALLUCINATE. Politely ask the user for clarification.

CONTEXT (Contains Markdown tabular structures):
{context_text}

USER QUERY:
{query}

ANSWER:
"""

    try:
        ai_response_text = get_gemini_generation(prompt, gemini_key)
        
        return {
            "status": "success",
            "answer": ai_response_text,
            "sources": [doc["metadata"] for doc in matched_docs] if matched_docs else []
        }
    except Exception as e:
         return {"status": "error", "message": f"LLM Generation failed: {str(e)}"}
