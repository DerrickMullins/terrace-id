-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to chants table
-- 40 dimensions: 20 MFCC means + 20 MFCC standard deviations
ALTER TABLE chants ADD COLUMN IF NOT EXISTS embedding vector(40);

-- IVFFlat index for approximate nearest-neighbor cosine search
-- Run AFTER embed.py has populated at least ~100 rows
CREATE INDEX IF NOT EXISTS chants_embedding_idx
ON chants USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- RPC function called by the API to find the closest matching chant
CREATE OR REPLACE FUNCTION match_chant(
    query_embedding vector(40),
    match_threshold  float   DEFAULT 0.3,
    match_count      int     DEFAULT 1
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
