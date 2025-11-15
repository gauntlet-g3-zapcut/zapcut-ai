# ⚡️ Zapcut AI

## AI-Powered Video Generation Platform

Zapcut is an end-to-end AI video generation pipeline that creates professional-quality video advertisements from natural language prompts. From prompt to publish in under 5 minutes.

### 🎯 What We Do
- **AI Video Ads**: Generate complete 30-second video ads with music, visuals, and brand consistency
- **Multi-Agent Orchestration**: 6 specialized AI agents handle scriptwriting, scene planning, video generation, music composition, and compliance
- **Creative DNA System**: Reusable "Creative Bibles" ensure brand consistency across unlimited variations
- **Direct Publishing**: One-click export to X (Twitter) and LinkedIn

---

## 📚 Documentation

### Quick Start
- **Product Overview**: See [docs/PRD/01-product-vision.md](docs/PRD/01-product-vision.md)
- **Technical Architecture**: See [docs/Architecture.md](docs/Architecture.md)
- **Complete Docs**: See [docs/README.md](docs/README.md)

### For Developers
- **Tech Stack**: Electron + React + TypeScript (frontend), FastAPI + PostgreSQL (backend)
- **AI Services**: Claude (orchestration), Sora (video), Suno (music), DALL-E (images)
- **Infrastructure**: AWS (Cognito, RDS, S3, Elastic Beanstalk, SQS)

---

## 🚀 Monorepo Structure

```
zapcut-ai/
├── app/                 # Electron desktop app (React + TypeScript + Zustand)
├── backend/             # FastAPI backend (Python) + Multi-agent system
├── database/            # PostgreSQL migrations (Alembic)
├── infrastructure/      # Terraform IaC (AWS resources)
├── queue/               # Celery workers (video generation)
├── s3/                  # S3 bucket configuration
├── website/             # Marketing website (separate from app)
└── docs/                # Complete documentation (PRDs + Architecture)
```

---

## 🛠️ Development Setup

### Prerequisites
- Node.js 20+
- Python 3.11+
- PostgreSQL 16
- FFmpeg
- AWS CLI configured

### Frontend (Electron App)
```bash
cd app
npm install
npm run dev              # Run in development mode
npm run electron:build   # Build for production (macOS)
```

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload   # Run API server
```

### Database
```bash
cd database
alembic upgrade head     # Run migrations
```

### Infrastructure (Terraform)
```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

---

## 🎨 Tech Stack Highlights

### Frontend
- **Electron**: Cross-platform desktop app
- **React 18**: UI framework with TypeScript
- **Zustand**: Global state management
- **Tailwind CSS + Shadcn**: Glass morphism design system
- **Lucide React**: Modern icon library

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy 2.0**: Async ORM
- **Celery + Redis**: Task queue for video generation
- **PostgreSQL**: Primary database

### AI Services
- **Claude 3.5 Sonnet** (Anthropic): Orchestration, creative direction
- **Sora** (Replicate): Video scene generation
- **Suno** (Replicate): Music composition
- **DALL-E 3** (OpenAI): Reference image generation

### Infrastructure
- **AWS Cognito**: Authentication
- **AWS RDS**: PostgreSQL database
- **AWS S3 + CloudFront**: Storage + CDN
- **AWS Elastic Beanstalk**: API deployment
- **AWS SQS**: Message queue

---

## 📖 Key Documentation

### Product Requirements
1. [Product Vision](docs/PRD/01-product-vision.md) - Mission, market, roadmap
2. [User Personas](docs/PRD/02-user-personas.md) - Target users and use cases
3. [User Flows](docs/PRD/03-user-flows.md) - Complete user journey
4. [Features](docs/PRD/04-features.md) - MVP and future features
5. [UI/UX Guidelines](docs/PRD/05-ui-ux-guidelines.md) - Design system
6. [Content Policy](docs/PRD/06-content-policy.md) - Safety and compliance
7. [Success Metrics](docs/PRD/07-success-metrics.md) - KPIs and targets

### Technical Architecture
- [Architecture.md](docs/Architecture.md) - Complete technical specification
  - System design and tech stack
  - Database schema
  - API contracts
  - Multi-agent system
  - Video generation pipeline
  - Infrastructure as code
  - Security and monitoring

---

## 🎯 MVP Success Criteria (48 Hours)

- ✅ Generate at least 2 complete video ads
- ✅ Audio-visual synchronization working
- ✅ Visual consistency across 3-5 scenes
- ✅ Generation time <5 minutes for 30-second ad
- ✅ Deployed and accessible via web

---

## 🚦 Current Status

**Phase**: MVP Development (Week 1)  
**Target**: Launch complete ad creative pipeline  
**Next Milestone**: 2 sample videos by Sunday

---

## 🔐 Security & Compliance

- **Content Safety**: 4-layer validation (orchestrator, safety agent, prompts, post-gen)
- **Authentication**: AWS Cognito with JWT tokens
- **Data Protection**: Encryption at rest (RDS, S3) and in transit (TLS 1.3)
- **Brand Compliance**: Automated brand asset validation
- **Legal**: FTC, ASA, GDPR, COPPA compliant

---

## 💰 Cost Optimization

**Target**: <$2.50 per 30-second video

**Breakdown**:
- Claude API: $0.15
- DALL-E (4 images): $0.40
- Sora (5 scenes): $1.50
- Suno (1 track): $0.25
- Infrastructure: $0.20

**Optimizations**:
- Creative Bible reuse (40% cost savings)
- Smart caching and batching
- S3 lifecycle policies

---

## 📊 Key Metrics

### Performance
- **Generation Speed**: <5 minutes (MVP), <3 minutes (6 months)
- **Success Rate**: 90%+ first-try generation
- **Uptime**: 99.5%+ availability

### Quality
- **Visual Consistency**: 85%+ user satisfaction (MVP), 90%+ (6 months)
- **Audio-Visual Sync**: 95%+ perfect sync

### Business
- **MAU Target**: 100 (Month 1) → 10,000 (Month 12)
- **Cost Per Video**: <$2.50 (MVP) → <$1.50 (6 months)

---

## 🤝 Contributing

### Development Workflow
1. Read relevant [PRD docs](docs/PRD/) and [Architecture.md](docs/Architecture.md)
2. Create feature branch from `main`
3. Implement with tests
4. Submit PR with links to relevant documentation
5. Code review and merge

### Documentation Updates
- PRD changes require PM approval
- Architecture changes require tech lead approval
- Keep docs in sync with code

---

## 📞 Contact

- **Issues**: Use GitHub Issues
- **Discussions**: Use GitHub Discussions
- **Security**: security@zapcut.video

---

## 📄 License

Proprietary - All Rights Reserved

---

**Built with** ⚡️ **by the Zapcut team**

**Last Updated**: November 15, 2025