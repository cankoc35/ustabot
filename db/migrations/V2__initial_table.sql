CREATE TABLE IF NOT EXISTS embeddings (
    "id" SERIAL PRIMARY KEY,
    "createdAt" TIMESTAMPTZ DEFAULT NOW(),
    "updatedAt" TIMESTAMPTZ DEFAULT NOW(),
    "deletedAt" TIMESTAMPTZ DEFAULT NULL,
    "documents" TEXT NOT NULL,
    "embeddings" vector(1024) NOT NULL,
    "tsv" tsvector GENERATED ALWAYS AS (to_tsvector('english', "documents")) STORED
);

CREATE INDEX IF NOT EXISTS idx_embeddings_tsv ON embeddings USING gin(tsv);


