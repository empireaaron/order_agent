# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

TicketBot is a smart customer service ticket system with three main components:

1. **Backend** (`backend/`) - FastAPI with LangChain/LangGraph AI agents
2. **Frontend Admin** (`frontend-admin/`) - React + TypeScript + Ant Design for agents/admins
3. **Widget** (`widget/`) - Vanilla JS embeddable chat widget for customers

### AI Agent Workflow (LangGraph)

The AI agent (`backend/agents/`) processes user input through intent analysis:

```
User Input → analyze_intent → Route to:
  ├─ create_ticket → MySQL insert
  ├─ query_ticket → MySQL query
  ├─ process_ticket → Update ticket status
  ├─ transfer_to_agent → Create chat session
  ├─ summary → Statistics query
  └─ general → query_knowledge (Milvus) → Return results
```

### Real-time Chat System

WebSocket dual endpoints:
- `/ws` - General notifications (system broadcasts)
- `/ws/chat` - Real-time chat messages (customers ↔ agents)

Transfer to human flow:
1. Customer clicks "转人工" in Widget or AI routes to transfer
2. API creates chat session (`backend/api/v1/chat_service.py`)
3. If agents online: auto-assign or queue
4. WebSocket connection established for real-time messaging
5. Agent uses "Chat Workplace" (`frontend-admin/src/pages/ChatWorkplace/`) to handle sessions

### Key Directories

- `backend/agents/` - LangGraph nodes and state
- `backend/api/v1/` - REST API routes
- `backend/models/` - SQLAlchemy models (user, ticket, knowledge_base, chat)
- `backend/websocket/` - WebSocket managers (general + chat)
- `frontend-admin/src/stores/` - Zustand state management
- `frontend-admin/src/services/` - API client
- `widget/ticket-widget.js` - Embeddable widget (~1000 lines, Shadow DOM)

## Common Commands

```bash
# Initialize database
python manage.py init-db

# Start backend (port 8000 via manage.py, but use 8001 for uvicorn directly)
python manage.py run-backend
# OR: cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Start frontend (port 5173)
python manage.py run-frontend
# OR: cd frontend-admin && npm run dev

# Frontend linting
cd frontend-admin && npm run lint

# Docker dependencies (MySQL, Milvus, MinIO)
docker-compose up -d mysql milvus minio

# All services via Docker
docker-compose up -d
```

## Port Configuration

| Service | Port | Notes |
|---------|------|-------|
| Backend | 8001 | API + WebSocket |
| Frontend | 5173 | Vite dev server |
| MySQL | 3306 | |
| Milvus | 19530 | Vector DB for knowledge search |
| MinIO API | 9000 | File storage |
| MinIO Console | 9001 | |

## Key Concepts

**Multi-role RBAC**: JWT tokens with roles (admin, agent, operations, user). Check `backend/auth/dependencies.py` for `require_role()`.

**Knowledge Base**: Documents uploaded to MinIO, parsed into chunks, embedded via OpenAI/DashScope, stored in Milvus for semantic search.

**Widget Session Persistence**: Widget stores `session_id` and `token` in localStorage for automatic reconnection on page refresh.

**Agent Status**: Agents toggle online/offline via `POST /api/v1/agent/online`. Only online agents receive new session assignments.

## VS Code Debugging

Press `F5` and select "Run Backend" or "Run Frontend". Configurations are in `.vscode/launch.json`.

## Python Path

The backend uses `PYTHONPATH=./backend`. `manage.py` automatically adds this, or VS Code launch configurations handle it.