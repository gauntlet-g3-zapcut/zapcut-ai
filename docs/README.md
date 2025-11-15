# Zapcut AI Documentation

## Overview
This directory contains comprehensive documentation for the Zapcut AI video generation platform—a monorepo containing frontend (Electron app), backend (FastAPI), infrastructure, and supporting services.

---

## Document Structure

### Product Requirements (PRD)
Located in `/docs/PRD/`—these documents define **what** we're building and **why**.

1. **[01-product-vision.md](PRD/01-product-vision.md)**
   - Mission statement and value proposition
   - Market opportunity and competitive landscape
   - Success criteria and design principles
   - Product roadmap (MVP → Enterprise)

2. **[02-user-personas.md](PRD/02-user-personas.md)**
   - Primary Persona: Brand Marketer (Sarah)
   - Secondary Persona: Music Producer (Alex)
   - Tertiary Persona: Agency Creative Director (Marcus)
   - Anti-personas (who we're NOT targeting)

3. **[03-user-flows.md](PRD/03-user-flows.md)**
   - First-time user onboarding flow
   - Returning user (Creative Bible reuse)
   - Batch variation generation
   - Error handling and edge cases
   - Metrics tracking

4. **[04-features.md](PRD/04-features.md)**
   - MVP features (P0 - must-have)
   - Post-MVP features (P1 - should-have)
   - Future enhancements (P2 - nice-to-have)
   - Enterprise features (P3)
   - Out of scope (what we're NOT building)

5. **[05-ui-ux-guidelines.md](PRD/05-ui-ux-guidelines.md)**
   - Design philosophy (glass morphism, single-page agent experience)
   - Color palette (yellow lightning bolt, white cursor theme)
   - Component guidelines (chat messages, progress indicators, video preview)
   - Iconography (Lucide React)
   - Animations and accessibility

6. **[06-content-policy.md](PRD/06-content-policy.md)**
   - Prohibited content (violence, nudity, drugs, hate, deepfakes, copyright)
   - Brand compliance requirements
   - Safety enforcement layers (4-layer validation)
   - User consequences for violations
   - Legal and regulatory compliance

7. **[07-success-metrics.md](PRD/07-success-metrics.md)**
   - MVP success criteria (48-hour checkpoint)
   - Product quality metrics (visual consistency, audio-visual sync)
   - Performance metrics (generation speed, uptime, cost per video)
   - User adoption metrics (sign-up conversion, activation, retention)
   - Business metrics (MAU, revenue, CAC, LTV)

---

### Technical Architecture
Located in `/docs/Architecture.md`—this document defines **how** we're building it.

**[Architecture.md](Architecture.md)** contains:

#### System Design
- High-level architecture diagram
- Technology stack (frontend, backend, infrastructure, AI services)
- Application directory structure

#### Database
- Complete PostgreSQL schema
  - Users, Projects, Assets
  - Creative Bibles, Generated Ads
  - Generation Jobs, Safety Violations
- Indexes and constraints

#### API Design
- RESTful endpoint contracts
- Authentication (AWS Cognito JWT)
- Request/response schemas
- Error handling

#### Multi-Agent System
- 6 specialized AI agents:
  1. Master Orchestrator (workflow management)
  2. Story Structuring Agent (narrative planning)
  3. Style & Brand Consistency Agent (Creative Bible generation)
  4. Safety Validation Agent (content moderation)
  5. Prompt Synthesis Agent (Sora/Suno prompt creation)
  6. Continuity Back-Propagation Agent (scene consistency)
- Agent communication protocols
- State management

#### Video Generation Pipeline
- End-to-end workflow (4-5 minute generation)
- Celery task implementation
- Parallel processing (Sora + Suno)
- FFmpeg video composition

#### Infrastructure as Code
- Terraform configuration for AWS
  - Cognito (authentication)
  - RDS PostgreSQL (database)
  - S3 + CloudFront (storage + CDN)
  - Elastic Beanstalk (API servers)
  - SQS (task queue)
- Deployment strategy (CI/CD with GitHub Actions)

#### Security & Monitoring
- Authentication and authorization
- Data protection and encryption
- Content safety enforcement
- Observability (metrics, logging, alerts)
- Cost optimization strategies

---

## Quick Reference

### For Product Managers
Start here:
- [Product Vision](PRD/01-product-vision.md) → Understand the "why"
- [User Personas](PRD/02-user-personas.md) → Know the target users
- [Features](PRD/04-features.md) → See what's being built
- [Success Metrics](PRD/07-success-metrics.md) → Track progress

### For Designers
Start here:
- [UI/UX Guidelines](PRD/05-ui-ux-guidelines.md) → Design system and components
- [User Flows](PRD/03-user-flows.md) → Understand user journey
- [Product Vision](PRD/01-product-vision.md) → Grasp design principles

### For Engineers
Start here:
- [Architecture](Architecture.md) → Complete technical design
- [Features](PRD/04-features.md) → Implementation requirements
- [Content Policy](PRD/06-content-policy.md) → Safety constraints

### For Marketing/Sales
Start here:
- [Product Vision](PRD/01-product-vision.md) → Value proposition
- [User Personas](PRD/02-user-personas.md) → Target audience
- [Success Metrics](PRD/07-success-metrics.md) → KPIs and benchmarks

---

## Development Workflow

### 1. Feature Development
```
1. Read relevant PRD docs → Understand requirements
2. Review Architecture.md → Understand technical approach
3. Create feature branch → Implement
4. Test against acceptance criteria (from Features.md)
5. Submit PR with links to relevant PRD sections
```

### 2. Architecture Decisions
```
1. Propose change in Architecture.md
2. Create ADR (Architecture Decision Record) in /docs/decisions/
3. Review with team
4. Update relevant PRD docs if user-facing impact
```

### 3. Documentation Updates
```
- PRD docs updated when: requirements change, features added, user feedback
- Architecture.md updated when: tech stack changes, new services, major refactors
- Reviewed quarterly or before major releases
```

---

## Monorepo Structure

```
zapcut-ai/
├── app/                    # Electron frontend (React + TypeScript)
├── backend/                # FastAPI backend (Python)
├── database/               # Database migrations (Alembic)
├── infrastructure/         # Terraform IaC (AWS)
├── queue/                  # Celery workers (video generation)
├── s3/                     # S3 bucket configuration
├── website/                # Marketing website (NOT part of app)
└── docs/                   # This directory
    ├── PRD/                # Product requirements
    ├── Architecture.md     # Technical architecture
    └── README.md           # This file
```

---

## Key Technologies

### Frontend
- **Electron** + **React 18** + **TypeScript**
- **Zustand** (state management)
- **Tailwind CSS** + **Shadcn UI** (glass morphism design)
- **Lucide React** (icons)
- **Vite** (build tool)

### Backend
- **FastAPI** (Python 3.11+)
- **SQLAlchemy 2.0** (async ORM)
- **Celery** + **Redis** (task queue)
- **PostgreSQL 16** (database)

### AI Services
- **Claude 3.5 Sonnet** (orchestration, scriptwriting)
- **Sora** via Replicate (video generation)
- **Suno** via Replicate (music generation)
- **DALL-E 3** (reference image generation)

### Infrastructure (AWS)
- **Cognito** (authentication)
- **RDS** (PostgreSQL)
- **S3 + CloudFront** (storage + CDN)
- **Elastic Beanstalk** (API servers)
- **SQS** (message queue)

---

## Key Concepts

### Creative Bible
A reusable style template that locks brand DNA:
- Visual style, colors, lighting, camera movement
- Energy level and motion patterns
- Reference images (4 DALL-E generated images)
- Enables 40% faster + cheaper regeneration

### Multi-Agent Orchestration
Rather than one monolithic AI call, we use 6 specialized agents:
1. Orchestrator → Guides user through stages
2. Story Agent → Plans narrative structure
3. Style Agent → Ensures brand consistency
4. Safety Agent → Content moderation
5. Prompt Agent → Optimizes Sora/Suno prompts
6. Continuity Agent → Maintains visual consistency across scenes

### Back-Propagation for Continuity
Scene N uses the last frame of Scene N-1 as input to maintain:
- Color palette consistency
- Lighting continuity
- Product appearance
- Smooth narrative flow

---

## Success Metrics Summary

### MVP Gate (48 Hours)
- ✅ 2+ complete video ads generated
- ✅ Audio-visual sync working
- ✅ Visual consistency across scenes
- ✅ <5 minute generation time
- ✅ Deployed and accessible

### 6-Month Targets
- **Quality**: 90%+ visual consistency score
- **Speed**: <3 minutes generation time
- **Cost**: <$1.50 per video
- **Adoption**: 2,000 MAU, 15,000 videos/month
- **Retention**: 25%+ D7 retention

---

## Contributing

### Documentation Updates
- **PRD changes**: Require PM approval
- **Architecture changes**: Require tech lead approval
- **Typos/clarifications**: Can be fixed directly

### Versioning
- PRD docs versioned by date in footer
- Architecture.md versioned by date in footer
- Major changes logged in version history

---

## Contact & Support

### Internal Team
- **Product**: PM team for PRD questions
- **Engineering**: Tech lead for Architecture questions
- **Design**: Design lead for UI/UX questions

### External Resources
- **Replicate Docs**: https://replicate.com/docs
- **Anthropic Claude**: https://docs.anthropic.com/
- **AWS Documentation**: https://docs.aws.amazon.com/

---

## Change Log

### November 15, 2025
- Initial documentation created
- PRD suite (7 documents)
- Architecture.md (complete technical spec)
- README.md (this file)

### Future Updates
- Will be tracked here as documentation evolves
- Major version bumps noted with summary of changes

---

**Last Updated**: November 15, 2025  
**Status**: Active Development  
**Maintainers**: Product + Engineering Teams  
**Next Review**: December 1, 2025

