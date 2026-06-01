-- Drop old index and column (40-dim), re-add as 104-dim
-- Run this in the Supabase SQL editor, then re-run embed.py

DROP INDEX  IF EXISTS chants_embedding_idx;
ALTER TABLE chants DROP COLUMN IF EXISTS embedding;
ALTER TABLE chants ADD  COLUMN embedding vector(104);

-- Recreate index (run again after embed.py finishes populating rows)
CREATE INDEX IF NOT EXISTS chants_embedding_idx
ON chants USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Updated RPC function for 104-dim vectors
CREATE OR REPLACE FUNCTION match_chant(
    query_embedding vector(104),
    match_threshold  float DEFAULT 0.3,
    match_count      int   DEFAULT 1
)
RETURNS TABLE (
    id          uuid,
    team        text,
    chant_name  text,
    audio_url   text,
    similarity  float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        id,
        team,
        chant_name,
        audio_url,
        1 - (embedding <=> query_embedding) AS similarity
    FROM chants
    WHERE embedding IS NOT NULL
      AND 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;
