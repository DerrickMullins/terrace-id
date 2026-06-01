-- Add fingerprint column for chromaprint-based matching
ALTER TABLE chants ADD COLUMN IF NOT EXISTS fingerprint TEXT;
