# Watch Party Platform - Product Requirements Document

## Project Overview
A real-time collaborative browsing platform that enables users to watch content together with friends through a shared browser session, complete with remote control handoff, text chat, and voice communication.

**Tech Stack:**
- **Backend:** FastAPI (Python)
- **Frontend:** React + WebRTC
- **Real-time Communication:** WebSockets (FastAPI WebSocket support)
- **Browser Streaming:** WebRTC + Screen Sharing API
- **Database:** PostgreSQL
- **Cache/Session Store:** Redis
- **File Storage:** MinIO (for recordings/snapshots if needed)
- **Containerization:** Docker

---

## Core Concept
Think of it as "Hyperbeam for watch parties" - a browser-in-browser experience where:
1. Host creates a room with a virtual browser
2. Multiple guests can join
3. Control passes between participants via "remote control" system
4. Real-time text and voice chat accompanies the shared browsing

---

## MVP Feature Set

### Phase 1: Foundation (Weeks 1-2)
**Priority: Critical**

#### 1.1 User Authentication
- [ ] User registration (email + password)
- [ ] User login with JWT tokens
- [ ] Basic user profile (username, email)
- [ ] Password reset flow
- [ ] Session management with Redis

**Why First:** Need user identity before creating/joining rooms

#### 1.2 Room Management
- [ ] Create room (generates unique room ID)
- [ ] Join room via room ID or link
- [ ] Room capacity limit (e.g., max 10 users)
- [ ] Host designation (creator is host)
- [ ] Basic room metadata (title, created_at, host_id)
- [ ] Close/end room (host only)

**Database Schema:**
```sql
users (id, username, email, password_hash, created_at)
rooms (id, room_code, title, host_id, created_at, ended_at, max_participants)
room_participants (id, room_id, user_id, joined_at, is_host)
```

---

### Phase 2: Browser Streaming & Control (Weeks 3-5)
**Priority: Critical - This is your core feature**

#### 2.1 Browser Session Setup
- [ ] Headless browser instance per room (using Playwright or Selenium)
- [ ] Browser screen capture and streaming
- [ ] WebRTC peer connection setup
- [ ] Stream browser display to all participants

**Technical Approach:**
- **Option A (Recommended for MVP):** Each room spawns a headless Chromium instance via Playwright
- **Option B (Advanced):** Use containerized browser instances (browserless.io approach)

#### 2.2 Remote Control System
- [ ] "Remote holder" state management (only one user at a time)
- [ ] Host can take remote from anyone instantly
- [ ] Current holder can pass remote to specific user
- [ ] Guests can request remote (optional for MVP)
- [ ] Visual indicator of who has control
- [ ] Mouse movement relay
- [ ] Keyboard input relay
- [ ] Click/scroll event relay

**WebSocket Events:**
```
- remote.request
- remote.grant
- remote.revoke
- remote.pass
- browser.mouse_move
- browser.click
- browser.scroll
- browser.keypress
```

#### 2.3 Browser Interaction
- [ ] Navigate to URLs
- [ ] Backward/forward navigation
- [ ] Refresh page
- [ ] New tab support (optional for MVP)
- [ ] Full-screen toggle

---

### Phase 3: Real-time Chat (Week 6)
**Priority: High**

#### 3.1 Text Chat
- [ ] WebSocket-based message delivery
- [ ] Message persistence in database
- [ ] Chat history on join
- [ ] User join/leave notifications
- [ ] Typing indicators
- [ ] Message timestamps
- [ ] Basic emoji support

**Database Schema:**
```sql
messages (id, room_id, user_id, message, created_at)
```

---

### Phase 4: Voice Chat (Weeks 7-8)
**Priority: Medium-High**

#### 4.1 WebRTC Voice
- [ ] Peer-to-peer voice connections (mesh network for MVP)
- [ ] Mute/unmute controls
- [ ] Speaker volume controls
- [ ] Push-to-talk option
- [ ] Voice status indicators

**Technical Note:** 
- For MVP: P2P mesh (works well up to 5-6 users)
- Future: Consider SFU (Selective Forwarding Unit) like mediasoup for scalability

---

### Phase 5: Frontend UI (Weeks 9-10)
**Priority: Critical**

#### 5.1 Core Pages
- [ ] Landing page
- [ ] Login/Register page
- [ ] Dashboard (create/join room)
- [ ] Room page (main interface)

#### 5.2 Room Interface Components
- [ ] Browser viewport (main area - 70% screen)
- [ ] Chat panel (side panel - 20% screen)
- [ ] Participant list with controls
- [ ] Remote control indicator/controls
- [ ] Voice chat controls (bottom bar)
- [ ] Room settings/controls

#### 5.3 Responsive Design
- [ ] Desktop-first (tablets minimum)
- [ ] Mobile warning/limited support

---

## Post-MVP Features (Future Phases)

### Phase 6: Enhanced Features
- [ ] Video chat (WebRTC video streams)
- [ ] Screen sharing from participants
- [ ] Room history/replays
- [ ] Invite system (email invites)
- [ ] Room passwords/privacy settings
- [ ] Custom room URLs (vanity URLs)
- [ ] Reactions/emojis overlay on browser
- [ ] Synchronized playback controls for video players

### Phase 7: Scaling & Performance
- [ ] SFU implementation for voice/video
- [ ] Multiple browser instance servers
- [ ] Load balancing
- [ ] CDN for static assets
- [ ] Horizontal scaling with Redis Cluster

### Phase 8: Premium Features (Monetization)
- [ ] Recording sessions
- [ ] Larger room capacity
- [ ] Custom branding
- [ ] Analytics dashboard
- [ ] Ad-free experience

---

## Technical Architecture

### Backend Services

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
├─────────────────────────────────────────┤
│  - REST API (auth, rooms, users)        │
│  - WebSocket Server (chat, control)     │
│  - Browser Manager (Playwright)         │
│  - WebRTC Signaling Server              │
└─────────────────────────────────────────┘
            ↓           ↓
    ┌───────────┐  ┌──────────┐
    │PostgreSQL │  │  Redis   │
    │(Main DB)  │  │(Sessions)│
    └───────────┘  └──────────┘
```

### Frontend Architecture

```
┌─────────────────────────────────────────┐
│           React Application             │
├─────────────────────────────────────────┤
│  - Authentication (JWT)                 │
│  - WebSocket Client (Socket.io/native)  │
│  - WebRTC Client (simple-peer)          │
│  - UI Components (Tailwind CSS)         │
└─────────────────────────────────────────┘
```

---

## Chronological Build Order

### Sprint 1 (Week 1-2): Foundation
1. Set up FastAPI project structure
2. Configure PostgreSQL + Redis with Docker
3. Implement user authentication (register/login)
4. Create basic REST API endpoints
5. Set up JWT token management
6. Database migrations setup (Alembic)

### Sprint 2 (Week 3-4): Core Room Logic
1. Room creation/joining API endpoints
2. Room state management in Redis
3. WebSocket connection handling
4. Basic room participant tracking
5. Host/guest role assignment
6. Room closure logic

### Sprint 3 (Week 5-6): Browser Integration
1. Integrate Playwright for headless browser
2. Browser screen capture implementation
3. WebRTC stream setup (browser → server)
4. Stream relay to all participants
5. Basic remote control (mouse/keyboard events)
6. Remote holder state management

### Sprint 4 (Week 7): Remote Control System
1. Remote request/grant/revoke logic
2. Host override capabilities
3. Guest-to-guest remote passing
4. Control event relay optimization
5. Cursor synchronization
6. Input lag reduction

### Sprint 5 (Week 8): Text Chat
1. WebSocket message handling
2. Chat message persistence
3. Message history retrieval
4. Join/leave notifications
5. Typing indicators
6. Chat UI component

### Sprint 6 (Week 9-10): Voice Chat
1. WebRTC peer connection setup
2. Audio stream handling (P2P mesh)
3. Mute/unmute controls
4. Audio mixing (if needed)
5. Voice status indicators
6. Audio quality optimization

### Sprint 7 (Week 11-12): Frontend Development
1. React app setup with Vite
2. Authentication pages (login/register)
3. Dashboard for room management
4. Main room interface layout
5. Browser viewport component
6. Chat panel component
7. Participant list component
8. Voice controls component

### Sprint 8 (Week 13): Integration & Testing
1. End-to-end testing
2. Performance optimization
3. Bug fixes
4. Cross-browser testing
5. Mobile responsiveness check
6. Security audit

### Sprint 9 (Week 14): Deployment
1. Docker containerization
2. CI/CD pipeline setup
3. Environment configuration
4. Production deployment
5. Monitoring setup
6. Documentation

---

## Free Tool Recommendations

### Development
- **Code Editor:** VS Code
- **API Testing:** Postman (free tier) / Thunder Client
- **Database GUI:** pgAdmin / DBeaver
- **Redis GUI:** RedisInsight

### Frontend
- **Framework:** React (with Vite)
- **UI Library:** Tailwind CSS + shadcn/ui
- **Icons:** Lucide React / Heroicons
- **WebRTC:** simple-peer library
- **WebSocket:** Native WebSocket API or socket.io-client
- **State Management:** Zustand (lightweight) or Context API

### Backend
- **WebRTC:** aiortc (Python WebRTC)
- **Browser Automation:** Playwright
- **WebSocket:** FastAPI native WebSocket support
- **Task Queue:** Celery (for background tasks)
- **Testing:** pytest + pytest-asyncio

### Infrastructure (Free Tiers)
- **Hosting:** 
  - Railway.app (generous free tier)
  - Render.com (free tier)
  - Fly.io (free tier)
- **Database:** 
  - Supabase (free PostgreSQL)
  - ElephantSQL (free tier)
- **Redis:** 
  - Upstash (free tier)
  - Redis Cloud (free tier)
- **Storage:** 
  - Cloudflare R2 (10GB free)
  - Backblaze B2 (10GB free)

### Monitoring & Analytics
- **Logging:** Sentry (free tier)
- **Analytics:** Plausible (self-hosted) / Umami
- **Uptime:** UptimeRobot (free tier)

---

## Technical Challenges & Solutions

### Challenge 1: Browser Resource Management
**Problem:** Each room runs a headless browser instance - resource intensive

**Solutions:**
- Set maximum concurrent rooms
- Implement room timeout (auto-close after inactivity)
- Use lightweight browser profiles
- Monitor memory usage and kill zombie processes

### Challenge 2: WebRTC Scaling
**Problem:** P2P mesh doesn't scale beyond 5-6 users

**Solutions:**
- MVP: Limit rooms to 6 participants
- Future: Implement SFU (mediasoup)
- Alternative: Use managed service (Daily.co has free tier)

### Challenge 3: Latency in Remote Control
**Problem:** Mouse/keyboard events need to be near-instant

**Solutions:**
- Use UDP where possible (WebRTC data channels)
- Implement input prediction/smoothing
- Reduce server-side processing
- Direct peer-to-peer event relay

### Challenge 4: Browser Compatibility
**Problem:** Different browsers handle WebRTC differently

**Solutions:**
- Focus on Chrome/Chromium for MVP
- Use adapter.js for WebRTC compatibility
- Clear browser requirements in documentation

---

## Security Considerations

### Authentication & Authorization
- [ ] JWT token expiration (15min access, 7day refresh)
- [ ] HTTPS only in production
- [ ] Password hashing (bcrypt)
- [ ] Rate limiting on auth endpoints
- [ ] CORS configuration

### Room Security
- [ ] Room access validation
- [ ] Host verification for privileged actions
- [ ] Prevent XSS in chat messages
- [ ] Browser isolation between rooms
- [ ] Input sanitization for browser navigation

### Privacy
- [ ] No recording by default
- [ ] Clear data retention policy
- [ ] Option to delete chat history
- [ ] Anonymous guest mode (future)

---

## Success Metrics (MVP)

### Technical Metrics
- Room creation success rate > 99%
- WebSocket connection stability > 95%
- Average control latency < 200ms
- Browser stream quality > 720p @ 30fps
- Support 5+ concurrent rooms

### User Experience Metrics
- Room setup time < 30 seconds
- Join room time < 10 seconds
- Remote handoff time < 2 seconds
- Chat message delivery < 100ms

---

## Estimated Timeline

**MVP Delivery:** 14 weeks (3.5 months) part-time
**Full-time equivalent:** 7-8 weeks

**Breakdown:**
- Backend Core: 4 weeks
- Browser Integration: 3 weeks
- Frontend: 3 weeks
- Voice Chat: 2 weeks
- Testing & Deployment: 2 weeks

---

## Next Steps

1. **Week 0 (Prep):**
   - Set up development environment
   - Create project repository
   - Initialize FastAPI + React projects
   - Set up Docker Compose for local development

2. **Week 1 (Start Building):**
   - Begin Sprint 1 (Foundation)
   - Focus on authentication first
   - Set up database schemas
   - Create basic API structure

3. **Build, Test, Iterate:**
   - Complete sprints in order
   - Test each feature before moving on
   - Document as you build
   - Seek feedback early and often

---

## Risk Mitigation

### High Risk Areas
1. **Browser automation reliability:** Test Playwright thoroughly early
2. **WebRTC complexity:** Use proven libraries (simple-peer)
3. **Scaling costs:** Implement strict limits on free tier
4. **Legal concerns:** Add ToS prohibiting copyrighted content streaming

### Contingency Plans
- If Playwright is too heavy → Consider puppeteer or browser-based approach
- If WebRTC is too complex → Start with screen sharing API only
- If voice chat is problematic → Ship MVP without it, add later
- If hosting costs exceed budget → Implement waitlist/invite system

---

## Open Questions

1. Should guests be able to kick each other? (Recommend: No, host only)
2. Maximum room duration before auto-close? (Suggest: 4 hours)
3. Allow anonymous joining or require signup? (Suggest: Require signup for MVP)
4. Should chat history persist after room closes? (Suggest: Yes, for host only)
5. Rate limiting for room creation? (Suggest: 5 rooms per hour per user)

---

This PRD is a living document. Update as you build and learn!