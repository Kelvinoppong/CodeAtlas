# 🗺️ CodeAtlas

A code analysis platform that uses your file tree to provide comprehensive codebase context, AI file modification, branching tree tools, and stunning visualizations.

![CodeAtlas Screenshot](docs/screenshot.png)

## Features

- **3-Pane UX**: File Tree (left) + Graph/Chat/Insights (center) + Code Editor (right)
- **Codebase Q&A**: "How does this work?", "Where is X used?", "What breaks if I change Y?"
- **Visualizations**: Dependency graph, call graph, module graph, change impact
- **Safe AI Modifications**: Multi-file edits, diffs, apply/rollback, commit

## Tech Stack

- **Frontend**: Next.js, TypeScript, TailwindCSS, React Flow
- **Backend**: FastAPI, Python
- **Database**: PostgreSQL + pgvector
- **AI**: Gemini 1.5 Flash / OpenAI

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose

### 1. Start Database

```bash
docker-compose up -d
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy env and add your keys
cp .env.example .env

# Run the server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install

# Copy env
cp .env.example .env.local

# Run dev server
npm run dev
```

### 4. Open the App

Visit [http://localhost:3000](http://localhost:3000)

## Project Structure

```
CodeAtlas/
├── frontend/           # Next.js app
│   ├── src/
│   │   ├── app/        # Pages & layout
│   │   └── components/ # React components
│   └── package.json
├── backend/            # FastAPI app
│   ├── app/
│   │   ├── api/        # API routes
│   │   ├── core/       # Config, DB
│   │   └── main.py     # Entry point
│   └── requirements.txt
├── docker-compose.yml  # PostgreSQL + Redis
└── plan.md             # Detailed project plan
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /projects/import` | Import a repository |
| `GET /snapshots/{id}/tree` | Get file tree |
| `GET /snapshots/{id}/files?path=...` | Get file content |
| `GET /snapshots/{id}/symbols` | Search symbols |
| `POST /snapshots/{id}/ai/chat` | Chat about codebase |
| `POST /changesets/{id}/apply` | Apply code changes |

## Roadmap

- [x] Phase 1: MVP (3-pane UI, file tree, graph, chat)
- [ ] Phase 2: Safe edits + Git awareness
- [ ] Phase 3: Collaboration + scale

## License

MIT
