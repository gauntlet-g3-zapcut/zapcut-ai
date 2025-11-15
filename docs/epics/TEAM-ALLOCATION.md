# 3-Developer Team Allocation Strategy

## Team Structure

### Developer 1: DevOps + Foundation Track
**Skills:** DevOps, Infrastructure, Backend
**Primary Responsibility:** Infrastructure, deployments, backend foundations

### Developer 2: Full-Stack Track (AI Features)
**Skills:** Full-stack, AI/LLM integration, Python + React
**Primary Responsibility:** Chat, script generation, AI orchestration

### Developer 3: Full-Stack Track (Video Pipeline)
**Skills:** Full-stack, Video processing, FFmpeg, Python + React
**Primary Responsibility:** Video generation, editor integration

---

## Phase-by-Phase Breakdown

### Phase 1: Foundation (Weeks 1-2)

**ALL 3 DEVELOPERS work on Epic 1 together**

This is the ONLY epic where everyone works together because:
- Epic 1 is blocking everything else
- Faster completion = earlier parallelization
- Everyone learns the infrastructure

#### Work Division:

**Developer 1 (Lead):**
- [ ] AWS infrastructure (Terraform/CDK)
  - VPC, subnets, security groups
  - RDS PostgreSQL
  - ElastiCache Redis
  - S3 buckets
- [ ] ECS cluster and task definitions
- [ ] Secrets Manager setup
- [ ] CloudWatch monitoring

**Developer 2:**
- [ ] Backend CI/CD pipeline
  - Dockerfile for FastAPI
  - GitHub Actions workflow
  - ECR setup
  - ECS deployment automation
- [ ] Database migration system (Alembic)
- [ ] Health check endpoints
- [ ] Smoke tests

**Developer 3:**
- [ ] Frontend CI/CD pipeline
  - Electron builder configuration
  - GitHub Actions for builds (macOS, Windows, Linux)
  - Auto-update configuration
  - Code signing setup
- [ ] Environment configuration management
- [ ] Sentry integration (frontend + backend)

**Checkpoint:** Epic 1 100% complete, all deployments working ✅

---

### Phase 2: Parallel Development with Mocking (Weeks 3-7)

Now developers can work in parallel by **mocking dependencies**.

#### Developer 1: Epic 2 (Auth & Brands) - REAL IMPLEMENTATION
**Duration:** 3 weeks (Weeks 3-5)

**Why Dev 1:** No dependencies, can be built from scratch

**Backend:**
- [ ] Users table and auth endpoints
- [ ] Google OAuth integration
- [ ] JWT token system
- [ ] Brands table and CRUD endpoints
- [ ] S3 image upload endpoint
- [ ] Authorization middleware

**Frontend:**
- [ ] Landing page
- [ ] Login/Signup pages
- [ ] Brands dashboard
- [ ] Create/Edit brand modals
- [ ] Image uploader component
- [ ] authStore and brandStore (Zustand)

**Tests:**
- [ ] Auth flow E2E tests
- [ ] Brand CRUD tests
- [ ] Authorization tests

**Deploy to staging weekly**

---

#### Developer 2: Epic 3 + Epic 4 (AI Chat & Script) - WITH MOCKS
**Duration:** 5 weeks (Weeks 3-7)

**Week 3-5: Epic 3 (Chat) with MOCKED Epic 2**

**Mocked Dependencies:**
```typescript
// Mock auth - hardcoded user
const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  name: 'Test User'
}

// Mock brand
const mockBrand = {
  id: 'brand-123',
  title: 'Test Shoes',
  description: 'Athletic footwear brand',
  product_images: ['https://placeholder.com/image1.jpg']
}

// Mock JWT - always valid
const mockToken = 'mock-jwt-token'
```

**Backend:**
- [ ] AdProjects table and endpoints
- [ ] ChatMessages table
- [ ] OpenAI GPT-4 integration
- [ ] 5-question conversation logic
- [ ] Structured data extraction
- [ ] ad_details JSONB population

**Frontend:**
- [ ] ChatPage component
- [ ] Message bubbles, typing indicator
- [ ] Chat input with send
- [ ] Progress tracking (5 questions)
- [ ] adProjectStore (Zustand)

**Week 6-7: Epic 4 (Script Generation)**

**Backend:**
- [ ] Scripts table
- [ ] Script generation endpoint (OpenAI)
- [ ] Structured JSON output (storyline + scenes)
- [ ] Script regeneration with feedback

**Frontend:**
- [ ] ScriptReviewPage
- [ ] SceneCard components
- [ ] Regenerate script UI
- [ ] Approve script button

**Tests:**
- [ ] OpenAI integration tests
- [ ] Script generation tests
- [ ] Chat flow E2E tests

**Deploy to staging with mocked auth**

---

#### Developer 3: Epic 5 (Video Pipeline) - WITH MOCKS
**Duration:** 5 weeks (Weeks 3-7)

**Mocked Dependencies:**
```python
# Mock auth
mock_user = User(id='user-123', email='test@example.com')

# Mock brand
mock_brand = Brand(
    id='brand-123',
    title='Test Shoes',
    product_images=['https://placeholder.com/image1.jpg']
)

# Mock script
mock_script = Script(
    storyline='Runner achieves greatness',
    scenes=[
        Scene(sceneNumber=1, duration=10, visualPrompt='...', voiceoverText='...'),
        Scene(sceneNumber=2, duration=10, visualPrompt='...', voiceoverText='...'),
        Scene(sceneNumber=3, duration=10, visualPrompt='...', voiceoverText='...')
    ]
)
```

**Backend:**
- [ ] GenerationJobs table
- [ ] RQ worker setup
- [ ] Replicate API integration (Sora for video)
- [ ] Replicate API integration (TTS for voiceover)
- [ ] Suno API integration (music)
- [ ] FFmpeg composition pipeline
  - Scene stitching with crossfades
  - Product image overlays
  - Audio mixing (voiceover + music)
- [ ] S3 upload for generated videos
- [ ] Generation status endpoint (polling)

**Frontend:**
- [ ] GenerationStatusPage
- [ ] Progress bar and status tracking
- [ ] Polling mechanism (5-second interval)
- [ ] GenerationCompleteScreen
- [ ] Video player component

**Tests:**
- [ ] RQ job tests
- [ ] Replicate API integration tests (mocked)
- [ ] FFmpeg composition tests (with sample videos)
- [ ] Progress calculation tests

**Deploy to staging with mocked script**

---

### Phase 3: Integration (Weeks 8-9)

**All developers integrate their work**

#### Week 8: Integration Sprint

**Developer 1 → Developer 2 Integration:**
- [ ] Replace mocked auth in Epic 3/4 with real Epic 2 APIs
- [ ] Replace mocked brand data
- [ ] Test JWT flow end-to-end
- [ ] Fix integration bugs

**Developer 1 → Developer 3 Integration:**
- [ ] Replace mocked auth in Epic 5 with real Epic 2 APIs
- [ ] Replace mocked brand data
- [ ] Test brand images in video generation
- [ ] Fix integration bugs

**Developer 2 → Developer 3 Integration:**
- [ ] Replace mocked script in Epic 5 with real Epic 4 script
- [ ] Test script → video generation flow
- [ ] Verify ad_details passed correctly
- [ ] Fix integration bugs

#### Week 9: End-to-End Testing

**All developers:**
- [ ] Complete user journey test: Signup → Brand → Chat → Script → Video
- [ ] Fix any remaining integration issues
- [ ] Performance testing (generation time, API latency)
- [ ] Load testing (concurrent users)
- [ ] Bug fixes and polish

**Deploy integrated system to staging**

---

### Phase 4: Editor Integration (Weeks 10-11)

**Developer 3 leads, others support**

**Developer 3 (Lead):**
- [ ] Epic 6: Editor Integration
  - Download video to local filesystem
  - Load video into Zapcut editor
  - Product images in asset library
  - "Back to Brands" navigation
  - Export functionality verification

**Developer 1 (Support):**
- [ ] Video download endpoint optimization
- [ ] S3 presigned URL generation
- [ ] Performance optimization for large files

**Developer 2 (Support):**
- [ ] UI polish and bug fixes
- [ ] Error handling improvements
- [ ] Loading states and feedback

**All developers:**
- [ ] E2E testing of complete flow
- [ ] Cross-platform testing (macOS, Windows)
- [ ] Documentation updates

**Deploy complete system to staging**

---

### Phase 5: Production Deployment (Week 12)

**All developers:**
- [ ] Final production readiness review
- [ ] Performance benchmarking
- [ ] Security audit
- [ ] Production deployment
- [ ] Post-deployment smoke tests
- [ ] Monitoring verification
- [ ] Production incident response plan

---

## Timeline Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│ WEEK 1-2: Epic 1 - ALL DEVELOPERS TOGETHER                             │
├─────────────────────────────────────────────────────────────────────────┤
│ Dev 1: AWS Infra (Terraform, RDS, Redis, S3, ECS)                       │
│ Dev 2: Backend CI/CD + Alembic + Health checks                          │
│ Dev 3: Frontend CI/CD + Electron builds + Sentry                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ WEEK 3-5: PARALLEL DEVELOPMENT (with mocking)                           │
├─────────────────────────────────────────────────────────────────────────┤
│ Dev 1: Epic 2 (Auth & Brands) - REAL IMPLEMENTATION                     │
│   ✓ OAuth, JWT, Users/Brands tables, S3 uploads, UI                    │
│                                                                          │
│ Dev 2: Epic 3 (AI Chat) - MOCKED Auth/Brands                           │
│   ⚠ Mock user/brand data, build chat system                            │
│                                                                          │
│ Dev 3: Epic 5 (Video Pipeline) - MOCKED Auth/Brands/Script             │
│   ⚠ Mock all dependencies, build generation pipeline                   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ WEEK 6-7: PARALLEL DEVELOPMENT (continued)                              │
├─────────────────────────────────────────────────────────────────────────┤
│ Dev 1: Epic 2 COMPLETE ✅ → Support others with integration prep        │
│                                                                          │
│ Dev 2: Epic 4 (Script Generation) - MOCKED Auth/Brands                 │
│   ⚠ Continue with mocks, build script gen                              │
│                                                                          │
│ Dev 3: Epic 5 (Video Pipeline) - CONTINUED                             │
│   ⚠ FFmpeg composition, audio mixing, progress tracking                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ WEEK 8: INTEGRATION SPRINT                                              │
├─────────────────────────────────────────────────────────────────────────┤
│ Dev 1 → Dev 2: Replace mocks in Epic 3/4 with real Epic 2              │
│ Dev 1 → Dev 3: Replace mocks in Epic 5 with real Epic 2                │
│ Dev 2 → Dev 3: Replace mocked script with real Epic 4                  │
│                                                                          │
│ ALL: Integration testing, bug fixes                                     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ WEEK 9: END-TO-END TESTING                                              │
├─────────────────────────────────────────────────────────────────────────┤
│ ALL: Complete user journey testing                                      │
│ ALL: Performance testing, load testing                                  │
│ ALL: Bug fixes, polish                                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ WEEK 10-11: Epic 6 - Editor Integration                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ Dev 3: Lead - Zapcut editor integration                                 │
│ Dev 1: Support - Video download optimization                            │
│ Dev 2: Support - UI polish, error handling                              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ WEEK 12: PRODUCTION DEPLOYMENT                                          │
├─────────────────────────────────────────────────────────────────────────┤
│ ALL: Final testing, security audit, production deployment               │
└─────────────────────────────────────────────────────────────────────────┘
```

**Total Duration:** 12 weeks (3 months)

---

## Daily Standups Structure

### Format
15 minutes, same time daily

### Questions
1. **What did you complete yesterday?**
2. **What are you working on today?**
3. **Any blockers or dependencies on other devs?**
4. **Which files are you modifying today?** (prevents merge conflicts)

### Example Standup (Week 4):

**Dev 1 (Epic 2):**
- Yesterday: Completed Google OAuth integration
- Today: Building brand CRUD endpoints
- Blockers: None
- Files: `src/api/routes/brands.py`, `src/database/schema.sql`

**Dev 2 (Epic 3):**
- Yesterday: Built chat UI components
- Today: Integrating OpenAI for AI responses
- Blockers: None
- Files: `src/api/routes/chat.py`, `src/pages/ChatPage.tsx`

**Dev 3 (Epic 5):**
- Yesterday: Set up RQ worker infrastructure
- Today: Integrating Replicate Sora API
- Blockers: None
- Files: `src/tasks/video_generation.py`, `src/utils/replicate_client.py`

---

## Merge Conflict Prevention

### Shared Files to Coordinate

| File | Epic 1 | Epic 2 | Epic 3 | Epic 4 | Epic 5 | Epic 6 |
|------|--------|--------|--------|--------|--------|--------|
| `database/schema.sql` | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| `alembic/versions/*` | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| `api/routes/__init__.py` | - | ✓ | ✓ | ✓ | ✓ | - |
| `stores/index.ts` | - | ✓ | ✓ | ✓ | ✓ | ✓ |
| `App.tsx` (routes) | - | ✓ | ✓ | ✓ | ✓ | ✓ |

### Coordination Strategy

**1. Database Schema (Epic 1 Week 2):**
- Dev 1 creates initial schema with ALL tables (placeholders for future epics)
- Devs 2 & 3 only ADD fields, never remove or rename

**Example initial schema:**
```sql
-- Epic 1: Create ALL tables upfront (minimal columns)
CREATE TABLE users (id, email, created_at);
CREATE TABLE brands (id, user_id, title, created_at);
CREATE TABLE ad_projects (id, user_id, brand_id, status, created_at);
CREATE TABLE chat_messages (id, ad_project_id, role, content, created_at);
CREATE TABLE scripts (id, ad_project_id, storyline, scenes, created_at);
CREATE TABLE generation_jobs (id, ad_project_id, job_type, status, created_at);
```

**2. Migration Naming Convention:**
```
alembic/versions/
├── 001_epic1_initial_schema.py
├── 002_epic2_add_auth_fields.py
├── 003_epic3_add_chat_fields.py
├── 004_epic4_add_script_fields.py
├── 005_epic5_add_generation_fields.py
```

**3. API Routes:**
Each epic gets its own router file:
```
api/routes/
├── auth.py         (Epic 2)
├── brands.py       (Epic 2)
├── projects.py     (Epic 3)
├── chat.py         (Epic 3)
├── scripts.py      (Epic 4)
├── generation.py   (Epic 5)
```

Only one developer touches each file.

**4. Frontend Stores:**
Each epic gets its own store:
```
stores/
├── authStore.ts           (Epic 2 - Dev 1)
├── brandStore.ts          (Epic 2 - Dev 1)
├── adProjectStore.ts      (Epic 3 - Dev 2)
├── generationStore.ts     (Epic 5 - Dev 3)
```

**5. Frontend Routes:**
Use separate route files:
```
routes/
├── authRoutes.tsx         (Epic 2 - Dev 1)
├── brandRoutes.tsx        (Epic 2 - Dev 1)
├── chatRoutes.tsx         (Epic 3 - Dev 2)
├── scriptRoutes.tsx       (Epic 4 - Dev 2)
├── generationRoutes.tsx   (Epic 5 - Dev 3)
```

Then combine in `App.tsx` during integration week.

---

## Git Branching Strategy

### Main Branches
```
main (protected - only merge during integration)
├── epic-1-infrastructure  (Weeks 1-2, all devs)
├── epic-2-auth-brands     (Weeks 3-5, Dev 1)
├── epic-3-chat            (Weeks 3-5, Dev 2)
├── epic-4-script          (Weeks 6-7, Dev 2)
└── epic-5-video           (Weeks 3-7, Dev 3)
```

### Merge Schedule

**Week 2 End:**
```
epic-1-infrastructure → main (all devs review)
```

**Week 5 End:**
```
epic-2-auth-brands → main (Dev 1 merges, others review)
```

**Week 8 (Integration Week):**
```
epic-3-chat → main (rebase on latest main first)
epic-4-script → main (rebase on latest main first)
epic-5-video → main (rebase on latest main first)
```

**Week 11 End:**
```
epic-6-editor → main
```

### Daily Workflow (During Parallel Development)

**Morning (before standup):**
```bash
# Pull latest from your epic branch
git checkout epic-3-chat
git pull origin epic-3-chat

# Check if Epic 2 merged (after Week 5)
git log main..epic-2-auth-brands
# If merged, rebase
git rebase main
```

**During Day:**
```bash
# Commit frequently to your epic branch
git add .
git commit -m "feat(chat): add OpenAI integration"
git push origin epic-3-chat
```

**End of Week:**
- Push all commits
- Create PR for review (don't merge yet)
- Other devs review PR asynchronously

---

## Code Review Strategy

### PR Review Assignments

| Epic/Week | Author | Primary Reviewer | Secondary Reviewer |
|-----------|--------|------------------|-------------------|
| Epic 1 | All | All review all | N/A |
| Epic 2 (Wk 5) | Dev 1 | Dev 2 | Dev 3 |
| Epic 3 (Wk 5) | Dev 2 | Dev 1 | Dev 3 |
| Epic 4 (Wk 7) | Dev 2 | Dev 1 | Dev 3 |
| Epic 5 (Wk 7) | Dev 3 | Dev 1 | Dev 2 |
| Epic 6 (Wk 11) | Dev 3 | Dev 1 | Dev 2 |

### Review Checklist

**Backend Code:**
- [ ] API endpoints have authentication
- [ ] Database queries use parameterized statements (SQL injection prevention)
- [ ] Error handling present
- [ ] Tests included
- [ ] Logging added
- [ ] Follows project structure

**Frontend Code:**
- [ ] Components are properly typed (TypeScript)
- [ ] State management follows pattern (Zustand)
- [ ] Error states handled
- [ ] Loading states shown
- [ ] Responsive design
- [ ] Follows design system (glassmorphism)

**Database Migrations:**
- [ ] Migration is reversible (has downgrade)
- [ ] No breaking changes to existing columns
- [ ] Indexes added for foreign keys
- [ ] Tested locally

---

## Testing Ownership

| Test Type | Epic 1 | Epic 2 | Epic 3 | Epic 4 | Epic 5 | Epic 6 |
|-----------|--------|--------|--------|--------|--------|--------|
| Unit Tests (Backend) | Dev 2 | Dev 1 | Dev 2 | Dev 2 | Dev 3 | Dev 3 |
| Unit Tests (Frontend) | Dev 3 | Dev 1 | Dev 2 | Dev 2 | Dev 3 | Dev 3 |
| Integration Tests | All | Dev 1 | Dev 2 | Dev 2 | Dev 3 | Dev 3 |
| E2E Tests | Dev 2 | Dev 1 | All | All | All | All |

### Test Coverage Targets
- Backend: > 80%
- Frontend: > 70%
- E2E: All critical paths (signup → video generation)

---

## Communication Channels

### Slack Channels (Recommended)

**#zapcut-dev** - General development discussion
**#zapcut-epic-1** - Infrastructure questions
**#zapcut-epic-2** - Auth & brands
**#zapcut-epic-3-4** - Chat & script generation
**#zapcut-epic-5** - Video generation pipeline
**#zapcut-deployments** - Deployment notifications
**#zapcut-bugs** - Bug reports and tracking

### Weekly Sync (1 hour)

**Agenda:**
1. **Demo (20 min):** Each dev shows what they built this week
2. **Integration Planning (20 min):** Discuss upcoming integration points
3. **Blockers (10 min):** Discuss any blockers or technical decisions needed
4. **Next Week Planning (10 min):** Confirm what everyone is working on

---

## Risk Mitigation

### Risk: Developer gets blocked waiting for another's epic

**Mitigation:**
- Use mocks extensively
- Define interface contracts early (API schemas, data models)
- Weekly demos keep everyone aligned
- Integration week has buffer for issues

### Risk: Merge conflicts during integration

**Mitigation:**
- Separate files per epic (routes, stores, migrations)
- Naming conventions prevent overlap
- Daily standup announces file changes
- Integration week dedicated to merging

### Risk: One epic takes longer than expected

**Mitigation:**
- Weekly check-ins on progress
- Can shift resources if needed (e.g., Dev 1 helps Dev 3 with Epic 5 after Epic 2 done)
- Buffer week in timeline (Week 12)

### Risk: External API failures (OpenAI, Replicate)

**Mitigation:**
- Mock API responses for development
- Test with real APIs in integration week
- Have fallback strategies documented

---

## Success Metrics

### Week 2 Checkpoint (Epic 1)
✅ Infrastructure deployed to staging
✅ Sample API responds to health check
✅ Database migrations run successfully
✅ Frontend builds for all platforms

### Week 5 Checkpoint (Epic 2 Complete, Epic 3/5 50%)
✅ Users can signup and create brands in staging
✅ Chat UI functional with mocked auth
✅ Video generation pipeline tested with sample videos

### Week 8 Checkpoint (Integration)
✅ All epics merged to main
✅ End-to-end flow works: Signup → Brand → Chat → Script → Video
✅ No critical bugs

### Week 12 Checkpoint (Launch)
✅ Production deployment successful
✅ Complete user journey tested in production
✅ Monitoring showing green metrics
✅ Team can create videos end-to-end

---

## Summary

**Key Success Factors:**

1. ✅ **Epic 1 done right** - Don't rush infrastructure
2. ✅ **Mocking enables parallelization** - Fake it till integration week
3. ✅ **Daily communication** - Prevents conflicts and blockers
4. ✅ **Separate files** - Minimize merge conflicts
5. ✅ **Integration week buffer** - Time to fix the unexpected
6. ✅ **Incremental testing** - Deploy epics to staging as completed
7. ✅ **Clear ownership** - Each dev owns their epic's success

**Timeline Summary:**
- Weeks 1-2: Epic 1 (all together)
- Weeks 3-7: Parallel development (with mocks)
- Week 8: Integration sprint
- Week 9: E2E testing
- Weeks 10-11: Epic 6 + polish
- Week 12: Production deployment

**Total:** 12 weeks to launch 🚀
