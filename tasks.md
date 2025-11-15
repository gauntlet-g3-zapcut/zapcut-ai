# AdCraft AI - Development Tasks

## Project Setup & Infrastructure

### Phase 1: Project Scaffold (Hours 1-2)
- [ ] Initialize React frontend (Vite)
  - [ ] Setup project structure
  - [ ] Install dependencies (React Router, Firebase SDK, etc.)
  - [ ] Configure build tools
- [ ] Initialize FastAPI backend
  - [ ] Setup project structure
  - [ ] Install dependencies (FastAPI, SQLAlchemy, Celery, etc.)
  - [ ] Configure CORS
- [ ] Setup environment variables
  - [ ] Create `.env.example` files
  - [ ] Document required API keys
- [ ] Initialize Git repository
  - [ ] Create `.gitignore`
  - [ ] Initial commit

### Phase 2: Database & Auth (Hours 2-4)
- [ ] Setup PostgreSQL database
  - [ ] Create database schema (users, brands, creative_bibles, campaigns)
  - [ ] Create migration files
  - [ ] Setup SQLAlchemy models
- [ ] Firebase Authentication setup
  - [ ] Create Firebase project
  - [ ] Configure Firebase Auth (email/password, Google OAuth)
  - [ ] Frontend: Auth context/provider
  - [ ] Backend: Verify Firebase tokens
- [ ] User management API
  - [ ] POST /api/users (create user from Firebase)
  - [ ] GET /api/users/me (get current user)

### Phase 3: Railway Deployment Setup (Hours 3-4)
- [ ] Setup Railway account
  - [ ] Create new project
  - [ ] Connect GitHub repository
- [ ] Configure Railway services
  - [ ] PostgreSQL service
  - [ ] Redis service (for Celery)
  - [ ] Backend service
- [ ] Environment variables in Railway
  - [ ] Database URL
  - [ ] Redis URL
  - [ ] API keys (OpenAI, Replicate, S3, Firebase)

---

## Frontend Development

### Phase 4: Landing & Auth Pages (Hours 5-6)
- [ ] Landing Page
  - [ ] Hero section with value proposition
  - [ ] "Get Started" button
  - [ ] Basic styling (modern, clean)
- [ ] Login/Auth Page
  - [ ] Email/password form
  - [ ] Google OAuth button
  - [ ] Error handling
  - [ ] Redirect to dashboard after login
- [ ] Auth Context/Provider
  - [ ] User state management
  - [ ] Protected routes
  - [ ] Logout functionality

### Phase 5: Brands Dashboard (Hours 6-7)
- [ ] Layout component
  - [ ] Left sidebar (user info, navigation, credits)
  - [ ] Main content area
- [ ] Brands Dashboard page
  - [ ] Header with "Brands" title and count
  - [ ] Grid/list of brand cards
  - [ ] Brand card component (image, title, description, campaign count)
  - [ ] "Create Brand +" button
- [ ] API integration
  - [ ] GET /api/brands (list user's brands)
  - [ ] Loading states
  - [ ] Empty state

### Phase 6: Create Brand Form (Hours 7-8)
- [ ] Create Brand page
  - [ ] Title input
  - [ ] Description textarea
  - [ ] Product Image 1 upload
  - [ ] Product Image 2 upload
  - [ ] Image preview
  - [ ] Form validation
  - [ ] Submit button
- [ ] Image upload
  - [ ] Upload to S3 (via backend)
  - [ ] Progress indicator
  - [ ] Error handling
- [ ] API integration
  - [ ] POST /api/brands (create brand)
  - [ ] Redirect to Brand Chat after creation

### Phase 7: Brand Chat Interface (Hours 9-10)
- [ ] Chat UI component
  - [ ] Message list (user messages, LLM responses)
  - [ ] Input field
  - [ ] Send button
  - [ ] Message bubbles styling
- [ ] Chat state management
  - [ ] Message history
  - [ ] Current question tracking
  - [ ] "Go back" functionality
- [ ] API integration
  - [ ] POST /api/brands/{brand_id}/chat (send message)
  - [ ] WebSocket or polling for responses
  - [ ] Handle follow-up questions
  - [ ] Detect when brief is complete

### Phase 8: Storyline Review Page (Hours 10-11)
- [ ] Storyline/Script display
  - [ ] Creative Bible summary
  - [ ] Scene cards (5 scenes)
  - [ ] Each scene: title, description, timing, energy levels
  - [ ] Suno prompt preview
- [ ] Actions
  - [ ] "Approve" button
  - [ ] "Edit" button (optional - go back to chat)
- [ ] API integration
  - [ ] GET /api/campaigns/{campaign_id}/storyline
  - [ ] POST /api/campaigns/{campaign_id}/approve (start generation)

### Phase 9: Video Generation Progress (Hours 11-12)
- [ ] Progress page
  - [ ] Progress indicator
  - [ ] Current stage display:
    - Generating reference images...
    - Creating storyboard...
    - Generating video scenes (1/5, 2/5, etc.)...
    - Generating soundtrack...
    - Composing final video...
  - [ ] ETA/estimated time
  - [ ] Loading animation
- [ ] Real-time updates
  - [ ] WebSocket or polling for progress
  - [ ] Update UI as stages complete
- [ ] API integration
  - [ ] GET /api/campaigns/{campaign_id}/status
  - [ ] WebSocket connection for live updates

### Phase 10: Video Player (Hours 17-18)
- [ ] Video player component
  - [ ] 4K video player (HTML5 video)
  - [ ] Autoplay preview
  - [ ] Play/Pause controls
- [ ] Download functionality
  - [ ] Download MP4 button
  - [ ] Download WebM button
- [ ] Share functionality
  - [ ] Generate shareable link
  - [ ] Copy to clipboard
- [ ] API integration
  - [ ] GET /api/campaigns/{campaign_id}/video
  - [ ] GET /api/campaigns/{campaign_id}/share-link

---

## Backend Development

### Phase 11: Core APIs (Hours 8-9)
- [ ] Brands API
  - [ ] GET /api/brands (list user's brands)
  - [ ] POST /api/brands (create brand)
  - [ ] GET /api/brands/{brand_id} (get brand details)
- [ ] Campaigns API
  - [ ] GET /api/brands/{brand_id}/campaigns (list campaigns)
  - [ ] GET /api/campaigns/{campaign_id} (get campaign)
  - [ ] POST /api/campaigns (create campaign)

### Phase 12: Chat & LLM Integration (Hours 10-12)
- [ ] Chat API endpoint
  - [ ] POST /api/brands/{brand_id}/chat
  - [ ] Store conversation history
  - [ ] Call OpenAI GPT-4
- [ ] OpenAI integration
  - [ ] Setup OpenAI client
  - [ ] Creative Director system prompt
  - [ ] Handle follow-up questions (one at a time)
  - [ ] Detect when brief is complete
- [ ] Creative Bible generation
  - [ ] Extract style, vibe, energy from conversation
  - [ ] Generate Creative Bible JSON
  - [ ] Store in database
- [ ] Storyline/Script generation
  - [ ] Generate 5-scene storyline
  - [ ] Generate Suno prompt with precise timing
  - [ ] Return formatted JSON

### Phase 13: Celery Task Queue (Hours 12-13)
- [ ] Celery setup
  - [ ] Configure Celery with Redis
  - [ ] Create task definitions
  - [ ] Setup task routing
- [ ] Video generation task
  - [ ] Generate reference images
  - [ ] Generate Sora prompts
  - [ ] Generate video scenes
  - [ ] Generate music
  - [ ] Compose final video
  - [ ] Update campaign status

### Phase 14: Replicate API Integration (Hours 13-14)
- [ ] Replicate client setup
  - [ ] Install Replicate SDK
  - [ ] Configure API key
- [ ] Reference image generation
  - [ ] Find best model (Flux Pro, SDXL, etc.)
  - [ ] Generate image prompts (LLM)
  - [ ] Call Replicate API (parallel)
  - [ ] Download and store images
- [ ] Sora video generation
  - [ ] Generate 5 scene prompts
  - [ ] Call Sora API (parallel for 5 scenes)
  - [ ] Poll for completion
  - [ ] Download video clips
- [ ] Suno music generation
  - [ ] Call Suno API with generated prompt
  - [ ] Poll for completion
  - [ ] Download audio file

### Phase 15: Video Composition (Hours 14-15)
- [ ] FFmpeg integration
  - [ ] Install FFmpeg
  - [ ] Create composition script
- [ ] Video stitching
  - [ ] Concatenate 5 scenes with 0.5s crossfade
  - [ ] Mix Suno audio underneath
  - [ ] Add text overlay (brand name at 24s)
  - [ ] Add text overlay ("Learn More" at 27s)
  - [ ] Encode to H.264, 4K (3840x2160), 30fps
- [ ] S3 upload
  - [ ] Upload final video
  - [ ] Upload individual scene videos
  - [ ] Upload audio file
  - [ ] Store URLs in database

### Phase 16: Error Handling & Retries (Hours 15-16)
- [ ] Retry logic
  - [ ] Retry failed API calls (exponential backoff)
  - [ ] Handle rate limits
  - [ ] Handle timeouts
- [ ] Error handling
  - [ ] Graceful failures
  - [ ] Error logging
  - [ ] User-friendly error messages
- [ ] Status tracking
  - [ ] Update campaign status (pending, generating, completed, failed)
  - [ ] Store error messages

---

## Testing & Deployment

### Phase 17: Testing (Hours 19-20)
- [ ] End-to-end testing
  - [ ] Create 3 sample brands
  - [ ] Test full generation flow
  - [ ] Verify video quality
  - [ ] Verify audio sync
- [ ] Bug fixes
  - [ ] Fix any issues found
  - [ ] Test edge cases
  - [ ] Test error scenarios

### Phase 18: Deployment (Hours 20-22)
- [ ] Backend deployment (Railway)
  - [ ] Configure production environment
  - [ ] Deploy FastAPI app
  - [ ] Deploy Celery worker
  - [ ] Test production endpoints
- [ ] Frontend deployment (Vercel)
  - [ ] Configure build settings
  - [ ] Set environment variables
  - [ ] Deploy
  - [ ] Test production site
- [ ] Final polish
  - [ ] UI/UX improvements
  - [ ] Loading states
  - [ ] Error messages
  - [ ] Performance optimization

---

## Priority Order

1. **Critical Path (Must Have)**
   - Project setup
   - Database & Auth
   - Brands Dashboard
   - Create Brand
   - Chat interface
   - LLM integration
   - Video generation pipeline
   - Video player

2. **Important (Should Have)**
   - Progress tracking
   - Error handling
   - Storyline review page
   - Download/share functionality

3. **Nice to Have (Can Skip for MVP)**
   - Edit storyline
   - Advanced video controls
   - Campaign history
   - Analytics

---

## API Endpoints Summary

### Authentication
- `POST /api/auth/verify` - Verify Firebase token
- `GET /api/users/me` - Get current user

### Brands
- `GET /api/brands` - List user's brands
- `POST /api/brands` - Create brand
- `GET /api/brands/{brand_id}` - Get brand details
- `POST /api/brands/{brand_id}/chat` - Chat with Creative Director

### Campaigns
- `GET /api/brands/{brand_id}/campaigns` - List campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{campaign_id}` - Get campaign
- `GET /api/campaigns/{campaign_id}/status` - Get generation status
- `POST /api/campaigns/{campaign_id}/approve` - Approve storyline and start generation
- `GET /api/campaigns/{campaign_id}/video` - Get video URL

---

## Environment Variables

### Frontend
```
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_API_URL=
```

### Backend
```
DATABASE_URL=
REDIS_URL=
OPENAI_API_KEY=
REPLICATE_API_TOKEN=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
FIREBASE_PROJECT_ID=
FIREBASE_PRIVATE_KEY=
FIREBASE_CLIENT_EMAIL=
```

---

## Notes

- Use React Router for frontend routing
- Use React Query or SWR for data fetching
- Use Zustand or Context API for state management
- Use Tailwind CSS or styled-components for styling
- Use WebSockets or Server-Sent Events for real-time updates
- Use PostgreSQL UUID extension for IDs
- Use boto3 for S3 operations
- Use celery-beat for scheduled tasks (if needed)


