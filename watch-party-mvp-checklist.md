# Watch Party MVP - Feature Checklist

## What Makes the Cut for MVP?

### ✅ MUST HAVE (Core MVP)
These features are **absolutely essential** for the product to work.

#### 1. User Management
- [ ] Sign up with email/password
- [ ] Login with JWT authentication
- [ ] Basic profile (username display)
- [ ] Logout

#### 2. Room Operations
- [ ] Create room (get unique room code/link)
- [ ] Join room via code/link
- [ ] See list of participants in room
- [ ] Leave room
- [ ] Close room (host only)
- [ ] Maximum 6 participants per room (technical limit for P2P)

#### 3. Shared Browser (THE CORE FEATURE)
- [ ] Spawn headless browser per room (Playwright)
- [ ] Stream browser screen to all participants
- [ ] Display stream in frontend
- [ ] Navigate to URLs
- [ ] Basic controls: back, forward, refresh

#### 4. Remote Control System
- [ ] One person controls browser at a time
- [ ] Host starts with control automatically
- [ ] Current controller can pass remote to another user
- [ ] Host can take remote from anyone at any time
- [ ] Visual indicator showing who has control
- [ ] Mouse movements synced
- [ ] Clicks synced
- [ ] Keyboard input synced
- [ ] Scrolling synced

#### 5. Text Chat
- [ ] Send/receive messages in real-time (WebSocket)
- [ ] Display who sent each message
- [ ] Show timestamps
- [ ] Show "User joined" / "User left" notifications
- [ ] Chat history visible when you join

#### 6. Voice Chat
- [ ] Connect voice channels (WebRTC)
- [ ] Mute/unmute yourself
- [ ] See who's talking (visual indicator)
- [ ] Adjust individual user volumes
- [ ] Works with up to 6 people (P2P mesh network)

---

### 🎯 NICE TO HAVE (Post-MVP)
These features improve the experience but aren't critical for launch.

#### Phase 2 Features
- [ ] Request remote (guest sends request, host approves)
- [ ] Video chat (webcam streams)
- [ ] Screen sharing from participants
- [ ] Emoji reactions overlay on browser
- [ ] Better chat (edit messages, delete, reply threads)
- [ ] Custom room names/URLs
- [ ] Room password protection
- [ ] Email invites
- [ ] User avatars
- [ ] Dark mode
- [ ] Mobile support

#### Phase 3 Features
- [ ] Record sessions
- [ ] Replay past sessions
- [ ] Room templates (pre-configured settings)
- [ ] Synchronized video player controls
- [ ] Picture-in-picture mode
- [ ] Multiple tabs support in browser
- [ ] Browser bookmarks/favorites
- [ ] Room analytics
- [ ] Bigger room capacity (needs SFU)

---

## Technical MVP Stack

### Backend
```
FastAPI (Python)
├── PostgreSQL (user data, rooms, messages)
├── Redis (sessions, room state, cache)
├── Playwright (headless browser automation)
├── WebSocket (real-time communication)
└── aiortc or simple WebRTC signaling (voice)
```

### Frontend
```
React + Vite
├── Tailwind CSS (styling)
├── shadcn/ui (UI components)
├── WebSocket client (chat + control)
├── simple-peer (WebRTC voice)
└── Zustand (state management)
```

### Local Development
```
Virtual Environment (Python)
├── FastAPI application
├── PostgreSQL database (local install)
├── Redis server (local install)
└── Playwright browser automation
```

---

## MVP User Flow

### 1. New User Journey
```
1. Land on homepage
2. Click "Sign Up"
3. Enter email, username, password
4. Click "Create Account"
5. Redirect to dashboard
```

### 2. Creating a Watch Party
```
1. On dashboard, click "Create Room"
2. (Optional) Enter room title
3. Click "Create"
4. Get unique room link (e.g., /room/abc123)
5. Copy link to share with friends
6. Wait in room for friends to join
```

### 3. Joining a Watch Party
```
1. Receive room link from friend
2. Click link (if logged in, join directly)
3. If not logged in, prompt to sign up/login
4. After auth, join room
5. See browser stream + chat + participants
```

### 4. Watching Together
```
1. Host has control initially
2. Host navigates to YouTube
3. Host searches for video
4. Host starts playing video
5. Everyone sees the same stream
6. Chat about what you're watching
7. Talk via voice
```

### 5. Passing Control
```
1. Current controller clicks "Pass Remote"
2. Selects friend from participant list
3. Friend gets notification "You now have control"
4. Friend can now control the browser
5. Host can take back control anytime with "Take Remote"
```

---

## What We're NOT Building (MVP Scope Cuts)

### ❌ Out of Scope
- **Account recovery:** No password reset in MVP (add later)
- **Email verification:** Trust users for MVP
- **User profiles:** No bio, avatar upload, etc.
- **Friend system:** No friend lists or invites
- **Room history:** Rooms are ephemeral, no replay
- **Recording:** Too complex and storage-heavy
- **Mobile apps:** Desktop web only
- **Payment/monetization:** Free only for MVP
- **Admin dashboard:** Manual management if needed
- **Content moderation:** Trust-based initially
- **Advanced browser features:** No extensions, bookmarks, etc.
- **Multiple simultaneous rooms per user:** One at a time
- **Room scheduling:** Rooms are created on-demand only

---

## MVP Feature Priorities (Build Order)

### Priority 1 (Weeks 1-4): Can't Ship Without This
1. User authentication (login/signup)
2. Room creation and joining
3. Basic WebSocket connection
4. Participant tracking

### Priority 2 (Weeks 5-8): The Magic Happens Here
5. Browser streaming (Playwright + WebRTC)
6. Remote control system (mouse, keyboard, clicks)
7. Control handoff logic

### Priority 3 (Weeks 9-10): Making It Social
8. Text chat with history
9. Join/leave notifications

### Priority 4 (Weeks 11-12): Adding Voice
10. Voice chat (P2P WebRTC)
11. Mute controls
12. Speaking indicators

### Priority 5 (Weeks 13-14): Polish & Ship
13. Frontend UI/UX refinement
14. Error handling and edge cases
15. Testing and bug fixes
16. Deployment

---

## Success Criteria for MVP Launch

### Functional Requirements
- [ ] User can sign up and log in without errors
- [ ] User can create a room and get a shareable link
- [ ] At least 3 people can join the same room
- [ ] Browser stream is visible to all participants (min 720p)
- [ ] Remote control passes between users smoothly
- [ ] Chat messages appear for everyone within 1 second
- [ ] Voice chat works with 3+ people simultaneously
- [ ] Host can always take control back
- [ ] Room closes when host leaves

### Technical Requirements
- [ ] No crashes for 30-minute session
- [ ] Control latency under 300ms
- [ ] Voice has no significant echo or feedback
- [ ] Works on latest Chrome, Firefox, Safari
- [ ] Can support 5 concurrent rooms (for testing)

### User Experience Requirements
- [ ] First-time user can create room in under 2 minutes
- [ ] Friends can join via link in under 30 seconds
- [ ] Remote handoff feels intuitive
- [ ] No confusing error messages
- [ ] UI is clean and uncluttered

---

## Development Phases (14-Week Timeline)

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Users can create accounts and authenticate

**Deliverables:**
- FastAPI project setup with virtual environment
- PostgreSQL + Redis configured locally
- User registration endpoint
- Login endpoint with JWT
- Basic frontend (login/signup pages)

**Success Metric:** Can create account and login

**Setup tasks:**
- Install PostgreSQL and Redis locally
- Create Python virtual environment
- Install FastAPI dependencies
- Set up Alembic for migrations
- Initialize React project with Vite

---

### Phase 2: Room System (Weeks 3-4)
**Goal:** Users can create and join rooms

**Deliverables:**
- Room creation API
- Room joining API
- WebSocket connection setup
- Participant tracking
- Basic room UI (empty for now)

**Success Metric:** Multiple users in same room, see participant list

---

### Phase 3: Browser Integration (Weeks 5-6)
**Goal:** Shared browser stream works

**Deliverables:**
- Playwright browser spawning
- Screen capture implementation
- WebRTC stream to participants
- Basic browser viewport in UI
- URL navigation

**Success Metric:** All participants see the same browser output

**Setup tasks:**
- Install Playwright and Chromium browser
- Configure browser launch settings
- Set up WebRTC streaming pipeline

---

### Phase 4: Remote Control (Weeks 7-8)
**Goal:** Users can control the browser and pass control

**Deliverables:**
- Mouse/keyboard event capture
- Event relay to browser
- Remote holder state management
- Pass/take remote logic
- Control UI indicators

**Success Metric:** Smooth browser control with visible cursor sync

---

### Phase 5: Chat (Week 9)
**Goal:** Real-time text communication

**Deliverables:**
- WebSocket message handling
- Message persistence
- Chat UI component
- History on join
- Notifications for join/leave

**Success Metric:** Chat feels instant and reliable

---

### Phase 6: Voice (Weeks 10-11)
**Goal:** Voice communication works

**Deliverables:**
- WebRTC peer connections (P2P)
- Audio stream routing
- Mute/unmute controls
- Speaking indicators
- Volume controls

**Success Metric:** Clear voice with 3+ people, no echo

---

### Phase 7: Frontend Polish (Week 12)
**Goal:** UI is clean and usable

**Deliverables:**
- Responsive layout
- Error states
- Loading states
- Tooltips and help text
- Visual polish

**Success Metric:** First-time user doesn't get confused

---

### Phase 8: Testing & Deployment (Weeks 13-14)
**Goal:** Ship to production

**Deliverables:**
- End-to-end testing
- Bug fixes
- Environment configuration for production
- Deployment to hosting (Railway, Render, or Fly.io)
- Documentation

**Success Metric:** Live URL that works

---

## Common Pitfalls to Avoid

### 1. Feature Creep
**Problem:** Adding "just one more feature" before launch
**Solution:** Stick to this checklist. Write down new ideas for v2.

### 2. Over-Engineering
**Problem:** Building for scale before you have users
**Solution:** Use simple solutions (P2P instead of SFU, SQLite → Postgres, etc.)

### 3. Perfection Paralysis
**Problem:** Waiting for everything to be perfect
**Solution:** Ship with known bugs (document them). Fix after launch.

### 4. Ignoring Real Users
**Problem:** Building in isolation without feedback
**Solution:** Get 3-5 friends testing by week 8. Listen to their pain points.

### 5. Underestimating Browser Complexity
**Problem:** Playwright can be finicky with different sites
**Solution:** Test with YouTube, Netflix, Twitch early. Some sites may block automation.

---

## Weekly Milestones (Checkpoints)

### Week 2 Checkpoint
✅ Can register and login
✅ PostgreSQL database is set up locally
✅ Redis is running locally
✅ Basic frontend structure exists
✅ Virtual environment configured with dependencies

### Week 4 Checkpoint
✅ Can create a room
✅ Multiple users can join room
✅ See participant list live
✅ WebSocket connections working

### Week 6 Checkpoint
✅ Browser stream visible to all users
✅ Can navigate to different URLs
✅ Stream quality is acceptable
✅ Playwright automation working

### Week 8 Checkpoint
✅ Remote control works smoothly
✅ Can pass control between users
✅ Host can override
✅ Input latency is acceptable

### Week 10 Checkpoint
✅ Chat messages work in real-time
✅ Join/leave notifications appear
✅ Chat history loads
✅ WebSocket stability tested

### Week 12 Checkpoint
✅ Voice chat connects
✅ Can mute/unmute
✅ No significant audio issues
✅ P2P connections stable

### Week 14 Checkpoint
✅ Deployed to production hosting
✅ All core features working
✅ Ready for first users
✅ Documentation complete

---

## Questions to Answer Before Building

### Technical Decisions
1. **Playwright vs Puppeteer?** → Playwright (better maintained, faster)
2. **JWT in cookies or localStorage?** → httpOnly cookies (more secure)
3. **How to handle browser crashes?** → Auto-restart, notify users
4. **Max room duration?** → 4 hours (auto-close after)
5. **WebRTC: P2P or SFU?** → P2P for MVP (simpler, free)
6. **PostgreSQL vs MongoDB?** → PostgreSQL (better for relational data, ACID transactions)
7. **Local development vs Docker?** → Local for MVP (simpler setup, faster iteration)

### Product Decisions
1. **Require login to join rooms?** → Yes (prevents abuse)
2. **Allow room passwords?** → No for MVP (add v2)
3. **Show browser URL bar to participants?** → Yes (transparency)
4. **Allow multiple tabs?** → No for MVP (too complex)
5. **What happens when host disconnects?** → Room closes (simplest)

### Business Decisions
1. **Completely free or freemium?** → Free for MVP
2. **Terms of service?** → Yes, simple ToS (anti-piracy clause)
3. **Age restrictions?** → 13+ (COPPA compliance)
4. **Data retention?** → Delete messages after 7 days
5. **Support mechanism?** → Email only for MVP

---

This checklist is your north star. When in doubt, check back here!