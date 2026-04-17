import os
import argparse
from dotenv import load_dotenv

# Automatically loads your API keys from the .env file
load_dotenv()

from pdf_processor import process_pdf_for_tenant
from rag_agent import answer_query

# We will use a standard hardcoded tenant_id for this demo test
DEMO_TENANT_ID = "00000000-0000-0000-0000-000000000000"

def main():
    parser = argparse.ArgumentParser(description="Test your Document RAG platform.")
    parser.add_argument("--pdf", type=str, help="Path to a structural PDF file to ingest.", required=False)
    parser.add_argument("--query", type=str, help="A query to ask the Gemini agent.", required=False)
    
    args = parser.parse_args()

    # Step 1: Handle PDF Ingestion if requested
    if args.pdf:
        print(f"🚀 Ingesting PDF: '{args.pdf}' for Tenant: {DEMO_TENANT_ID}...")
        try:
            with open(args.pdf, "rb") as f:
                pdf_bytes = f.read()
            
            # This calls the processor that uses PyMuPDF and saves directly to Supabase vector DB
            result = process_pdf_for_tenant(pdf_bytes, DEMO_TENANT_ID, filename=os.path.basename(args.pdf))
            
            if result.get("status") == "success":
                print(f"✅ Success! {result['message']}")
            else:
                print(f"❌ Error: {result.get('message')}")
        except FileNotFoundError:
            print(f"❌ Error: Could not find file: {args.pdf}")
        except Exception as e:
            print(f"❌ Fatal Error generating embeddings: {str(e)}")
            
    # Step 2: Handle Question Asking if requested
    if args.query:
        print(f"\n🤖 Asking Gemini: '{args.query}' for Tenant: {DEMO_TENANT_ID}...")
        
        # This calls Supabase vector matching to get context, then runs Gemini to formulate answer
        result = answer_query(args.query, DEMO_TENANT_ID)
        
        if result.get("status") == "success":
            print("\n" + "="*50)
            print("🔹 AGENT ANSWER:")
            print("="*50)
            print(result["answer"])
            print("\n" + "-"*50)
            print("📑 SOURCES RETRIEVED (pgvector matches):")
            
            sources = result.get("sources", [])
            if not sources:
                print("No context was retrieved from Supabase.")
            for i, doc in enumerate(sources):
                print(f"{i+1}. {doc.get('source')} (Format: {doc.get('format', 'unknown')})")
            print("-" * 50)
        else:
            print(f"❌ Error: {result.get('message')}")
            
    # Step 3: Print help if no arguments passed
    if not args.pdf and not args.query:
        print("💡 Welcome to your RAG Demo!")
        print("Please provide a --pdf to ingest, a --query to ask the agent, or both!")
        print("\nExamples:")
        print("  1) Ingest a PDF:  python run_demo.py --pdf my_schema.pdf")
        print("  2) Ask a Query:   python run_demo.py --query \"What are the structural dimensions?\"")
        print("  3) Do both:       python run_demo.py --pdf my_schema.pdf --query \"Summarize everything.\"")

if __name__ == "__main__":
    main()
