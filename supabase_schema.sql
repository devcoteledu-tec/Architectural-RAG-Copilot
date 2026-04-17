-- Enable the pgvector extension to work with embedding vectors
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the tenants table
CREATE TABLE public.tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS on the tenants table
ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read/write their own tenant data
-- Assuming the active tenant_id is passed via JWT claims as 'app_metadata.tenant_id'
-- You can modify current_setting() if you pass the tenant ID differently (e.g. custom headers or auth mapping)
CREATE POLICY "Tenant isolation for tenants table" 
  ON public.tenants 
  FOR ALL 
  USING (id = (NULLIF(current_setting('request.jwt.claims', true), '')::jsonb -> 'app_metadata' ->> 'tenant_id')::uuid);


-- Create the documents table
CREATE TABLE public.documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  metadata JSONB,
  embedding VECTOR(3072), -- 3072 is required for Gemini's current provisioned models
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS on the documents table
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

-- Policy: Queries only return vectors/documents belonging to the active tenant_id
CREATE POLICY "Tenant isolation for documents table" 
  ON public.documents 
  FOR ALL 
  USING (tenant_id = (NULLIF(current_setting('request.jwt.claims', true), '')::jsonb -> 'app_metadata' ->> 'tenant_id')::uuid);


-- HNSW Indexes in Postgres PgVector are often limited to 2000 dimensions. 
-- Since Gemini outputs 3072, we omit an HNSW index here. Exact Nearest Neighbor lookup suffices seamlessly!


-- Create the match_documents RPC function (used for vector similarity search via REST API)
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(3072),
  match_threshold float,
  match_count int,
  filter_tenant_id uuid
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) AS similarity
  FROM documents
  WHERE documents.tenant_id = filter_tenant_id
    AND 1 - (documents.embedding <=> query_embedding) > match_threshold
  ORDER BY documents.embedding <=> query_embedding
  LIMIT match_count;
$$;
