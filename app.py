import os
import streamlit as st
import tempfile
from dotenv import load_dotenv

load_dotenv()

from pdf_processor import process_pdf_for_tenant
from rag_agent import answer_query

# Streamlit Page Config
st.set_page_config(page_title="Architecture RAG", page_icon="🏢", layout="wide")

st.title("🏢 Architectural RAG Copilot")
st.markdown("Upload structural PDF specifications and query them instantly using Supabase PGVector & Gemini 1.5 Pro.")

# Manage Tenant ID in state
if 'tenant_id' not in st.session_state:
    st.session_state.tenant_id = "00000000-0000-0000-0000-000000000000"

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar for Component Uploads
with st.sidebar:
    st.header("1. Data Ingestion")
    st.info("Upload standard or structural architectural PDFs. Tables will be heavily preserved in vector state.")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Process & Embed PDF", type="primary"):
            with st.spinner("Extracting structural tables and pushing vectors to Supabase..."):
                pdf_bytes = uploaded_file.read()
                result = process_pdf_for_tenant(pdf_bytes, st.session_state.tenant_id, filename=uploaded_file.name)
                
                if result.get("status") == "success":
                    st.success(result["message"])
                else:
                    st.error(f"Error: {result.get('message')}")
                    
    st.markdown("---")
    st.caption("Active Auth Tenant ID:")
    st.code(st.session_state.tenant_id)

# Main UI Chat Interaction
st.header("2. Search & Analyze")

# Display previous chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("View Retrieved Context Citations"):
                for s in msg["sources"]:
                    st.caption(f"📄 {s.get('source')} (Chunk #{s.get('chunk_index')} - Format: {s.get('format', 'unknown')})")

# Chat input
query = st.chat_input("E.g., What are the tolerance specifications listed in the table?")
if query:
    # Render user query
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Render AI Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Performing PGVector semantic search & streaming Gemini..."):
            res = answer_query(query, st.session_state.tenant_id)
            
            if res.get("status") == "success":
                st.markdown(res["answer"])
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": res["answer"], 
                    "sources": res.get("sources", [])
                })
                # Show sources below answer
                with st.expander("View Retrieved Context Citations"):
                    for s in res.get("sources", []):
                        st.caption(f"📄 {s.get('source')} (Chunk #{s.get('chunk_index')} - Format: {s.get('format', 'unknown')})")
            else:
                st.error("Engine Error: " + res.get("message", "Unknown error"))
