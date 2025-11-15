# Epic Allocation Strategies - 3 Developer Team

This document presents **3 different allocation strategies** for dividing epics among developers, with pros/cons and recommendations.

---

## Strategy Overview

| Strategy | Approach | Best For | Risk Level |
|----------|----------|----------|------------|
| **Option A** | Track-Based (DevOps/AI/Video) | Specialized teams | Low |
| **Option B** | Sequential Epic Ownership | Full-stack generalists | Medium |
| **Option C** | Feature-Based Pairing | Learning & knowledge sharing | Low-Medium |

---

## OPTION A: Track-Based Allocation (RECOMMENDED)

### Concept
Developers specialize in tracks that span multiple epics.

### Team Structure

```
Developer 1: INFRASTRUCTURE & FOUNDATION TRACK
├─ Epic 1: Infrastructure & Deployment (Lead, 100%)
├─ Epic 2: Authentication & Brands (Lead, 100%)
├─ Epic 3-6: Support role (DB, Auth, Deployment)
└─ Skills: DevOps, AWS, Backend, PostgreSQL

Developer 2: AI & CONVERSATION TRACK
├─ Epic 1: Backend CI/CD (30%)
├─ Epic 2: Frontend for auth/brands (30%)
├─ Epic 3: AI Chat & Requirements (Lead, 100%)
├─ Epic 4: Script Generation (Lead, 100%)
├─ Epic 5: AI orchestration support (20%)
└─ Skills: Full-stack, OpenAI, LLM, Python/React

Developer 3: VIDEO & EDITOR TRACK
├─ Epic 1: Frontend CI/CD (30%)
├─ Epic 2: Frontend for auth/brands (30%)
├─ Epic 5: Video Generation Pipeline (Lead, 100%)
├─ Epic 6: Editor Integration (Lead, 100%)
└─ Skills: Full-stack, FFmpeg, Video AI, Electron
```

### Timeline (12 Weeks)

#### Weeks 1-2: Epic 1 (ALL TOGETHER)

| Developer | Allocation | Tasks |
|-----------|------------|-------|
| **Dev 1** | 100% Epic 1 | AWS infra, Terraform, RDS, S3, ECS |
| **Dev 2** | 100% Epic 1 | Backend CI/CD, Docker, Alembic, health checks |
| **Dev 3** | 100% Epic 1 | Frontend CI/CD, Electron builds, Sentry |

**Why together:** Infrastructure is blocking - faster completion enables parallelization.

---

#### Weeks 3-5: Parallel Development

| Developer | Primary Epic | Allocation | Supporting |
|-----------|--------------|------------|------------|
| **Dev 1** | Epic 2 (Auth & Brands) | 80% | 20% support Dev 2/3 with DB/deployment |
| **Dev 2** | Epic 3 (AI Chat) | 100% | Mocks Dev 1's auth/brands |
| **Dev 3** | Epic 5 (Video Pipeline) | 100% | Mocks Dev 1's auth/brands + Dev 2's script |

**Dev 1 Deliverables (Epic 2):**
- ✅ Backend: OAuth, JWT, users/brands tables, CRUD APIs, S3 uploads
- ✅ Frontend: Landing, login/signup, brands dashboard, create/edit modals
- ✅ Tests: Auth flow, brand CRUD, authorization
- ✅ Deploy to staging

**Dev 2 Deliverables (Epic 3):**
- ✅ Backend: Ad projects, chat messages tables, OpenAI integration, 5-question flow
- ✅ Frontend: Chat UI, message bubbles, typing indicator, progress tracking
- ✅ Uses MOCK auth (hardcoded user/brand)
- ✅ Deploy to staging with mocks

**Dev 3 Deliverables (Epic 5):**
- ✅ Backend: RQ workers, Replicate (Sora/TTS), Suno API, FFmpeg pipeline
- ✅ Frontend: Generation status page, progress tracking, video player
- ✅ Uses MOCK auth/brands/script
- ✅ Deploy to staging with mocks

---

#### Weeks 6-7: Continue Parallel

| Developer | Primary Epic | Allocation | Supporting |
|-----------|--------------|------------|------------|
| **Dev 1** | Epic 2 complete ✅ | 40% | 60% support - help Dev 2 with Epic 4 frontend, help Dev 3 with DB optimization |
| **Dev 2** | Epic 4 (Script Gen) | 100% | Uses MOCK auth/brands from Dev 1 |
| **Dev 3** | Epic 5 (continued) | 100% | Finishing FFmpeg composition, audio mixing, testing |

**Dev 2 Deliverables (Epic 4):**
- ✅ Backend: Scripts table, OpenAI script generation, structured JSON output
- ✅ Frontend: Script review page, scene cards, regenerate UI, approve button
- ✅ Deploy to staging with mocks

**Dev 3 Deliverables (Epic 5 completion):**
- ✅ All generation jobs working
- ✅ FFmpeg composition complete
- ✅ Progress tracking accurate
- ✅ Full pipeline tested with sample data

---

#### Week 8: Integration Sprint (ALL TOGETHER)

| Developer | Allocation | Tasks |
|-----------|------------|-------|
| **Dev 1** | 100% Integration | Replace mocks in Epic 3/4/5 with real Epic 2 APIs |
| **Dev 2** | 100% Integration | Update Epic 3/4 to use real auth, provide script API for Epic 5 |
| **Dev 3** | 100% Integration | Update Epic 5 to use real auth/brands/script |

**Deliverables:**
- ✅ All mocks removed
- ✅ End-to-end flow works: Signup → Brand → Chat → Script → Video
- ✅ Integration bugs fixed
- ✅ Merged to main

---

#### Week 9: E2E Testing (ALL TOGETHER)

| Developer | Allocation | Tasks |
|-----------|------------|-------|
| **Dev 1** | 100% Testing | DB performance testing, auth edge cases, deployment verification |
| **Dev 2** | 100% Testing | AI chat flow testing, script quality testing, error handling |
| **Dev 3** | 100% Testing | Video generation testing, FFmpeg edge cases, progress accuracy |

---

#### Weeks 10-11: Epic 6 + Polish

| Developer | Primary Epic | Allocation | Supporting |
|-----------|--------------|------------|------------|
| **Dev 1** | Support | 30% | Video download optimization, S3 presigned URLs |
| **Dev 2** | Support | 30% | UI/UX polish, error handling, loading states |
| **Dev 3** | Epic 6 (Editor) | 100% | Zapcut integration, download, asset loading |

**Dev 3 Deliverables (Epic 6):**
- ✅ Download video to local
- ✅ Load into Zapcut editor
- ✅ Product images in library
- ✅ "Back to Brands" navigation
- ✅ Export verification

---

#### Week 12: Production Launch (ALL TOGETHER)

| Developer | Allocation | Tasks |
|-----------|------------|-------|
| **Dev 1** | 100% Launch | Final infrastructure checks, production deployment, monitoring |
| **Dev 2** | 100% Launch | Final testing, bug fixes, documentation |
| **Dev 3** | 100% Launch | Final testing, cross-platform verification, user acceptance |

---

### Epic Ownership Matrix (Option A)

| Epic | Lead | Support | Backend | Frontend | Testing |
|------|------|---------|---------|----------|---------|
| Epic 1 | All | N/A | Dev 1 + 2 | Dev 3 | All |
| Epic 2 | Dev 1 | Dev 2/3 | Dev 1 | Dev 1 | Dev 1 |
| Epic 3 | Dev 2 | Dev 1 | Dev 2 | Dev 2 | Dev 2 |
| Epic 4 | Dev 2 | Dev 1 | Dev 2 | Dev 2 | Dev 2 |
| Epic 5 | Dev 3 | Dev 1 | Dev 3 | Dev 3 | Dev 3 |
| Epic 6 | Dev 3 | Dev 1/2 | Dev 3 | Dev 3 | Dev 3 |

### Pros & Cons

**Pros:**
- ✅ Clear ownership and accountability
- ✅ Developers become experts in their track
- ✅ Minimal context switching
- ✅ Efficient parallelization (Weeks 3-7)
- ✅ Natural skill development paths
- ✅ Reduced merge conflicts (separate domains)

**Cons:**
- ❌ Knowledge silos (Dev 3 doesn't know auth)
- ❌ Risk if one developer leaves
- ❌ Requires specific skill sets upfront

**Mitigation:**
- Pair programming during integration week
- Code reviews across all PRs
- Documentation for each epic
- Weekly demos to share knowledge

---

## OPTION B: Sequential Epic Ownership

### Concept
Each developer owns 2 complete epics sequentially (full-stack).

### Team Structure

```
Developer 1: Epic 1 + Epic 2 (Foundation)
Developer 2: Epic 3 + Epic 4 (AI/Script)
Developer 3: Epic 5 + Epic 6 (Video/Editor)
```

### Timeline (16 Weeks - LONGER)

#### Phase 1: Weeks 1-2
**Epic 1 - ALL TOGETHER** (same as Option A)

#### Phase 2: Weeks 3-7
```
Dev 1: Epic 2 (Auth & Brands) - 100%
Dev 2: Epic 3 (Chat) - 100%, WAITING for Epic 2
Dev 3: Epic 5 (Video) - 100%, WAITING for Epic 2 + 4
```

**Problem:** Dev 2 and 3 are BLOCKED waiting for Epic 2.

**Solution:** They can:
- Use mocks (same as Option A)
- Help Dev 1 with Epic 2 (but then not truly sequential)
- Work on other projects (waste of time)

#### Phase 3: Weeks 8-11
```
Dev 1: Done, helping others
Dev 2: Epic 4 (Script) - 100%
Dev 3: Epic 5 (Video) - 100%, WAITING for Epic 4
```

#### Phase 4: Weeks 12-15
```
Dev 1: Done
Dev 2: Done
Dev 3: Epic 6 (Editor) - 100%
```

#### Phase 5: Week 16
Integration testing - ALL

### Pros & Cons

**Pros:**
- ✅ Each developer becomes full-stack expert
- ✅ No knowledge silos
- ✅ Each developer owns complete features
- ✅ Clear handoffs between epics

**Cons:**
- ❌ 4 weeks LONGER (16 weeks vs 12 weeks)
- ❌ Massive blocking dependencies
- ❌ Poor resource utilization (devs idle waiting)
- ❌ Late integration means late bug discovery
- ❌ High risk - if Epic 2 is late, everything cascades

**Recommendation:** ❌ **NOT RECOMMENDED** unless timeline is flexible and team learning is top priority.

---

## OPTION C: Feature-Based Pairing

### Concept
Developers work in pairs on epics, rotating pairs.

### Team Structure

```
Pair Rotation:
Weeks 1-2:   All 3 on Epic 1
Weeks 3-5:   Pair A (Dev 1+2) on Epic 2, Dev 3 on Epic 5
Weeks 6-7:   Pair B (Dev 2+3) on Epic 3+4, Dev 1 supports
Weeks 8-9:   Integration + Testing
Weeks 10-11: Pair C (Dev 1+3) on Epic 6, Dev 2 polishes
```

### Timeline (12 Weeks)

#### Weeks 1-2: Epic 1 (ALL)
Same as Option A.

#### Weeks 3-5: Paired Development

| Pair | Epic | Tasks |
|------|------|-------|
| **Dev 1 + Dev 2** | Epic 2 | Dev 1: Backend, Dev 2: Frontend |
| **Dev 3 (Solo)** | Epic 5 | Uses mocked Epic 2/4 dependencies |

**Benefits:**
- Dev 2 learns auth from Dev 1
- Epic 2 completes faster (2 people)
- Knowledge sharing built-in

#### Weeks 6-7: Rotated Pairs

| Pair | Epic | Tasks |
|------|------|-------|
| **Dev 2 + Dev 3** | Epic 3 + 4 | Dev 2: AI backend, Dev 3: Frontend |
| **Dev 1 (Solo)** | Support | DB optimization, deployment, help others |

**Benefits:**
- Dev 3 learns AI from Dev 2
- Epic 3/4 complete faster
- Dev 1 unblocked to support

#### Weeks 8-9: Integration + Testing (ALL)
Same as Option A.

#### Weeks 10-11: Final Pair

| Pair | Epic | Tasks |
|------|------|-------|
| **Dev 1 + Dev 3** | Epic 6 | Dev 1: Backend download APIs, Dev 3: Electron integration |
| **Dev 2 (Solo)** | Polish | UI/UX refinements, bug fixes |

#### Week 12: Launch (ALL)
Same as Option A.

### Pairing Matrix

| Epic | Driver (Primary) | Navigator (Support) |
|------|------------------|---------------------|
| Epic 1 | All | All |
| Epic 2 | Dev 1 | Dev 2 |
| Epic 3 | Dev 2 | Dev 3 |
| Epic 4 | Dev 2 | Dev 3 |
| Epic 5 | Dev 3 | Dev 1 (async support) |
| Epic 6 | Dev 3 | Dev 1 |

### Pros & Cons

**Pros:**
- ✅ Knowledge sharing built-in
- ✅ Reduced silos
- ✅ Faster epic completion (2 people)
- ✅ Built-in code review
- ✅ Same 12-week timeline
- ✅ Lower risk of blocking

**Cons:**
- ❌ Requires co-located or synchronous work
- ❌ May slow down if pair dynamics don't work
- ❌ Less parallel work overall
- ❌ Communication overhead

**Recommendation:** ✅ **GOOD OPTION** if team is co-located and values learning.

---

## Comparison Matrix

| Factor | Option A (Track-Based) | Option B (Sequential) | Option C (Pairing) |
|--------|----------------------|----------------------|-------------------|
| **Timeline** | 12 weeks ✅ | 16 weeks ❌ | 12 weeks ✅ |
| **Knowledge Silos** | High ❌ | None ✅ | Low ✅ |
| **Parallelization** | High ✅ | None ❌ | Medium ✅ |
| **Blocking Risk** | Low ✅ | High ❌ | Low ✅ |
| **Skill Requirements** | Specialized ⚠️ | Full-stack ✅ | Mixed ✅ |
| **Onboarding Time** | Medium | Low | Medium |
| **Code Quality** | Good | Good | High ✅ |
| **Team Learning** | Low | High | High ✅ |
| **Flexibility** | High ✅ | Low ❌ | Medium |

---

## RECOMMENDATION: Hybrid of Option A + C

### Recommended Approach

**Use Track-Based allocation (Option A) WITH pairing on complex epics**

```
Week 1-2:   Epic 1 - ALL TOGETHER (pair naturally)

Week 3-5:   PARALLEL
            - Dev 1: Epic 2 (solo, straightforward auth)
            - Dev 2+3: Epic 3 (PAIR, complex AI)
            - Dev 3 also: Epic 5 (async, mocked dependencies)

Week 6-7:   PARALLEL
            - Dev 1: Support (solo)
            - Dev 2: Epic 4 (solo, extension of Epic 3)
            - Dev 3: Epic 5 (solo, video pipeline)

Week 8:     Integration - ALL TOGETHER (pair naturally)

Week 9:     Testing - ALL TOGETHER (pair naturally)

Week 10-11: Epic 6
            - Dev 1+3: PAIR on editor integration
            - Dev 2: Polish (solo)

Week 12:    Launch - ALL TOGETHER
```

### Why This Hybrid Works

✅ **Fast timeline** (12 weeks)
✅ **Knowledge sharing** on complex epics (Epic 3, 6)
✅ **Efficient parallelization** (Weeks 3-7)
✅ **Reduced silos** (pairing on 2-3 epics)
✅ **Clear ownership** (tracks prevent confusion)
✅ **Flexibility** (can adjust pairing based on complexity)

---

## Detailed Work Breakdown (Recommended Hybrid)

### Epic 1: Infrastructure (Weeks 1-2)
**All 3 developers - Natural collaboration**

| Component | Owner | Support |
|-----------|-------|---------|
| AWS Infrastructure | Dev 1 | - |
| Backend CI/CD | Dev 2 | Dev 1 |
| Frontend CI/CD | Dev 3 | - |
| Database Setup | Dev 1 | Dev 2 |
| Monitoring | Dev 1 | Dev 2, 3 |

---

### Epic 2: Auth & Brands (Weeks 3-5)
**Dev 1 solo - 100%**

| Component | Owner | Hours |
|-----------|-------|-------|
| Database schema (users, brands) | Dev 1 | 8h |
| OAuth integration | Dev 1 | 16h |
| JWT system | Dev 1 | 12h |
| Brand CRUD APIs | Dev 1 | 16h |
| S3 image upload | Dev 1 | 12h |
| Frontend pages | Dev 1 | 24h |
| Testing | Dev 1 | 12h |
| **Total** | | **~100h (2.5 weeks)** |

---

### Epic 3: AI Chat (Weeks 3-5)
**Dev 2 (lead) + Dev 3 (pair) - 70/30%**

| Component | Lead | Pair | Hours |
|-----------|------|------|-------|
| Database schema | Dev 2 | Dev 3 reviews | 6h |
| OpenAI integration | Dev 2 | Dev 3 | 20h |
| 5-question logic | Dev 2 | Dev 3 | 16h |
| Chat backend APIs | Dev 2 | - | 12h |
| Chat UI components | Dev 3 | Dev 2 | 20h |
| State management | Dev 3 | - | 8h |
| Testing | Dev 2 | Dev 3 | 12h |
| **Total** | | | **~94h (2.4 weeks)** |

**Why pair:** Complex AI logic, knowledge sharing on OpenAI

---

### Epic 4: Script Generation (Weeks 6-7)
**Dev 2 solo - 100%**

| Component | Owner | Hours |
|-----------|-------|-------|
| Scripts table | Dev 2 | 4h |
| Script generation (OpenAI) | Dev 2 | 20h |
| Script review UI | Dev 2 | 16h |
| Regeneration logic | Dev 2 | 12h |
| Testing | Dev 2 | 8h |
| **Total** | | **~60h (1.5 weeks)** |

---

### Epic 5: Video Pipeline (Weeks 3-7)
**Dev 3 solo - 100%**

| Component | Owner | Hours |
|-----------|-------|-------|
| RQ worker setup | Dev 3 | 12h |
| Replicate integration (Sora) | Dev 3 | 24h |
| Replicate integration (TTS) | Dev 3 | 12h |
| Suno API integration | Dev 3 | 12h |
| FFmpeg pipeline | Dev 3 | 32h |
| Progress tracking | Dev 3 | 12h |
| Frontend UI | Dev 3 | 20h |
| Testing | Dev 3 | 16h |
| **Total** | | **~140h (3.5 weeks)** |

---

### Epic 6: Editor Integration (Weeks 10-11)
**Dev 3 (lead) + Dev 1 (pair) - 70/30%**

| Component | Lead | Pair | Hours |
|-----------|------|------|-------|
| Download video logic | Dev 3 | Dev 1 | 12h |
| Zapcut integration | Dev 3 | - | 20h |
| Backend download APIs | Dev 1 | - | 8h |
| Product image loading | Dev 3 | - | 12h |
| Navigation | Dev 3 | - | 8h |
| Testing | Dev 3 | Dev 1 | 12h |
| **Total** | | | **~72h (1.8 weeks)** |

**Why pair:** Dev 1 helps with backend download optimization

---

## Sprint Planning Template

### Sprint 1 (Weeks 1-2): Epic 1

**Goal:** Infrastructure deployed and operational

**Dev 1 Commits:**
- [ ] Terraform scripts for all AWS resources
- [ ] RDS PostgreSQL provisioned
- [ ] S3 buckets created
- [ ] Secrets Manager configured

**Dev 2 Commits:**
- [ ] Dockerfile for FastAPI
- [ ] GitHub Actions backend workflow
- [ ] Alembic migration system
- [ ] Health check endpoints

**Dev 3 Commits:**
- [ ] Electron builder config
- [ ] GitHub Actions frontend workflow
- [ ] Auto-update setup
- [ ] Sentry integration

**Demo:** Deploy sample API to staging

---

### Sprint 2 (Weeks 3-5): Epic 2 + Epic 3

**Goal:** Users can signup and chat with AI

**Dev 1 Commits (Epic 2):**
- [ ] OAuth + JWT working
- [ ] Users can create brands
- [ ] Image upload to S3 works
- [ ] Brands dashboard functional

**Dev 2 Commits (Epic 3):**
- [ ] Chat interface working
- [ ] AI responds to messages
- [ ] 5-question flow complete
- [ ] Requirements extracted

**Dev 3 Commits (Epic 3 + 5):**
- [ ] Chat UI polished (pair with Dev 2)
- [ ] RQ workers running (Epic 5)
- [ ] Replicate API integrated (Epic 5)

**Demo:**
- Signup → Create brand (Dev 1)
- Chat with AI → 5 questions (Dev 2+3)

---

### Sprint 3 (Weeks 6-7): Epic 4 + Epic 5

**Goal:** Script generation and video pipeline working

**Dev 1 Commits:**
- [ ] Support Dev 2 with Epic 4 frontend
- [ ] Database optimization
- [ ] Deployment improvements

**Dev 2 Commits (Epic 4):**
- [ ] Script generation working
- [ ] Script review UI complete
- [ ] Regeneration functional

**Dev 3 Commits (Epic 5):**
- [ ] FFmpeg composition complete
- [ ] Video generation end-to-end
- [ ] Progress tracking accurate

**Demo:**
- Generate script (Dev 2)
- Generate video (Dev 3)

---

### Sprint 4 (Week 8): Integration

**Goal:** All epics working together

**All Devs:**
- [ ] Remove all mocks
- [ ] End-to-end flow working
- [ ] Integration bugs fixed
- [ ] Merged to main

**Demo:** Complete flow: Signup → Brand → Chat → Script → Video

---

### Sprint 5 (Week 9): Testing

**Goal:** Production readiness

**All Devs:**
- [ ] E2E tests pass
- [ ] Performance testing complete
- [ ] Security review done
- [ ] Bug fixes

---

### Sprint 6 (Weeks 10-11): Epic 6

**Goal:** Editor integration complete

**Dev 3 + Dev 1:**
- [ ] Video loads in Zapcut
- [ ] Export works
- [ ] Round-trip functional

**Dev 2:**
- [ ] UI polish
- [ ] Error handling
- [ ] Documentation

**Demo:** Video → Editor → Export

---

### Sprint 7 (Week 12): Launch

**Goal:** Production deployment

**All Devs:**
- [ ] Production deployment
- [ ] Monitoring operational
- [ ] Launch checklist complete

---

## Final Recommendation

### **Use Hybrid Option A+C:**

1. **Track-based ownership** for clear accountability
2. **Pairing on complex epics** (Epic 3, 6) for knowledge sharing
3. **Mocking for parallelization** during weeks 3-7
4. **Integration week** for replacing mocks
5. **All-hands for infrastructure and launch**

### Timeline: 12 weeks

### Expected Outcome:
- ✅ Production-ready system in 3 months
- ✅ Each developer has deep expertise in their track
- ✅ Team has shared knowledge of complex components
- ✅ Minimal blocking, maximum parallelization
- ✅ High code quality through pairing and reviews

---

## Questions & Answers

**Q: What if we only have 2 developers?**
**A:** Use Option A but extend timeline to 16-18 weeks:
- Dev 1: Epic 1 + Epic 2 + Epic 6 support
- Dev 2: Epic 3 + Epic 4 (pair with Dev 1 on Epic 1)
- Both: Epic 5 together (video pipeline is complex)

**Q: What if developers are remote/async?**
**A:** Use Option A (Track-Based) with minimal pairing:
- Clear API contracts defined upfront
- More frequent integration (Week 5, 7, 8)
- Async code reviews instead of pairing

**Q: What if one epic takes much longer?**
**A:** Reallocate after Week 5:
- If Epic 2 is slow → Dev 2 helps Dev 1
- If Epic 5 is slow → Dev 1 helps Dev 3
- Track-based structure makes this easy

---

**Document Status:** Complete ✅
**Recommended Strategy:** Hybrid Option A+C
**Timeline:** 12 weeks
**Next Step:** Review with team, assign developers to tracks
