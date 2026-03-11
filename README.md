# WatchParty

A real-time watch-party platform for shared media experiences across distance.

## Overview

I love watching media with people I care about - movies, YouTube videos, and more. Distance makes that hard, so I built **WatchParty** to recreate the feeling of watching together while staying in sync inside the same session.

WatchParty is a full-stack project centered on synchronized rooms, real-time communication, shared controls, and collaborative viewing.

## Why I Built It

Sometimes sending a link and saying "press play now" is not enough.

I wanted to build shared watch sessions where people can join one room, communicate in real time, and stay coordinated while consuming media from different locations. This project helped me explore the backend challenges behind that experience: room state, participant coordination, websocket events, session control, and synchronization.

## Core Features

- User authentication (signup/login + protected routes)
- Room lifecycle (create, join, participant management)
- Real-time communication (WebSocket events + live chat)
- Session coordination (shared state + synchronized controls)
- Signaling flows for multi-user interactions
- Caching layer for active room/session state
- Browser/session orchestration modules for collaborative playback workflows
- Automated tests for auth, rooms, browser/session logic, and websockets

## Technical Highlights

1. Dedicated real-time backend layer for chat, control, and signaling events.
2. Structured service layer (`auth`, `room`, `chat`, `remote/session`) to keep business logic maintainable.
3. Domain modeling around collaborative entities (`users`, `rooms`, `participants`, `messages`, `remote_sessions`).
4. Cache utilities to speed up room/session reads during live interactions.
5. Browser/session orchestration that moves beyond a basic CRUD API.

## Backend Architecture

```text
backend/
|-- app/
|   |-- api/v1/endpoints/
|   |   |-- auth.py
|   |   |-- health.py
|   |   |-- rooms.py
|   |   `-- users.py
|   |-- browser/
|   |   |-- audio.py
|   |   |-- controller.py
|   |   |-- manager.py
|   |   |-- session.py
|   |   `-- streamer.py
|   |-- cache/
|   |   |-- client.py
|   |   |-- keys.py
|   |   |-- room_cache.py
|   |   `-- session_cace.py
|   |-- core/
|   |-- db/
|   |-- models/
|   |-- schemas/
|   |-- services/
|   |-- websocket/
|   |   |-- events.py
|   |   |-- manager.py
|   |   |-- routes.py
|   |   `-- handlers/
|   `-- tests/
|-- alembic/
|-- requirements.txt
`-- test_websocket.py
```

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- WebSockets
- Pydantic
- Redis caching for room/session state

### Frontend

- TypeScript (see `frontend/`)

### Database

- Relational database with Alembic migrations

## API + Realtime Capabilities

- Authentication endpoints
- User endpoints
- Room endpoints
- Health checks
- WebSocket routes for persistent real-time session communication

## How to Start the Project

### 1. Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL (local)
- Redis (local)
- FFmpeg (optional, required for browser audio streaming)

### 2. Start backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
Copy-Item .env.example .env
```

Create database (if needed):

```sql
CREATE DATABASE watchparty_dev;
CREATE USER watchparty WITH PASSWORD 'watchparty_dev';
GRANT ALL PRIVILEGES ON DATABASE watchparty_dev TO watchparty;
```

Run migrations and start API server:

```powershell
cd backend
alembic upgrade head
uvicorn app.main:app --reload
```

Backend: `http://localhost:8000`

### 3. Start frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

### 4. Optional frontend environment file

Create `frontend/.env` only if you want to override defaults:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```