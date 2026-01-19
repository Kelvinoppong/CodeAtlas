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
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#api-reference">API</a> •
  <a href="#roadmap">Roadmap</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat-square&logo=typescript" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql" alt="PostgreSQL" />
</p>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🌳 Interactive File Explorer
Browse your codebase with a smart file tree that respects `.gitignore`, detects languages, and provides instant navigation.

### 🔮 Dependency Graphs
Visualize how your code connects — imports, calls, and references rendered as beautiful, interactive node graphs.

### 💬 AI-Powered Q&A
Ask natural questions about your codebase: *"How does authentication work?"*, *"Where is this function used?"*, *"What happens if I change X?"*

</td>
<td width="50%">

### 📝 Smart Code Viewer
Syntax-highlighted code with symbol navigation, jump-to-definition, and inline AI explanations.

### 🛡️ Safe AI Modifications
Propose multi-file refactors with full diff preview, one-click apply, and instant rollback. Never lose code.

### 🔍 Semantic Search
Find code by meaning, not just text. Search across symbols, files, and documentation with vector-powered retrieval.

</td>
</tr>
</table>

---

## 🖼️ Screenshots

<p align="center">
  <img src="docs/screenshot.png" alt="CodeAtlas Interface" width="100%" />
</p>

<details>
<summary><strong>View More Screenshots</strong></summary>

| Graph View | Chat Interface | Code Editor |
|------------|----------------|-------------|
| ![Graph](docs/graph.png) | ![Chat](docs/chat.png) | ![Editor](docs/editor.png) |

</details>

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

# Configure environment (add your API keys)
cp .env.example .env

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local

# Start development server
npm run dev
```

### 5. Open CodeAtlas

Visit **[http://localhost:3000](http://localhost:3000)** and start exploring!

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, React 18, TypeScript, TailwindCSS |
| **Visualization** | React Flow, Mermaid |
| **Code Editor** | Monaco Editor |
| **Backend** | FastAPI, Python 3.11+ |
| **Database** | PostgreSQL 16 + pgvector |
| **Task Queue** | Redis (optional) |
| **AI/LLM** | Gemini 1.5 Flash, OpenAI GPT-4 |
| **Code Parsing** | Tree-sitter |

---

## 📁 Project Structure

```
CodeAtlas/
├── frontend/                    # Next.js application
│   ├── src/
│   │   ├── app/                 # Pages, layouts, global styles
│   │   │   ├── globals.css      # Dark theme + custom styles
│   │   │   ├── layout.tsx       # Root layout
│   │   │   └── page.tsx         # Main 3-pane workspace
│   │   └── components/          # React components
│   │       ├── Header.tsx       # Top navigation bar
│   │       ├── FileTree.tsx     # Left panel - file explorer
│   │       ├── CenterCanvas.tsx # Center panel - tabs container
│   │       ├── GraphViewer.tsx  # Dependency graph (React Flow)
│   │       ├── ChatPanel.tsx    # AI chat with citations
│   │       └── CodeEditor.tsx   # Right panel - code viewer
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── api/                 # API route handlers
│   │   │   ├── projects.py      # Project import & management
│   │   │   ├── snapshots.py     # Snapshot indexing & file trees
│   │   │   ├── files.py         # File content retrieval
│   │   │   ├── symbols.py       # Symbol search & references
│   │   │   ├── ai.py            # Chat, explain, propose changes
│   │   │   └── changesets.py    # Apply/rollback code changes
│   │   ├── core/
│   │   │   └── config.py        # Environment configuration
│   │   └── main.py              # FastAPI app entry point
│   └── requirements.txt
│
├── docker-compose.yml           # PostgreSQL + Redis containers
├── plan.md                      # Detailed implementation plan
└── README.md
```

---

## 📡 API Reference

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/projects` | List all projects |
| `POST` | `/projects/import` | Import a new repository |
| `GET` | `/projects/{id}` | Get project details |
| `POST` | `/projects/{id}/snapshots` | Start indexing |

### Snapshots & Files

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/snapshots/{id}/status` | Get indexing progress |
| `GET` | `/snapshots/{id}/tree` | Get file tree |
| `GET` | `/snapshots/{id}/files?path=...` | Get file content |
| `GET` | `/snapshots/{id}/graphs/deps` | Get dependency graph |

### Symbols

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/snapshots/{id}/symbols?query=...` | Search symbols |
| `GET` | `/snapshots/{id}/symbols/{symbolId}` | Get symbol details |
| `GET` | `/snapshots/{id}/symbols/{symbolId}/references` | Find all references |

### AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/snapshots/{id}/ai/chat` | Chat about codebase |
| `POST` | `/snapshots/{id}/ai/explain` | Explain file/symbol |
| `POST` | `/snapshots/{id}/ai/propose-changes` | Generate refactor plan |

### ChangeSets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/changesets` | List all changesets |
| `GET` | `/changesets/{id}` | Get changeset details |
| `POST` | `/changesets/{id}/apply` | Apply changes to repo |
| `POST` | `/changesets/{id}/rollback` | Undo applied changes |
| `POST` | `/changesets/{id}/commit` | Create git commit |

---

## 🗺️ Roadmap

### Phase 1 — MVP ✅
- [x] 3-pane UI (File Tree / Graph / Editor)
- [x] File tree with language detection
- [x] Dependency graph visualization
- [x] AI chat with citations
- [x] Basic symbol search

### Phase 2 — Safe Edits & Git
- [ ] ChangeSet diff viewer
- [ ] Apply/rollback functionality
- [ ] Multi-file refactoring
- [ ] Git commit integration
- [ ] Branch-aware snapshots
- [ ] Impact analysis ("what breaks if I change X?")

### Phase 3 — Collaboration & Scale
- [ ] Multi-user projects
- [ ] Real-time collaboration (PeerJS/WebRTC)
- [ ] Incremental indexing
- [ ] Large repo optimizations
- [ ] Enterprise RBAC & audit logs

---

## ⚙️ Configuration

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/codeatlas

# AI Providers (at least one required for AI features)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Optional
REDIS_URL=redis://localhost:6379/0
DEBUG=true
```

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
