# Watch Party Platform - Project Structure (Without Docker)

## Root Directory Structure

```
watch-party/
├── backend/                    # FastAPI application
├── frontend/                   # React application
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── .github/                    # GitHub Actions (CI/CD)
├── .env.example                # Environment variables template
├── .gitignore
├── README.md
└── Makefile                    # Common commands (optional)
```

---

## Backend Structure (FastAPI)

```
backend/
├── alembic/                           # Database migrations
│   ├── versions/                      # Migration files
│   ├── env.py
│   └── alembic.ini
│
├── app/
│   ├── __init__.py
│   │
│   ├── main.py                        # FastAPI app entry point
│   │
│   ├── core/                          # Core configurations
│   │   ├── __init__.py
│   │   ├── config.py                  # Settings (Pydantic BaseSettings)
│   │   ├── security.py                # JWT, password hashing
│   │   ├── dependencies.py            # Common dependencies
│   │   └── exceptions.py              # Custom exceptions
│   │
│   ├── api/                           # API routes
│   │   ├── __init__.py
│   │   ├── deps.py                    # Route dependencies
│   │   │
│   │   └── v1/                        # API version 1
│   │       ├── __init__.py
│   │       ├── router.py              # Main router aggregator
│   │       │
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py            # Login, register, logout
│   │           ├── users.py           # User management
│   │           ├── rooms.py           # Room CRUD operations
│   │           └── health.py          # Health check endpoint
│   │
│   ├── websocket/                     # WebSocket handling
│   │   ├── __init__.py
│   │   ├── manager.py                 # WebSocket connection manager
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py                # Chat message handlers
│   │   │   ├── control.py             # Remote control handlers
│   │   │   └── signaling.py           # WebRTC signaling
│   │   │
│   │   └── events.py                  # WebSocket event schemas
│   │
│   ├── browser/                       # Browser automation
│   │   ├── __init__.py
│   │   ├── manager.py                 # Browser instance manager
│   │   ├── controller.py              # Browser control logic
│   │   ├── streamer.py                # Screen streaming via WebRTC
│   │   └── session.py                 # Browser session lifecycle
│   │
│   ├── services/                      # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py            # Authentication logic
│   │   ├── room_service.py            # Room management logic
│   │   ├── user_service.py            # User operations
│   │   ├── chat_service.py            # Chat operations
│   │   └── remote_control_service.py  # Remote control logic
│   │
│   ├── models/                        # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py                    # Base model class
│   │   ├── user.py                    # User model
│   │   ├── room.py                    # Room model
│   │   ├── room_participant.py        # Room participant model
│   │   ├── message.py                 # Chat message model
│   │   └── remote_session.py          # Remote control session
│   │
│   ├── schemas/                       # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py                    # User request/response schemas
│   │   ├── room.py                    # Room request/response schemas
│   │   ├── message.py                 # Message schemas
│   │   ├── auth.py                    # Auth schemas (login, token)
│   │   └── websocket.py               # WebSocket message schemas
│   │
│   ├── db/                            # Database utilities
│   │   ├── __init__.py
│   │   ├── session.py                 # Database session management
│   │   ├── base.py                    # Import all models (for Alembic)
│   │   └── init_db.py                 # Initial data seeding
│   │
│   ├── cache/                         # Redis operations
│   │   ├── __init__.py
│   │   ├── client.py                  # Redis client setup
│   │   ├── room_cache.py              # Room state caching
│   │   ├── session_cache.py           # User session caching
│   │   └── keys.py                    # Cache key generators
│   │
│   ├── utils/                         # Utility functions
│   │   ├── __init__.py
│   │   ├── validators.py              # Custom validators
│   │   ├── generators.py              # ID/code generators
│   │   ├── logger.py                  # Logging configuration
│   │   └── decorators.py              # Custom decorators
│   │
│   └── tests/                         # Test files
│       ├── __init__.py
│       ├── conftest.py                # Pytest fixtures
│       ├── test_auth.py
│       ├── test_rooms.py
│       ├── test_websocket.py
│       └── test_browser.py
│
├── requirements/
│   ├── base.txt                       # Core dependencies
│   ├── dev.txt                        # Development dependencies
│   └── prod.txt                       # Production dependencies
│
├── .env.example
├── .env.test
├── Dockerfile
├── pyproject.toml                     # Python project config
├── pytest.ini
└── README.md
```

---

## Frontend Structure (React + Vite)

```
frontend/
├── public/
│   ├── favicon.ico
│   └── robots.txt
│
├── src/
│   ├── main.jsx                       # App entry point
│   ├── App.jsx                        # Root component
│   │
│   ├── assets/                        # Static assets
│   │   ├── images/
│   │   ├── icons/
│   │   └── styles/
│   │       └── global.css             # Global styles
│   │
│   ├── components/                    # Reusable components
│   │   ├── ui/                        # shadcn/ui components
│   │   │   ├── button.jsx
│   │   │   ├── input.jsx
│   │   │   ├── dialog.jsx
│   │   │   ├── avatar.jsx
│   │   │   └── ...
│   │   │
│   │   ├── layout/                    # Layout components
│   │   │   ├── Header.jsx
│   │   │   ├── Footer.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── MainLayout.jsx
│   │   │
│   │   └── common/                    # Common components
│   │       ├── Loading.jsx
│   │       ├── ErrorBoundary.jsx
│   │       ├── ProtectedRoute.jsx
│   │       └── Toast.jsx
│   │
│   ├── features/                      # Feature-based modules
│   │   │
│   │   ├── auth/                      # Authentication feature
│   │   │   ├── components/
│   │   │   │   ├── LoginForm.jsx
│   │   │   │   ├── RegisterForm.jsx
│   │   │   │   └── PasswordReset.jsx
│   │   │   ├── hooks/
│   │   │   │   ├── useAuth.js
│   │   │   │   └── useLogin.js
│   │   │   ├── services/
│   │   │   │   └── authService.js
│   │   │   └── store/
│   │   │       └── authStore.js       # Zustand store
│   │   │
│   │   ├── room/                      # Room feature
│   │   │   ├── components/
│   │   │   │   ├── RoomList.jsx
│   │   │   │   ├── CreateRoomModal.jsx
│   │   │   │   ├── JoinRoomModal.jsx
│   │   │   │   ├── RoomCard.jsx
│   │   │   │   └── ShareRoomLink.jsx
│   │   │   ├── hooks/
│   │   │   │   ├── useRoom.js
│   │   │   │   └── useRoomParticipants.js
│   │   │   ├── services/
│   │   │   │   └── roomService.js
│   │   │   └── store/
│   │   │       └── roomStore.js
│   │   │
│   │   ├── browser/                   # Browser viewing feature
│   │   │   ├── components/
│   │   │   │   ├── BrowserViewport.jsx
│   │   │   │   ├── BrowserControls.jsx
│   │   │   │   ├── URLBar.jsx
│   │   │   │   └── StreamDisplay.jsx
│   │   │   ├── hooks/
│   │   │   │   ├── useBrowserStream.js
│   │   │   │   └── useRemoteControl.js
│   │   │   ├── services/
│   │   │   │   └── browserService.js
│   │   │   └── store/
│   │   │       └── browserStore.js
│   │   │
│   │   ├── chat/                      # Chat feature
│   │   │   ├── components/
│   │   │   │   ├── ChatPanel.jsx
│   │   │   │   ├── ChatMessage.jsx
│   │   │   │   ├── ChatInput.jsx
│   │   │   │   └── TypingIndicator.jsx
│   │   │   ├── hooks/
│   │   │   │   ├── useChat.js
│   │   │   │   └── useChatMessages.js
│   │   │   ├── services/
│   │   │   │   └── chatService.js
│   │   │   └── store/
│   │   │       └── chatStore.js
│   │   │
│   │   ├── voice/                     # Voice chat feature
│   │   │   ├── components/
│   │   │   │   ├── VoiceControls.jsx
│   │   │   │   ├── ParticipantAudio.jsx
│   │   │   │   ├── MuteButton.jsx
│   │   │   │   └── VolumeControl.jsx
│   │   │   ├── hooks/
│   │   │   │   ├── useVoiceChat.js
│   │   │   │   ├── useWebRTC.js
│   │   │   │   └── useAudioStream.js
│   │   │   ├── services/
│   │   │   │   ├── webrtcService.js
│   │   │   │   └── voiceService.js
│   │   │   └── store/
│   │   │       └── voiceStore.js
│   │   │
│   │   ├── participants/              # Participants feature
│   │   │   ├── components/
│   │   │   │   ├── ParticipantList.jsx
│   │   │   │   ├── ParticipantItem.jsx
│   │   │   │   ├── RemoteControlBadge.jsx
│   │   │   │   └── PassRemoteMenu.jsx
│   │   │   ├── hooks/
│   │   │   │   └── useParticipants.js
│   │   │   └── store/
│   │   │       └── participantsStore.js
│   │   │
│   │   └── dashboard/                 # Dashboard feature
│   │       ├── components/
│   │       │   ├── DashboardHome.jsx
│   │       │   ├── QuickActions.jsx
│   │       │   └── RecentRooms.jsx
│   │       └── hooks/
│   │           └── useDashboard.js
│   │
│   ├── pages/                         # Page components
│   │   ├── LandingPage.jsx
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   ├── DashboardPage.jsx
│   │   ├── RoomPage.jsx
│   │   ├── NotFoundPage.jsx
│   │   └── ErrorPage.jsx
│   │
│   ├── hooks/                         # Global hooks
│   │   ├── useWebSocket.js
│   │   ├── useLocalStorage.js
│   │   └── useDebounce.js
│   │
│   ├── services/                      # API services
│   │   ├── api.js                     # Axios instance
│   │   ├── websocket.js               # WebSocket client
│   │   └── storage.js                 # LocalStorage wrapper
│   │
│   ├── store/                         # Global state (Zustand)
│   │   ├── index.js                   # Store aggregator
│   │   └── appStore.js                # Global app state
│   │
│   ├── utils/                         # Utility functions
│   │   ├── constants.js               # App constants
│   │   ├── helpers.js                 # Helper functions
│   │   ├── validators.js              # Form validators
│   │   └── formatters.js              # Data formatters
│   │
│   ├── lib/                           # Third-party configs
│   │   └── cn.js                      # Tailwind class merger
│   │
│   ├── types/                         # TypeScript types (if using TS)
│   │   ├── auth.ts
│   │   ├── room.ts
│   │   └── websocket.ts
│   │
│   └── router/                        # Routing configuration
│       ├── index.jsx                  # Router setup
│       └── routes.jsx                 # Route definitions
│
├── .env.example
├── .env.development
├── .env.production
├── .eslintrc.json
├── .prettierrc
├── components.json                    # shadcn/ui config
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── vite.config.js
└── README.md
```

---

## Local Development Setup

### Prerequisites Installation

#### 1. PostgreSQL (Local)
**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
Download installer from [postgresql.org](https://www.postgresql.org/download/windows/)

#### 2. Redis (Local)
**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Windows:**
Download from [redis.io](https://redis.io/download) or use WSL

#### 3. Node.js & npm
**All platforms:**
Install from [nodejs.org](https://nodejs.org/) (LTS version 20.x recommended)

Or use nvm:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20
```

#### 4. Python 3.11+
**macOS:**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt install python3.11 python3.11-venv python3-pip
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

### Database Setup

```bash
# Create PostgreSQL database and user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE watchparty_dev;
CREATE USER watchparty WITH PASSWORD 'watchparty_dev';
GRANT ALL PRIVILEGES ON DATABASE watchparty_dev TO watchparty;
\q

# Test connection
psql -U watchparty -d watchparty_dev -h localhost
```

### Redis Setup

```bash
# Test Redis is running
redis-cli ping
# Should return: PONG
```

---

## Key Configuration Files

### `backend/app/core/config.py`
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Watch Party"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    
    # Room Settings
    MAX_ROOM_PARTICIPANTS: int = 6
    ROOM_TIMEOUT_HOURS: int = 4
    
    # WebRTC
    STUN_SERVERS: list[str] = ["stun:stun.l.google.com:19302"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### `backend/app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.websocket.manager import websocket_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(websocket_router)

@app.get("/")
async def root():
    return {"message": "Watch Party API", "version": settings.VERSION}
```

### `frontend/src/services/api.js`
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          `${import.meta.env.VITE_API_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken }
        );
        
        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

---

## Makefile (Common Commands - Optional)

```makefile
.PHONY: help setup dev-backend dev-frontend test migrate clean install-deps

help:
	@echo "Available commands:"
	@echo "  make install-deps  - Install all dependencies"
	@echo "  make setup         - Initial project setup"
	@echo "  make dev-backend   - Start backend server"
	@echo "  make dev-frontend  - Start frontend dev server"
	@echo "  make test          - Run backend tests"
	@echo "  make migrate       - Run database migrations"
	@echo "  make clean         - Clean build artifacts"

install-deps:
	@echo "Installing backend dependencies..."
	cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements/dev.txt && playwright install chromium
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Dependencies installed!"

setup:
	@echo "Setting up project..."
	cp backend/.env.example backend/.env
	cp frontend/.env.example frontend/.env
	@echo "Creating database..."
	createdb watchparty_dev -U postgres || echo "Database might already exist"
	cd backend && source .venv/bin/activate && alembic upgrade head
	@echo "Setup complete!"

dev-backend:
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && source .venv/bin/activate && pytest

migrate:
	cd backend && source .venv/bin/activate && alembic revision --autogenerate -m "$(msg)"
	cd backend && source .venv/bin/activate && alembic upgrade head

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/.pytest_cache
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.vite
```

**Note for Windows users:** Replace `source .venv/bin/activate` with `.venv\Scripts\activate`

---

## Environment Variables

### `backend/.env.example`
```env
# App
ENVIRONMENT=development
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database
DATABASE_URL=postgresql://watchparty:watchparty_dev@localhost:5432/watchparty_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Room Settings
MAX_ROOM_PARTICIPANTS=6
ROOM_TIMEOUT_HOURS=4

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173"]
```

### `frontend/.env.example`
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_NAME=Watch Party
```

---

## Scripts Directory

### `scripts/init_db.sh`
```bash
#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done

echo "PostgreSQL started"

echo "Running migrations..."
alembic upgrade head

echo "Database initialized!"
```

### `scripts/create_admin.py`
```python
#!/usr/bin/env python
import asyncio
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def create_admin():
    db = SessionLocal()
    try:
        admin = User(
            email="admin@watchparty.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            is_superuser=True
        )
        db.add(admin)
        db.commit()
        print("Admin user created!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(create_admin())
```

---

## Git Configuration

### `.gitignore`
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
env.bak/
venv.bak/
*.egg-info/
dist/
build/
*.egg

# FastAPI
.pytest_cache/
.coverage
htmlcov/
.tox/
*.log

# Database
*.db
*.sqlite3
*.sql

# Environment
.env
.env.local
.env.development
.env.test
.env.production
*.env

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.project
.pydevproject
.settings/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
package-lock.json  # Optional: remove if you want to commit it
yarn.lock          # Optional: remove if you want to commit it

# Frontend
dist/
dist-ssr/
*.local
.cache/
.vite/

# Playwright
playwright-report/
test-results/
playwright/.cache/

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*
.pnpm-debug.log*

# Alembic (keep versions, ignore other generated files)
alembic/__pycache__/

# Redis
dump.rdb

# Temporary files
*.tmp
*.temp
*.bak
*.swp
```

---

## README Structure

### `README.md`
```markdown
# Watch Party Platform

Real-time collaborative browsing platform for watching content together.

## Features
- 🎬 Shared browser sessions
- 🎮 Remote control handoff
- 💬 Real-time text chat
- 🎙️ Voice communication
- 👥 Up to 6 participants per room

## Tech Stack
**Backend:** FastAPI, PostgreSQL, Redis, Playwright
**Frontend:** React, Vite, Tailwind CSS, WebRTC

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.11+
- Node.js 20+ (with npm)
- PostgreSQL 15+
- Redis 7+

## Quick Start

### 1. Clone and Navigate
```bash
git clone <repo-url>
cd watch-party
```

### 2. Setup PostgreSQL
```bash
# Create database
sudo -u postgres psql
CREATE DATABASE watchparty_dev;
CREATE USER watchparty WITH PASSWORD 'watchparty_dev';
GRANT ALL PRIVILEGES ON DATABASE watchparty_dev TO watchparty;
\q
```

### 3. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements/dev.txt

# Install Playwright browser
playwright install chromium

# Copy environment file
cp .env.example .env

# Run migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload
```

Backend will run on: http://localhost:8000

### 4. Frontend Setup (New Terminal)
```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start dev server
npm run dev
```

Frontend will run on: http://localhost:5173

### 5. Start Redis (if not running as service)
```bash
redis-server
```

## Development

### Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Redis (if needed):**
```bash
redis-server
```

### Database Migrations

```bash
cd backend
source .venv/bin/activate

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
cd backend
source .venv/bin/activate
pytest
```

## Project Structure
See [docs/project-structure.md](docs/project-structure.md)

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://watchparty:watchparty_dev@localhost:5432/watchparty_dev
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-super-secret-key
ENVIRONMENT=development
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Common Issues

### PostgreSQL Connection Error
```bash
# Ensure PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list                # macOS

# Check if database exists
psql -U postgres -l
```

### Redis Connection Error
```bash
# Ensure Redis is running
redis-cli ping  # Should return PONG

# Start Redis
redis-server
```

### Playwright Browser Not Found
```bash
cd backend
source .venv/bin/activate
playwright install chromium
```

## License
MIT
```

---

## Best Practices Embedded

### 1. **Separation of Concerns**
- Business logic in `services/`
- Database models in `models/`
- API schemas in `schemas/`
- Routes in `api/endpoints/`

### 2. **Feature-Based Frontend**
- Each feature is self-contained
- Components, hooks, services, and state together
- Easy to find and modify related code

### 3. **Environment Configuration**
- Separate configs for dev/test/prod
- Never commit `.env` files
- Use Pydantic Settings for validation

### 4. **Virtual Environments**
- Always use venv for Python
- Never install globally
- Keep dependencies tracked in requirements files

### 5. **Testing Structure**
- Tests alongside code
- Fixtures in `conftest.py`
- Easy to run with `pytest`

### 6. **Database Migrations**
- Use Alembic for all schema changes
- Never modify database directly
- Keep migrations in version control

This structure scales well and aligns with your FastAPI expertise!

---

## Quick Start Commands Reference

### First Time Setup
```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
playwright install chromium
cp .env.example .env
alembic upgrade head

# Frontend
cd frontend
npm install
cp .env.example .env
```

### Daily Development
```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Redis (if not running as service)
redis-server
```

### When Pulling New Code
```bash
# Backend - check for new dependencies
cd backend
source .venv/bin/activate
pip install -r requirements/dev.txt
alembic upgrade head  # Apply new migrations

# Frontend - check for new dependencies
cd frontend
npm install
```

### Common Tasks
```bash
# Create new migration
cd backend && source .venv/bin/activate
alembic revision --autogenerate -m "add new table"

# Run tests
cd backend && source .venv/bin/activate && pytest

# Build frontend for production
cd frontend && npm run build

# Check Python code style
cd backend && source .venv/bin/activate
black app/
flake8 app/
```

