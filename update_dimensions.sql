-- 1. Drop the old matching function which depends on 1536
DROP FUNCTION IF EXISTS match_documents(vector(1536), float, int, uuid);

-- 2. Alter the documents table embedding column to support 3072 dimensions natively
ALTER TABLE public.documents 
  ALTER COLUMN embedding TYPE vector(3072);

-- 3. HNSW indices in typical PostgreSQL pgvector versions cannot natively support dimensions > 2000
-- Thus, we simply drop the earlier HNSW index and rely on Exact Nearest Neighbor linear matching.
DROP INDEX IF EXISTS documents_embedding_idx;

-- 4. Recreate the match_documents RPC logic with strictly a vector(3072) parameter
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
