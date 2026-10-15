# LocalRAG Architecture

## System context

LocalRAG runs inside a customer-controlled network. The browser talks only to the FastAPI application. FastAPI uses Qdrant for vector storage and Ollama for local embeddings and text generation.

![LocalRAG architecture](architecture.svg)

## Container view

```mermaid
flowchart LR
    User[User / Browser] -->|HTTP| API[FastAPI Backend]
    API -->|Upload and manage| FS[(Document Storage)]
    API -->|Embed text| EMB[Ollama: bge-m3]
    API -->|Store and search vectors| QD[(Qdrant)]
    API -->|Generate answer| LLM[Ollama: Qwen]
    EMB --> API
    QD --> API
    LLM --> API
```

## Indexing flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant A as FastAPI
    participant O as Ollama
    participant Q as Qdrant

    U->>B: Select document
    B->>A: POST /api/documents/upload
    A->>A: Parse and chunk text
    A->>O: Embed chunks with bge-m3
    O-->>A: Vectors
    A->>Q: Upsert vectors and metadata
    Q-->>A: Indexed
    A-->>B: Document ID and chunk count
```

## Query flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant A as FastAPI
    participant O as Ollama
    participant Q as Qdrant

    U->>B: Ask a question
    B->>A: POST /api/chat/stream
    A->>O: Embed the question
    O-->>A: Query vector
    A->>Q: Search Top-K chunks
    Q-->>A: Relevant chunks and metadata
    A->>O: Generate answer from retrieved context
    O-->>A: Generated answer
    A-->>B: Answer with source references
```

## Components

| Component | Responsibility | Storage |
|---|---|---|
| Browser UI | Upload documents, ask questions, display answers and sources | None |
| FastAPI backend | Parsing, chunking, RAG orchestration, REST API, static files | Document volume |
| Qdrant | Vector persistence and similarity search | `data/qdrant` |
| Ollama | Local embedding and generation runtime | `data/ollama` |
| Document storage | Original uploaded files | `data/documents` |

## Trust boundary

The important boundary is the customer network. At runtime:

- No document content is sent to a third-party AI API.
- No cloud vector database is used.
- No telemetry service is required.
- Docker images and Ollama models are prepared ahead of time for air-gapped installations.

Network access is required only during initial installation to pull images and models.