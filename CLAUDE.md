# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Watch Party is a real-time collaborative browsing platform where users watch content together through a shared browser session. Features include remote control handoff, text chat, and voice communication. Think "Hyperbeam for watch parties" - a browser-in-browser experience.

**Current State:** Architecture and planning phase. Directory structure created with empty placeholder files. No implementation code yet.

## Tech Stack

- **Backend:** FastAPI (Python 3.11+), PostgreSQL, Redis, Playwright (headless browser)
- **Frontend:** React + Vite, Tailwind CSS + shadcn/ui, Zustand (state management)
- **Real-time:** Native FastAPI WebSockets, WebRTC (simple-peer for voice/video)
- **No Docker for MVP:** Uses local PostgreSQL and Redis installations

## Common Commands

### Backend

```bash
# Setup (first time)
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements/dev.txt
playwright install chromium
cp .env.example .env

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload

# Run tests
pytest
pytest -v --cov

# Create new migration
alembic revision --autogenerate -m "description"
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Start dev server (port 5173)
npm run build    # Production build
npm run lint     # ESLint
npm run format   # Prettier
```

### Database Setup (Local PostgreSQL)

```sql
CREATE DATABASE watchparty_dev;
CREATE USER watchparty WITH PASSWORD 'watchparty_dev';
GRANT ALL PRIVILEGES ON DATABASE watchparty_dev TO watchparty;
```

## Architecture

### Backend Structure

```
backend/app/
├── main.py              # FastAPI entry point
├── core/                # Config, security, dependencies
├── api/v1/endpoints/    # REST endpoints (auth, users, rooms, health)
├── websocket/           # WebSocket handlers (chat, control, signaling)
├── browser/             # Playwright automation (manager, controller, streamer)
├── services/            # Business logic layer
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── db/                  # Database session and utilities
├── cache/               # Redis operations
└── tests/               # pytest tests
```

### Frontend Structure

```
frontend/src/
├── pages/               # Route pages (Landing, Login, Dashboard, Room)
├── features/            # Feature modules (auth, room, browser, chat, voice)
│   └── {feature}/
│       ├── components/
│       ├── hooks/
│       ├── services/
│       └── store/       # Zustand stores
├── components/          # Shared UI components (ui/, layout/, common/)
├── services/            # API client, WebSocket, storage
└── hooks/               # Global hooks
```

### Key Data Flow

1. **REST API:** Authentication, room CRUD, user management
2. **WebSocket:** Chat messages, room events, control handoff
3. **WebRTC Data Channel:** Mouse/keyboard events (low latency)
4. **WebRTC Media:** Browser screen stream (Playwright → participants), voice P2P mesh

### Database Models

- `users` - User accounts
- `rooms` - Room metadata (host_id, room_code, max 6 participants)
- `room_participants` - User-room associations
- `messages` - Chat history
- `remote_session` - Remote control state

## Key Constraints

- **Max 6 participants per room** (P2P mesh network limit)
- **4-hour room timeout** after inactivity
- **Desktop-first** (no mobile support for MVP)
- **Single tab per browser session** (no multi-tab for MVP)
- **Host leaves = room closes**

## Environment Variables

Backend requires `.env` with:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT signing key

Frontend requires `.env` with:
- `VITE_API_URL` - Backend URL (default: http://localhost:8000)
- `VITE_WS_URL` - WebSocket URL (default: ws://localhost:8000)
