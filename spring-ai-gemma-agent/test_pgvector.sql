-- Create test table with vector column
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    embedding vector(3)
);

-- Insert sample documents with vectors
INSERT INTO documents (name, embedding) VALUES
    ('Document A', '[0.1, 0.2, 0.3]'),
    ('Document B', '[0.4, 0.5, 0.6]'),
    ('Document C', '[0.7, 0.8, 0.9]');

-- Retrieve all documents
SELECT id, name, embedding FROM documents;

-- Test similarity search (find closest vectors to [0.2, 0.3, 0.4])
SELECT id, name, embedding, embedding <-> '[0.2, 0.3, 0.4]'::vector AS distance
FROM documents
ORDER BY distance
LIMIT 2;
