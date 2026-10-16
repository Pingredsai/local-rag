# LocalRAG

**English** | [简体中文](README.zh-CN.md) — **A private, self-hosted knowledge base that answers questions from your own documents.**

LocalRAG runs entirely inside your infrastructure. Documents, embeddings, retrieval, and answer generation stay on your machines. No cloud API is required at runtime.

> **Status:** Docker deployment verified on 2026-10-15  
> **Verified flow:** document upload -> indexing -> vector retrieval -> cited answer

---

## Why LocalRAG

Many teams cannot send internal documents to cloud AI services.

| Industry | Sensitive data | Why local matters |
|---|---|---|
| Legal | Case files, contracts | Client confidentiality |
| Healthcare | Patient records | Privacy and compliance |
| Finance / audit | Working papers, client data | Data protection |
| Manufacturing | Process and repair manuals | Intellectual property |
| Government / defense | Internal documents | Air-gapped environments |

LocalRAG is designed for teams that need AI-assisted document search without giving up control of the data.

---

## What it does

- Upload PDF, DOCX, TXT, or Markdown documents.
- Parse, chunk, embed, and index documents automatically.
- Ask questions in natural language.
- Generate answers from retrieved document context.
- Return source references for traceability.
- Run with Docker Compose on a local server or workstation.
- Operate without external AI APIs once images and models are available.

---

## Architecture

![LocalRAG architecture](docs/architecture.svg)

The system has three main containers:

| Component | Role |
|---|---|
| **FastAPI backend** | Document processing, RAG orchestration, REST API, static web UI |
| **Qdrant** | Persistent vector database |
| **Ollama** | Local embedding and generation runtime |

Detailed architecture notes: [`docs/architecture.md`](docs/architecture.md)

### Indexing flow

```text
Document -> parse -> chunk -> embed with bge-m3 -> store vectors in Qdrant
```

### Query flow

```text
Question -> embed -> retrieve Top-K chunks -> build prompt
         -> generate with local LLM -> return answer + sources
```

---

## Quick start

### Requirements

- Docker Engine or Docker Desktop with Docker Compose
- 8 GB RAM recommended
- 20 GB free disk space recommended
- Network access for the first image and model download

### Run locally

```bash
cp .env.example .env
docker compose up -d

docker exec localrag-ollama ollama pull qwen2.5:3b
docker exec localrag-ollama ollama pull bge-m3
```

Open: <http://localhost:8080>

The Compose file pins `ollama/ollama:0.11.3` to avoid the much larger `latest` image. For a smaller local test, use `qwen2.5:1.5b` and update `LLM_MODEL` in `.env`.

### Verify

```bash
docker compose ps
curl http://localhost:8080/api/health
```

Expected health response:

```json
{"status":"ok","qdrant":"ok","ollama":"ok","llm_model":"qwen2.5:3b","embed_model":"bge-m3"}
```

### Verified result

The current code was tested with:

- Docker Desktop 4.95.0
- Ollama 0.11.3
- Qdrant
- `bge-m3` for embeddings
- `qwen2.5:3b` for generation

A synthetic employee handbook was indexed as three chunks. The system answered annual-leave, remote-work, and information-security questions correctly and returned cited sources.

---

## Demo

- [Watch the 42-second demo](demo/video/localrag-demo.mp4)
- Demo script: `docs/demo-script.md`
- Synthetic source document: `demo/nova-employee-handbook.md`

![LocalRAG answer with sources](docs/screenshots/03-answer-with-source.png)
## Configuration

Edit `.env`:

```ini
# Embedding model used by Ollama
EMBED_MODEL=bge-m3

# Generation model used by Ollama
LLM_MODEL=qwen2.5:3b

# Retrieval depth
TOP_K=5
```

### Model guidance

| Hardware | Suggested model | Notes |
|---|---|---|
| CPU / laptop | `qwen2.5:1.5b` or `qwen2.5:3b` | Lower memory, slower generation |
| 8 GB VRAM | `qwen2.5:7b` | Better answer quality |
| 24 GB VRAM | `qwen2.5:14b` | Stronger production candidate |
| 48 GB+ VRAM | `qwen2.5:32b` | Highest quality, larger resource footprint |

---

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check Qdrant and Ollama connectivity |
| POST | `/api/documents/upload` | Upload and index a document |
| GET | `/api/documents` | List indexed documents |
| DELETE | `/api/documents/{id}` | Delete a document and its vectors |
| POST | `/api/chat` | Ask a question, non-streaming |
| POST | `/api/chat/stream` | Ask a question, streaming text response |

### Upload a document

```bash
curl -X POST http://localhost:8080/api/documents/upload \
  -F "file=@handbook.pdf"
```

### Ask a question

```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the approval process?","top_k":5}'
```

---

## Air-gapped deployment

Prepare everything on a machine with network access:

1. Pull the Docker images.
2. Pull the Ollama models.
3. Save the Docker images with `docker save`.
4. Copy the project directory, saved images, and `data/ollama` model directory to the air-gapped machine.
5. Load the images with `docker load`.
6. Start the stack with `docker compose up -d`.

At runtime, LocalRAG does not call external AI APIs and has no telemetry.

---

## Project structure

```text
local-rag/
├── docker-compose.yml
├── .env.example
├── LICENSE                   MIT
├── SECURITY.md               Security policy
├── package.json              Demo tooling
├── README.md                 English README
├── README.zh-CN.md           Chinese README
├── docs/
│   ├── architecture.md       Architecture explanation
│   ├── architecture.svg      Architecture diagram
│   ├── demo-script.md        Demo script
│   └── screenshots/          Demo screenshots
├── demo/
│   ├── nova-employee-handbook.md
│   └── video/localrag-demo.mp4
├── scripts/
│   └── capture-localrag.cjs  Automated screenshots and recording
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── api/
│       ├── models/
│       └── services/
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
└── data/                     Runtime data, not committed
```

---

## Current limitations

- Text-based PDF only. Scanned PDFs require OCR.
- Single knowledge base in the current version.
- No built-in authentication or multi-tenant permissions yet.
- Reranker support is planned, not implemented.
- Answer quality depends on document quality, chunking, and the selected model.

---

## Development status

| Capability | Status |
|---|---|
| Document upload and indexing | Implemented |
| Vector retrieval | Implemented |
| Cited answers | Implemented |
| Streaming responses | Implemented |
| Static web UI | Implemented |
| Docker Compose deployment | Verified |
| Air-gapped preparation | Documented |
| OCR | Planned |
| Reranker | Planned |
| Multi-knowledge-base support | Planned |
| Authentication and permissions | Planned |

---

## License

MIT License

---

## Contact

- GitHub: <https://github.com/Pingredsai>
- Email: siquhjh@gmail.com