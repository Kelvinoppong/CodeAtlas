<p align="center">
  <img src="docs/logo.png" alt="CodeAtlas Logo" width="120" />
</p>

<h1 align="center">🗺️ CodeAtlas</h1>

<p align="center">
  <strong>Navigate your codebase like never before.</strong>
</p>

<p align="center">
  A code analysis platform that transforms your repository into an interactive, explorable map — with AI-powered insights, stunning visualizations, and safe modification tools.
</p>

<p align="center">
  <img src="docs/interface.png" alt="CodeAtlas Interface" width="90%" />
</p>

<p align="center">
  <img src="docs/chat-demo.png" alt="AI Chat Demo - Explaining Code" width="90%" />
</p>
<p align="center"><em>AI-powered code explanation with Ollama (local LLM)</em></p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#api-reference">API</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat-square&logo=typescript" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Tree--sitter-Parsing-green?style=flat-square" alt="Tree-sitter" />
  <img src="https://img.shields.io/badge/Ollama-Local_LLM-white?style=flat-square&logo=ollama" alt="Ollama" />
</p>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🌳 Interactive File Explorer
Browse your codebase with a smart file tree that respects `.gitignore`, detects 30+ languages, and provides instant navigation.

### 🔮 Dependency Graphs
Visualize how your code connects — imports, calls, and references rendered as beautiful, interactive diamond node graphs.

### 💬 AI-Powered Q&A
Ask natural questions about your codebase: *"How does authentication work?"*, *"Where is this function used?"*, *"What happens if I change X?"*

</td>
<td width="50%">

### 📝 Smart Code Viewer
Syntax-highlighted code with symbol navigation, jump-to-definition, and inline explanations.

### 🔍 Symbol Search
Find functions, classes, and variables instantly. Search across your entire codebase with real-time results.

### 🧠 Code Parsing Engine
Tree-sitter powered parsing for Python, JavaScript, and TypeScript with fallback regex support for other languages.

</td>
</tr>
<tr>
<td width="50%">

### 🔄 Safe Code Modifications
Apply AI-proposed changes with confidence — full diff preview, one-click apply, and instant rollback if anything goes wrong.

### 📊 Impact Analysis
Before you change anything, see exactly what breaks. Trace dependencies across files and get risk assessments.

</td>
<td width="50%">

### 🌿 Git Integration
Branch-aware snapshots, commit history, and seamless git workflow integration. Create commits directly from applied changes.

### 🛡️ ChangeSet Management
Review, apply, rollback, and commit code changes with full audit trail. Never lose your original code.

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ 
- **Python** 3.11+
- **Docker** & Docker Compose

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/CodeAtlas.git
cd CodeAtlas
```

### 2. Start the Database

```bash
docker-compose up -d
```

This spins up PostgreSQL (with pgvector for embeddings) and Redis.

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server (auto-creates tables)
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Import Your First Project

1. Visit **[http://localhost:3000](http://localhost:3000)**
2. Click **Import** in the sidebar
3. Enter your project name and local path (e.g., `/home/user/my-project`)
4. Wait for indexing to complete
5. Explore your codebase!

---

## 🏗️ Architecture

CodeAtlas uses a modern, layered architecture designed for extensibility and performance.

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  File Tree  │  │   Graph     │  │    Code Editor      │  │
│  │  Component  │  │   Viewer    │  │    + Chat Panel     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         └────────────────┼────────────────────┘              │
│                          │ Zustand Store                     │
│                          │ API Client                        │
└──────────────────────────┼──────────────────────────────────┘
                           │ HTTP/REST
┌──────────────────────────┼──────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   API       │  │  Indexing   │  │   AI Integration    │  │
│  │   Routes    │  │  Engine     │  │   (Chat/Explain)    │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         └────────────────┼────────────────────┘              │
│                          │ SQLAlchemy Async                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│              PostgreSQL + pgvector                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐    │
│  │Projects │ │Snapshots│ │ Files   │ │ Symbols/Refs    │    │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Indexing Pipeline

When you import a project, CodeAtlas runs a multi-stage indexing pipeline:

```
1. SCAN          2. PARSE           3. EXTRACT         4. STORE
   │                 │                  │                  │
   ▼                 ▼                  ▼                  ▼
┌──────────┐    ┌──────────┐      ┌──────────┐      ┌──────────┐
│ Discover │───▶│ Tree-    │─────▶│ Symbols  │─────▶│ Database │
│ Files    │    │ sitter   │      │ + Refs   │      │ + Index  │
│          │    │ Parse    │      │          │      │          │
│ .gitignore    │ AST      │      │ Classes  │      │ Fast     │
│ Binary skip   │ Extract  │      │ Functions│      │ Queries  │
└──────────┘    └──────────┘      │ Imports  │      └──────────┘
                                  └──────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 14, React 18, TypeScript | UI Framework |
| **Styling** | TailwindCSS | Dark theme, responsive design |
| **State** | Zustand | Global state management |
| **Visualization** | React Flow | Interactive graph rendering |
| **Backend** | FastAPI, Python 3.11+ | Async API server |
| **ORM** | SQLAlchemy 2.0 (async) | Database models |
| **Database** | PostgreSQL 16 + pgvector | Persistent storage + vectors |
| **Parsing** | Tree-sitter | AST extraction for Python/JS/TS |
| **AI/LLM** | Ollama (local) / Gemini / OpenAI | Chat & code explanation |

---

## 📁 Project Structure

```
CodeAtlas/
├── frontend/                        # Next.js application
│   ├── src/
│   │   ├── app/                     # Pages & layouts
│   │   │   ├── globals.css          # Dark theme styles
│   │   │   ├── layout.tsx           # Root layout
│   │   │   └── page.tsx             # Main 3-pane workspace
│   │   ├── components/              # React components
│   │   │   ├── Header.tsx           # Nav bar + symbol search
│   │   │   ├── FileTree.tsx         # Left panel - file explorer
│   │   │   ├── CenterCanvas.tsx     # Tab container (Chat/Graph/Changes)
│   │   │   ├── GraphViewer.tsx      # Dependency graph
│   │   │   ├── ChatPanel.tsx        # AI chat interface
│   │   │   ├── CodeEditor.tsx       # Syntax-highlighted viewer
│   │   │   ├── ChangeSetPanel.tsx   # ChangeSet management UI
│   │   │   ├── DiffViewer.tsx       # Unified diff display
│   │   │   ├── ProjectImport.tsx    # Import modal
│   │   │   ├── AuthModal.tsx        # Login/register modal
│   │   │   ├── UserMenu.tsx         # User dropdown menu
│   │   │   └── PresenceIndicator.tsx # Real-time presence
│   │   └── lib/                     # Utilities
│   │       ├── api.ts               # API client + types
│   │       ├── store.ts             # Zustand state
│   │       └── authStore.ts         # Authentication state
│   ├── package.json
│   └── tailwind.config.ts
│
├── backend/                         # FastAPI application
│   ├── app/
│   │   ├── api/                     # Route handlers
│   │   │   ├── projects.py          # CRUD + import
│   │   │   ├── snapshots.py         # Tree, graphs, status
│   │   │   ├── files.py             # Content retrieval
│   │   │   ├── symbols.py           # Search + references
│   │   │   ├── ai.py                # Chat, explain
│   │   │   └── changesets.py        # Apply/rollback
│   │   ├── core/                    # Configuration
│   │   │   ├── config.py            # Settings
│   │   │   └── database.py          # Async DB session
│   │   ├── models/                  # SQLAlchemy models
│   │   │   ├── project.py           # Project entity
│   │   │   ├── snapshot.py          # Indexed snapshot
│   │   │   ├── file.py              # File metadata
│   │   │   ├── symbol.py            # Symbols + references
│   │   │   ├── embedding.py         # Vector chunks
│   │   │   └── changeset.py         # Code changes
│   │   ├── indexer/                 # Indexing engine
│   │   │   ├── scanner.py           # File discovery
│   │   │   ├── parser.py            # Tree-sitter + regex
│   │   │   └── engine.py            # Pipeline orchestration
│   │   ├── services/                # Business logic
│   │   │   ├── git_service.py       # Git operations
│   │   │   ├── impact_analyzer.py   # Dependency analysis
│   │   │   ├── auth_service.py      # JWT authentication
│   │   │   ├── audit_service.py     # Action logging
│   │   │   └── incremental_indexer.py # Smart re-indexing
│   │   └── main.py                  # FastAPI entry point
│   └── requirements.txt
│
├── docker-compose.yml               # PostgreSQL + Redis
├── plan.md                          # Detailed spec
├── LICENSE                          # MIT
└── README.md
```

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/login` | Login with credentials |
| `POST` | `/auth/logout` | Logout current user |
| `POST` | `/auth/refresh` | Refresh access token |
| `GET` | `/auth/me` | Get current user |
| `PUT` | `/auth/me` | Update profile |
| `POST` | `/auth/change-password` | Change password |

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/projects` | List all projects |
| `POST` | `/projects/import` | Import a new repository |
| `GET` | `/projects/{id}` | Get project details |
| `DELETE` | `/projects/{id}` | Delete project |
| `GET` | `/projects/{id}/snapshots` | List project snapshots |
| `POST` | `/projects/{id}/snapshots` | Start async indexing |
| `POST` | `/projects/{id}/snapshots/sync` | Index synchronously |
| `POST` | `/projects/{id}/snapshots/branch` | Index specific git branch |

### Snapshots & Files

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/snapshots/{id}/status` | Get indexing progress |
| `GET` | `/snapshots/{id}/tree` | Get file tree structure |
| `GET` | `/snapshots/{id}/files?path=...` | Get file content |
| `GET` | `/snapshots/{id}/files/list` | List all files |
| `GET` | `/snapshots/{id}/graphs/deps` | Get dependency graph |
| `POST` | `/snapshots/{id}/impact` | Analyze change impact |

### Git

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/snapshots/{id}/git/status` | Get working directory status |
| `GET` | `/snapshots/{id}/git/branches` | List all branches |
| `GET` | `/snapshots/{id}/git/commits` | Get commit history |

### Symbols

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/snapshots/{id}/symbols?query=...` | Search symbols |
| `GET` | `/snapshots/{id}/symbols?kind=class` | Filter by kind |
| `GET` | `/snapshots/{id}/symbols/{symbolId}` | Get symbol details |
| `GET` | `/snapshots/{id}/symbols/{symbolId}/references` | Find references |
| `GET` | `/snapshots/{id}/symbols/kinds/list` | List symbol kinds |

### AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/snapshots/{id}/ai/chat` | Chat about codebase |
| `POST` | `/snapshots/{id}/ai/explain` | Explain file/symbol |
| `POST` | `/snapshots/{id}/ai/propose-changes` | Generate refactor |

### ChangeSets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/changesets` | List all changesets |
| `POST` | `/changesets` | Create new changeset with patches |
| `GET` | `/changesets/{id}` | Get changeset details |
| `POST` | `/changesets/{id}/apply` | Apply changes to files |
| `POST` | `/changesets/{id}/rollback` | Restore original files |
| `POST` | `/changesets/{id}/commit` | Create git commit |
| `DELETE` | `/changesets/{id}` | Delete proposed changeset |

### Real-time (WebSocket)

| Endpoint | Description |
|----------|-------------|
| `WS /ws/{project_id}?token=...` | Real-time collaboration WebSocket |
| `GET /presence/{project_id}` | Get current online users (REST fallback) |

**WebSocket Message Types:**
- `cursor_move` - Update cursor position
- `file_open` - Notify file opened
- `file_close` - Notify file closed
- `chat` - Send chat message
- `presence_update` - User presence changed
- `user_joined` / `user_left` - User connected/disconnected

---

## ⚙️ Configuration

Create a `.env` file in the `backend/` directory:

```env
# Database (required)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/codeatlas

# AI Provider - choose one: "ollama" (local), "gemini", or "openai"
AI_PROVIDER=ollama

# Ollama (local - recommended, no API key needed)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# Cloud providers (optional alternatives)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Optional
REDIS_URL=redis://localhost:6379/0
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]
```

The database tables are created automatically on first startup.

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with 💜 for developers who want to understand their code better.
</p>

<p align="center">
  <a href="https://github.com/yourusername/CodeAtlas">⭐ Star this repo</a> if you find it useful!
</p>
