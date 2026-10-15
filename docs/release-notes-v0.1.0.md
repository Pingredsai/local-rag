# LocalRAG v0.1.0

## Highlights

- Private Docker Compose deployment with Qdrant, Ollama, and FastAPI
- Local document parsing, chunking, embedding, retrieval, and answer generation
- Source references in the web UI
- Streaming answers
- Docker Desktop verification on Windows
- English and Chinese README
- Architecture diagram and demo assets

## Verified flow

The release was tested with:

- Docker Desktop 4.95.0
- Ollama 0.11.3
- Qdrant
- `bge-m3` embeddings
- `qwen2.5:3b` generation

The test flow uploaded a synthetic employee handbook, indexed it as three chunks, answered policy questions, and returned cited sources.

## Quick start

```bash
cp .env.example .env
docker compose up -d
docker exec localrag-ollama ollama pull qwen2.5:3b
docker exec localrag-ollama ollama pull bge-m3
```

Open <http://localhost:8080>.

## Current limitations

- Text-based PDFs only; OCR is not included
- Single knowledge base
- No authentication or multi-tenant permissions
- Reranker is planned but not implemented
- Answer quality depends on the selected model and document quality

## License

MIT