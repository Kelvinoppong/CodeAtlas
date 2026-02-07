# CodeAtlas — Detailed Project Plan (Implementation-Ready)

## Product Summary (what you’re building)
**CodeAtlas** is a web app that ingests a repository’s **file tree + source code**, builds a **codebase context graph** (symbols, references, imports, calls), and provides:
- **3‑pane UX** (like your screenshot): **File Tree (left)** + **Graph/Chat/Insights (center)** + **Code Editor (right)**
- **Codebase Q&A** (“How does this work?”, “Where is X used?”, “What breaks if I change Y?”)
- **Visualizations** (dependency graph, call graph, module graph, branch/commit graph, change impact)
- **Safe AI file modification** (multi-file edits, diffs, apply/rollback, commit)

Primary design constraint: **“Deep context, safe edits.”** That means durable indexing, explicit provenance of answers, and guarded change application.

---

## UX Blueprint (match the screenshot)
### Layout
- **Left panel: Project Explorer**
  - Repo selector / import button
  - Search box
  - Tree view (gitignore-aware)
  - Quick actions: pin files, open in editor, “explain file”, “show deps”

- **Center panel: Context Canvas**
  - Tabs: **Chat**, **Graph**, **Timeline**, **Tasks**
  - Graph canvas shows interactive nodes/edges (imports/calls/refs)
  - “AI reasoning” responses anchored to code entities (files/symbols)

- **Right panel: Code Editor**
  - Monaco editor w/ syntax highlightingk
  - Jump to definition / references (from index)
  - AI “propose change” opens diff/preview

### Visual Design Targets (to look like the image)
- **Theme**: dark, high-contrast (near-black background, subtle gradients)
- **Three-column split**: narrow left, wide center, medium right
- **Rounded panels** with soft shadow and thin borders (glass-like cards)
- **Header bar** with project title + short subtitle
- **Pill tags** for tech stack (e.g., Next.js, FastAPI, TailwindCSS)
- **Primary action button** (e.g., “Website”) aligned right
- **Center canvas** supports both graph view and chat view with rich text
- **Left tree** shows file icons + collapsible folders (matches screenshot density)
- **Right editor** shows code with syntax theme similar to VS Code Dark+

### Key workflows (as in the screenshot)
- **Ingest repo → build index → show file tree**
- **Click node in graph → open file + highlight symbol**
- **Ask system-level question → response includes references and suggested graph path**
- **Propose multi-file refactor → review diffs → apply → optional git commit**

---

## Core Concepts & Domain Model
### Entities (minimum set)
- **Project**
  - id, name, root_path (or remote URL), default_branch, created_at
- **Snapshot**
  - id, project_id, git_commit (nullable), created_at, index_version
- **File**
  - id, snapshot_id, path, language, size_bytes, sha256
- **Symbol**
  - id, snapshot_id, file_id, name, kind (function/class/var/module), range, signature
- **Reference**
  - from_symbol_id, to_symbol_id (nullable), to_file_id (nullable), kind (import/call/usage)
- **EmbeddingChunk**
  - file_id, chunk_id, text_span, embedding_vector
- **AnalysisArtifact**
  - type (dep_graph/call_graph/mermaid), payload, created_at
- **AISession / ChatMessage**
  - session_id, messages with citations to (file, range, symbol)
- **ChangeSet**
  - id, snapshot_id, status (proposed/applied/rolled_back), patches, created_by

### Graphs you will build
- **File dependency graph**: modules/imports edges
- **Symbol graph**: definitions + references/calls
- **Git graph** (phase 2): branches/commits + per-commit index

---

## Architecture (recommended)
### High-level components
- **Frontend (Next.js + TS)**
  - Panels (tree/canvas/editor), auth, project import UI
  - Graph rendering (React Flow / Cytoscape), Mermaid renderer
  - Monaco editor for code + diff viewer

- **Backend API (FastAPI)**
  - Project management (import, snapshots)
  - Query endpoints (search, symbol lookup, references, graphs)
  - AI orchestration (prompting, tool calls, citations)
  - ChangeSet application (patch validation, write, git commit)

- **Indexing / Analysis Worker (Python)**
  - Filesystem scan + ignore rules
  - Language detection
  - Parsers (Tree-sitter / language servers where available)
  - Builds symbol tables + reference edges
  - Embeddings pipeline (chunking + vector insert)

- **Storage**
  - **PostgreSQL** for metadata (projects, files, symbols, references, changes)
  - **pgvector** for embeddings (or a vector DB)
  - **Object storage / disk** for snapshots/artifacts (optional)
  - **Redis** for task queue + job progress (optional but recommended)

### Execution model
- Backend is synchronous for reads + orchestration.
- Heavy work (indexing, embedding, large graph computation) runs async:
  - Task queue: **RQ/Celery** (or FastAPI background tasks for MVP)
  - UI subscribes to progress via **WebSocket/SSE**

### Deployment modes
- **Local-first (developer machine)**: best for privacy; indexes local repos.
- **Server mode**: multi-user; repos uploaded or connected via Git provider.

---

## “Context Engine” Design
### Indexing pipeline (MVP)
1. **Discover files** (gitignore-aware, size limits, binary detection)
2. **Detect language** (by extension + shebang + content heuristics)
3. **Parse AST** (Tree-sitter) and extract:
   - symbols (defs)
   - imports/exports
   - calls (best-effort)
4. **Build graphs**
   - file deps
   - symbol refs (partial in MVP)
5. **Chunk & embed** code and docs
6. Store everything under a **Snapshot** for repeatable queries.

### Query answering strategy
Use a hybrid of:
- **Graph retrieval** (find relevant files/symbols via refs/deps)
- **Vector retrieval** (semantic chunks)
- **Structured lookups** (exact symbol search, path search)

Then generate:
- explanation + “what to read next”
- citations (file path + range)
- optional diagram (Mermaid) derived from graph slice

---

## AI-assisted Modification (Safe Edit Workflow)
### Guardrails (non-negotiable)
- Never write without creating a **ChangeSet**.
- Always show **diff preview** before applying (unless explicitly configured).
- Validate patches against current snapshot (hashes/ranges).
- Maintain rollback (store original file contents or reverse patch).

### Edit flow
1. User request: “Refactor X”, “Add feature Y”
2. AI produces:
   - plan + impacted files
   - patches (unified diff)
   - rationale + risk notes
3. System runs:
   - patch apply in sandbox workspace
   - (optional) formatting / lint / tests
4. User approves → apply to repo
5. (optional) create git commit + update snapshot

---

## API Surface (first cut)
### Projects & snapshots
- `POST /projects/import` (local path or uploaded zip)
- `GET /projects`
- `POST /projects/{id}/snapshots` (kick off indexing)
- `GET /projects/{id}/snapshots/{sid}/status`

### File browsing
- `GET /snapshots/{sid}/tree`
- `GET /snapshots/{sid}/files?path=...`
- `GET /snapshots/{sid}/file-content?path=...`

### Code intelligence
- `GET /snapshots/{sid}/symbols?query=...`
- `GET /snapshots/{sid}/symbols/{symbolId}`
- `GET /snapshots/{sid}/references/{symbolId}`
- `GET /snapshots/{sid}/graphs/deps?path=...`
- `GET /snapshots/{sid}/graphs/calls?symbolId=...`

### AI
- `POST /snapshots/{sid}/chat`
- `POST /snapshots/{sid}/explain` (file/symbol/system)
- `POST /snapshots/{sid}/propose-changes`

### ChangeSets
- `GET /snapshots/{sid}/changesets`
- `GET /changesets/{cid}`
- `POST /changesets/{cid}/apply`
- `POST /changesets/{cid}/rollback`
- `POST /changesets/{cid}/commit` (message)

---

## Visualization Plan
### Graph types
- **Dependency graph**: file/module import edges
- **Call graph**: function/method call edges (best-effort in MVP)
- **Symbol map**: classes/functions per file
- **Git graph** (phase 2): branch/commit DAG + per-commit insights

### Rendering stack
- Graph canvas: **React Flow** (fast to ship) or **Cytoscape** (larger graphs)
- Diagrams: **Mermaid** for “explain this flow” outputs
- Code links: clicking any node opens editor at range

### Performance notes
- Use progressive loading:
  - show “local neighborhood” of a node first
  - fetch expanded edges on demand
- Cap graph size + use clustering (package/module grouping)

---

## Repo Import & Git Integration
### Import modes (MVP)
- Local directory path (desktop app / local agent)
- Upload zip (server mode)

### Git features (Phase 2)
- Branch list + branch graph
- Commit-aware snapshots
- Compare snapshots (diff + graph delta)
- “Impact of commit” summary

---

## Security & Privacy (practical)
- **Sandbox file access**: only within project root; no `..` traversal
- **Secret redaction** (optional): detect keys/tokens in text sent to LLM
- **Read-only mode** for sensitive repos (disable ChangeSets)
- **Audit log**: who asked AI to change what + when + what was applied

---

## Tech Stack (aligned to your screenshot tags)
- **Next.js + TypeScript + TailwindCSS**: core UI
- **FastAPI**: API + auth + orchestrator
- **Python analysis engine**: Tree-sitter parsing, indexing, embedding
- **Mermaid**: diagram output
- **PeerJS**: optional real-time collaboration (Phase 3)
- **Gemini 1.5 Flash (or equivalent)**: fast reasoning + summarization

---

## Phased Roadmap (deliverable-driven)
### Phase 1 — MVP (single user, local-first)
- Import local repo + build snapshot index
- File tree + code viewer/editor (read-only)
- Basic search (path + symbol name + text)
- Dependency graph (imports) + click-to-open
- Chat with retrieval (vector + graph) + citations to files/ranges

**Exit criteria**
- Can answer “How does this project work?” with correct pointers
- Can visualize deps for a selected file/module

### Phase 2 — Safe edits + Git awareness
- ChangeSet diff viewer + apply/rollback
- Multi-file edits (rename symbol, move file, refactor module)
- Git integration: commit changes + snapshot per commit
- “Impact analysis” (affected dependents, key call sites)

**Exit criteria**
- Can propose and safely apply a multi-file refactor with rollback

### Phase 3 — Collaboration + scale
- Multi-user projects (auth/roles)
- Shared sessions + presence (PeerJS/WebRTC or WebSocket)
- Large-repo optimizations (incremental indexing, caching, sharding graphs)
- Enterprise controls (RBAC, audit exports)

---

## MVP Implementation Notes (so it’s feasible)
- Prefer **Tree-sitter** for multi-language parsing (ship fast).
- For call graphs, start with:
  - Python: `ast` + imports + simple name resolution
  - TS/JS: TypeScript compiler API or tree-sitter + heuristic resolution
- Treat “perfect static analysis” as a Phase 2/3 refinement; MVP should be **useful with partial graphs**.

---

## Minimal Database Schema (Postgres)
### Tables (suggested)
- `projects(id, name, created_at, settings_json)`
- `snapshots(id, project_id, git_commit, created_at, status, index_version)`
- `files(id, snapshot_id, path, language, size_bytes, sha256, is_binary)`
- `symbols(id, snapshot_id, file_id, name, kind, start_line, start_col, end_line, end_col, signature, docstring)`
- `references(id, snapshot_id, from_symbol_id, to_symbol_id, to_file_id, kind)`
- `embedding_chunks(id, snapshot_id, file_id, chunk_index, start_line, end_line, text, embedding vector)`
- `analysis_artifacts(id, snapshot_id, type, scope, payload_json, created_at)`
- `ai_sessions(id, snapshot_id, created_at)`
- `ai_messages(id, session_id, role, content, created_at, citations_json)`
- `changesets(id, snapshot_id, status, title, rationale, patches_json, created_at, applied_at)`

### Indexes to add early
- `files(snapshot_id, path)`
- `symbols(snapshot_id, name)`
- `references(snapshot_id, from_symbol_id)`
- `references(snapshot_id, to_symbol_id)`
- `embedding_chunks` vector index (pgvector IVF/HNSW, depending on scale)

---

## Background Jobs & Progress
### Jobs
- **IndexSnapshotJob**
  - Input: `project_id`, optional `git_commit`
  - Output: `snapshot_id` + progress events
  - Steps: scan → parse → graph → embed → finalize

### Progress transport (MVP)
- **Server-Sent Events (SSE)**: easy to ship, one-way updates
- WebSocket later if you need bi-directional collaboration features

---

## Screens (MVP)
- **Project Import**
  - choose local directory (local-first) or upload zip (server mode)
  - start indexing, show progress
- **Workspace (3-pane)**
  - left: file tree + search
  - center: chat tab + graph tab
  - right: code view (read-only for MVP)
- **Graph Viewer**
  - dependency graph for current file/module
  - click node → open file
- **Symbol Search**
  - quick palette to jump to defs/references

---

## Acceptance Criteria (MVP)
- Ingest a small repo (<2k files) and finish indexing successfully.
- File tree reflects ignore rules and opens files instantly from snapshot.
- “Explain this repo” produces:
  - architecture summary
  - key entrypoints
  - at least 3 cited file/range references
- Dependency graph renders for a selected module and supports click-to-open.
- Symbol search returns correct definitions for common cases.

## Success Metrics
- **Time-to-first-insight**: repo import → first useful answer < 2 minutes (small repo)
- **Answer quality**: % responses with correct file pointers
- **Edit safety**: no silent writes; rollback always works
- **Adoption**: returning users + repeated project opens

---

## 🎯 Change Impact Analysis — 5-Day Implementation Sprint

### Overview
**Feature**: "If I modify this function, what breaks?"

This is a **core differentiator** that demonstrates:
- Graph data structures (symbol reference graph)
- BFS/DFS traversal algorithms
- Static analysis thinking
- Risk modeling and scoring
- Large codebase understanding

---

### Day 1: Reference Graph Data Layer & BFS Traversal Core
**Goal**: Build the foundational graph traversal engine that powers impact analysis

**Tasks**:
1. **Enhance the Symbol Reference Model**
   - Ensure `Reference` table captures `from_symbol_id`, `to_symbol_id`, `kind` (call/import/usage/extends)
   - Add reference `context` field (line snippet where reference occurs)
   - Index optimization: composite index on `(snapshot_id, to_symbol_id)` for fast reverse lookups

2. **Implement BFS Traversal Engine** (`impact_analyzer.py`)
   - Build `_trace_impact()` method with configurable `max_depth`
   - Track visited nodes to prevent cycles
   - Classify impact as "direct" (distance=1) or "transitive" (distance>1)
   - Return both impacted symbols AND the path taken to reach them

3. **Add Impact Scoring Algorithm**
   - `_calculate_risk()` method with weighted scoring:
     - Number of files affected (weight: high)
     - Number of symbols affected (weight: medium)
     - Depth of impact chain (weight: low)
     - Symbol kind weights (class > function > variable)
   - Risk levels: `low`, `medium`, `high`, `critical`

**Deliverables**:
- [ ] Updated `Reference` model with context field
- [ ] BFS traversal with cycle detection
- [ ] Risk scoring algorithm
- [ ] Unit tests for graph traversal

**Technical Notes**:
```python
# Core algorithm pseudocode
def trace_impact(start_symbols, max_depth=3):
    visited = set(start_symbols)
    queue = [(sym, 0) for sym in start_symbols]  # (symbol, distance)
    impacted = []
    
    while queue:
        current, distance = queue.pop(0)  # BFS
        if distance > max_depth:
            continue
        
        for ref in get_references_to(current):
            if ref.from_symbol not in visited:
                visited.add(ref.from_symbol)
                impacted.append((ref.from_symbol, distance + 1))
                queue.append((ref.from_symbol, distance + 1))
    
    return impacted
```

---

### Day 2: Impact Analysis API Endpoints
**Goal**: Expose impact analysis through REST API

**Tasks**:
1. **Create `/api/impact` Router** (`backend/app/api/impact.py`)
   - `POST /snapshots/{sid}/impact/analyze-file`
     - Input: `{ file_paths: string[] }`
     - Output: Full `ImpactAnalysis` response
   
   - `POST /snapshots/{sid}/impact/analyze-symbol`
     - Input: `{ symbol_ids: string[] }`
     - Output: Full `ImpactAnalysis` response
   
   - `GET /snapshots/{sid}/impact/preview`
     - Query params: `path`, `line` (for quick hover impact check)
     - Output: Lightweight impact summary

2. **Response Schema Design**
   ```typescript
   interface ImpactAnalysis {
     changedFiles: string[];
     changedSymbols: ImpactedSymbol[];
     impactedFiles: ImpactedFile[];
     impactedSymbols: ImpactedSymbol[];
     totalFilesAffected: number;
     totalSymbolsAffected: number;
     riskLevel: "low" | "medium" | "high" | "critical";
     riskExplanation: string;
     impactGraph: ImpactGraphData;  // For visualization
   }
   
   interface ImpactedSymbol {
     id: string;
     name: string;
     kind: string;
     filePath: string;
     startLine: number;
     endLine: number;
     impactType: "direct" | "transitive";
     distance: number;
     referenceContext?: string;  // The line where it references
   }
   
   interface ImpactGraphData {
     nodes: GraphNode[];
     edges: GraphEdge[];
   }
   ```

3. **Add API Tests**
   - Test with mock symbol graph
   - Test edge cases (orphan symbols, circular deps)

**Deliverables**:
- [ ] `/api/impact.py` router with 3 endpoints
- [ ] Pydantic schemas for request/response
- [ ] Integration tests

---

### Day 3: Impact Graph Visualization Component
**Goal**: Build interactive impact visualization in the frontend

**Tasks**:
1. **Create `ImpactGraphViewer` Component** (`frontend/src/components/ImpactGraphViewer.tsx`)
   - Use React Flow for graph rendering
   - Node types:
     - 🔴 **Changed** (red) - the modified symbol
     - 🟠 **Direct impact** (orange) - distance=1
     - 🟡 **Transitive impact** (yellow) - distance>1
   - Edge styling based on reference kind (solid for calls, dashed for imports)
   - Animated edges showing "ripple effect" from changed node

2. **Layout Algorithm**
   - Hierarchical layout: changed symbol at top, impacted symbols flow down
   - Group nodes by file (collapsible file containers)
   - Support zoom/pan for large graphs

3. **Interactivity**
   - Click node → open file in editor at symbol location
   - Hover node → show full signature + docstring
   - Click edge → highlight the reference line in code

**Deliverables**:
- [ ] `ImpactGraphViewer.tsx` component
- [ ] Node/edge type definitions
- [ ] Click-to-navigate integration with editor

**Visual Design**:
```
         ┌─────────────────┐
         │ 🔴 getUserById  │  ← Changed
         │   user.ts:45    │
         └────────┬────────┘
                  │ calls
        ┌─────────┴─────────┐
        ▼                   ▼
┌──────────────┐    ┌──────────────┐
│ 🟠 AuthMiddle│    │ 🟠 UserAPI   │  ← Direct
│  auth.ts:23  │    │  api.ts:89   │
└──────┬───────┘    └──────────────┘
       │ calls
       ▼
┌──────────────┐
│ 🟡 LoginFlow │  ← Transitive
│  login.tsx:12│
└──────────────┘
```

---

### Day 4: UI Integration & Impact Panel
**Goal**: Integrate impact analysis into the main workspace UX

**Tasks**:
1. **Add "Analyze Impact" Action to Editor**
   - Right-click context menu: "Analyze Impact of This Function"
   - Keyboard shortcut: `Ctrl+Shift+I`
   - Gutter icon on function/class definitions

2. **Create `ImpactPanel` Component** (`frontend/src/components/ImpactPanel.tsx`)
   - Slide-out panel or modal showing:
     - **Risk Badge**: Large colored badge (🟢🟡🟠🔴)
     - **Summary Stats**: X files, Y symbols affected
     - **Risk Explanation**: Human-readable text
     - **Impacted Files List**: Collapsible tree
     - **Graph Toggle**: Switch to visual graph view
   
3. **Real-time Impact Preview**
   - As user types in editor, debounced impact check
   - Subtle indicator in status bar: "⚠️ 12 dependents"
   - Click to expand full analysis

4. **Integration with ChangeSet Workflow**
   - Before applying a ChangeSet, auto-run impact analysis
   - Block high-risk changes with confirmation dialog
   - Include impact summary in commit message (optional)

**Deliverables**:
- [ ] Context menu integration
- [ ] `ImpactPanel.tsx` component
- [ ] Real-time impact indicator
- [ ] ChangeSet pre-apply hook

---

### Day 5: Polish, Testing & Demo Scenarios
**Goal**: Harden the feature and create impressive demo scenarios

**Tasks**:
1. **Performance Optimization**
   - Cache impact analysis results per snapshot+symbol
   - Lazy load deep transitive impacts (fetch on expand)
   - Add loading states and progress indicators

2. **Edge Case Handling**
   - Symbols with 100+ dependents: show "heavily used" warning
   - Circular dependencies: detect and visualize cycles
   - External/unresolved references: show as "unknown impact"

3. **Create Demo Scenarios**
   - **Scenario A**: Rename a utility function → show cascading impact
   - **Scenario B**: Modify a class interface → highlight all implementations
   - **Scenario C**: Delete an export → show breaking imports

4. **Add AI Enhancement** (bonus)
   - "Explain this impact" button → AI summarizes what breaks and why
   - Suggest safest refactoring approach based on impact graph

5. **Documentation & Recording**
   - Record demo video showing impact analysis in action
   - Write user guide section

**Deliverables**:
- [ ] Cached impact analysis
- [ ] Edge case handling
- [ ] 3 demo scenarios tested
- [ ] (Bonus) AI impact explanation
- [ ] Demo video/screenshots

---

### Technical Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│  ┌──────────────┐  ┌───────────────────┐  ┌──────────────────┐ │
│  │ CodeEditor   │  │ ImpactPanel       │  │ ImpactGraphViewer│ │
│  │ (Monaco)     │──│ - Risk Badge      │──│ (React Flow)     │ │
│  │ - Gutter     │  │ - File List       │  │ - Nodes/Edges    │ │
│  │ - Context    │  │ - Stats           │  │ - Click-to-nav   │ │
│  └──────────────┘  └───────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │ API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND                                  │
│  ┌──────────────┐  ┌───────────────────┐  ┌──────────────────┐ │
│  │ /api/impact  │  │ ImpactAnalyzer    │  │ Reference Graph  │ │
│  │ - analyze-   │──│ - BFS traversal   │──│ (PostgreSQL)     │ │
│  │   file       │  │ - Risk scoring    │  │ - symbols        │ │
│  │ - analyze-   │  │ - Path tracking   │  │ - references     │ │
│  │   symbol     │  │                   │  │                  │ │
│  └──────────────┘  └───────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

### Day 1 Checklist (Start Today!)

- [ ] Review existing `impact_analyzer.py` implementation
- [ ] Add `context` field to `Reference` model
- [ ] Implement path tracking in `_trace_impact()`
- [ ] Write unit tests for BFS traversal
- [ ] Test with a real codebase (this project!)

**Time estimate**: 4-6 hours
