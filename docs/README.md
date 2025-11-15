# Zapcut AI Documentation

Welcome to the Zapcut AI documentation repository. This directory contains all product requirements, technical specifications, architecture documentation, and agile artifacts (epics/stories) for the project.

## 📁 Directory Structure

```
docs/
├── README.md                          # This file
├── EPICS-INDEX.md                     # Master index of all epics and stories
├── REPLICATE-MODELS.md                # Complete Replicate model guide
├── PRD/                               # Product Requirements Documents
│   ├── 01-product-vision.md           # Product vision and mission
│   ├── 02-user-personas.md            # Target user personas
│   ├── 03-user-flows.md               # Detailed user journey flows
│   ├── 04-features.md                 # Feature requirements
│   ├── 05-ui-ux-guidelines.md         # Design system guidelines
│   ├── 06-content-policy.md           # Content moderation policy
│   └── 07-success-metrics.md          # KPIs and success criteria
├── Architecture.md                    # Technical architecture overview
├── Epics/                             # High-level feature epics
│   ├── E001-authentication-authorization.md
│   ├── E002-project-brand-management.md
│   ├── E003-creative-brief-chat.md
│   ├── E004-multi-agent-video-generation.md
│   ├── E005-video-composition-export.md
│   ├── E006-social-media-publishing.md
│   ├── E007-infrastructure-deployment.md
│   └── E008-video-editor-core.md
└── Stories/                           # Detailed user stories
    ├── S001-cognito-user-pool-setup.md
    ├── S002-email-password-auth.md
    ├── S014-master-orchestrator-agent.md
    ├── S062-replicate-model-abstraction.md
    └── ... (60+ total stories)
```

## 🎯 What is Zapcut AI?

Zapcut is an **AI-powered video generation platform** that transforms simple prompts into professional, publication-ready video advertisements with synchronized audio, coherent visuals, and brand consistency—all with minimal human intervention.

### Core Value Proposition
**"From prompt to publish in under 5 minutes"**

### Key Features
1. **End-to-End Generation**: Complete video ads with music, visuals, and brand consistency from a single brief
2. **Creative DNA System**: Reusable "Creative Bibles" that lock visual style
3. **Multi-Modal Intelligence**: Orchestrated AI agents powered by Replicate's full model suite
4. **Professional Quality**: 4K output at 30fps with audio-visual synchronization
5. **Direct Publishing**: One-click export to X (Twitter) and LinkedIn

### AI Models (via Replicate)
- **Text**: Llama 3.1 (70B/405B), Mistral Large, Llama Guard 3
- **Image**: FLUX 1.1 Pro, SDXL, Playground v2.5
- **Video**: Minimax Video-01, Luma Dream Machine, Runway Gen-3
- **Audio**: MusicGen, Suno Bark, AudioCraft

See [REPLICATE-MODELS.md](./REPLICATE-MODELS.md) for complete model guide.

## 📚 Documentation Hierarchy

### 1. Product Requirements (PRD)
High-level product vision, user needs, and business requirements.

**Start here if you're:**
- New to the project
- Planning features
- Understanding the "why" behind decisions

**Key files:**
- `PRD/01-product-vision.md` - Mission, problem, solution
- `PRD/03-user-flows.md` - How users interact with the system
- `PRD/04-features.md` - Detailed feature requirements

### 2. Technical Architecture
System design, infrastructure, and technical decisions.

**Start here if you're:**
- Implementing features
- Setting up infrastructure
- Understanding technical constraints

**Key file:**
- `Architecture.md` - Complete technical architecture

### 3. Epics & Stories
Agile artifacts breaking down features into implementable units.

**Start here if you're:**
- Planning sprints
- Estimating work
- Implementing specific features

**Key files:**
- `EPICS-INDEX.md` - Master index and roadmap
- `Epics/*.md` - High-level feature epics
- `Stories/*.md` - Detailed implementation stories

## 🚀 Quick Start Guides

### For Product Managers
1. Read [Product Vision](./PRD/01-product-vision.md)
2. Review [User Flows](./PRD/03-user-flows.md)
3. Check [Epics Index](./EPICS-INDEX.md) for roadmap

### For Engineers
1. Read [Architecture](./Architecture.md)
2. Review [Replicate Models Guide](./REPLICATE-MODELS.md) for AI integration
3. Review relevant Epic (e.g., `Epics/E004-multi-agent-video-generation.md`)
4. Check assigned Stories for implementation details

### For DevOps
1. Read [Architecture](./Architecture.md) - Infrastructure section
2. Review [E007: Infrastructure & Deployment](./Epics/E007-infrastructure-deployment.md)
3. Check stories S044-S053 for specific tasks

### For Designers
1. Read [UI/UX Guidelines](./PRD/05-ui-ux-guidelines.md)
2. Review [User Flows](./PRD/03-user-flows.md)
3. Check relevant epics for UI components needed

## 📖 How to Read Epics & Stories

### Epic Structure
Each epic is a major body of work that delivers significant value.

**Epic Contents:**
- **Overview**: What this epic achieves
- **Business Value**: Why it matters
- **Success Criteria**: Definition of done
- **Priority**: P0 (MVP), P1 (Post-MVP), P2 (Nice-to-have), P3 (Enterprise)
- **Estimated Effort**: Time required
- **Related Stories**: Breakdown of work
- **Technical Notes**: Implementation details

**Example:** [E004: Multi-Agent Video Generation](./Epics/E004-multi-agent-video-generation.md)

### Story Structure
Each story is a specific, implementable unit of work.

**Story Contents:**
- **User Story**: "As a [role], I want [goal], so that [benefit]"
- **Acceptance Criteria**: Checklist for completion
- **Technical Details**: Code examples, architecture
- **Testing Plan**: How to verify it works
- **Size**: XS (hours), S (hours), M (1-2 days), L (3-5 days), XL (weeks)

**Example:** [S014: Master Orchestrator Agent](./Stories/S014-master-orchestrator-agent.md)

## 🎯 Current Status

### Phase 1: MVP Foundation (Weeks 1-2)
- ✅ **E008: Video Editor Core** - Complete
- 🔴 **E001: Authentication** - Not started
- 🔴 **E002: Project Management** - Not started
- 🔴 **E007: Infrastructure** - Not started

### Phase 2: AI Generation Core (Weeks 3-4)
- 🔴 **E003: Creative Brief Chat** - Not started
- 🔴 **E004: Multi-Agent Pipeline** - Not started
- 🔴 **E005: Video Composition** - Not started

### Phase 3: Polish & Publishing (Weeks 5-6)
- 🔴 **E006: Social Media Publishing** - Not started

**Legend:**
- ✅ Complete
- 🟡 In Progress
- 🔴 Not Started
- 📋 Backlog

## 🛠️ How to Contribute

### Adding New Documentation
1. **New Epic**:
   ```bash
   cp docs/Epics/E001-authentication-authorization.md docs/Epics/E00X-new-epic.md
   # Update content
   # Add to EPICS-INDEX.md
   ```

2. **New Story**:
   ```bash
   cp docs/Stories/S001-cognito-user-pool-setup.md docs/Stories/S0XX-new-story.md
   # Update content
   # Link to parent epic
   ```

3. **Update Architecture**:
   - Edit `Architecture.md` directly
   - Add diagrams to `/docs/diagrams/`
   - Link from relevant epics/stories

### Documentation Standards

#### Markdown Conventions
- Use ATX headers (`#`, `##`, `###`)
- Code blocks with language tags (```python, ```typescript)
- Task lists for checklists (`- [ ]`, `- [x]`)
- Links to related docs (`[link text](./path/to/file.md)`)

#### File Naming
- Epics: `EXXX-kebab-case-title.md` (e.g., `E001-authentication-authorization.md`)
- Stories: `SXXX-kebab-case-title.md` (e.g., `S001-cognito-user-pool-setup.md`)
- Lowercase, hyphen-separated
- Sequential numbering

#### Version Control
- All documentation tracked in git
- Use meaningful commit messages
- Tag documentation updates with `[docs]` prefix

## 📊 Metrics & KPIs

### Documentation Coverage
- **Epics**: 8 total (100% of MVP scope)
- **Stories**: 60+ (covering P0 and P1 priorities)
- **PRDs**: 7 documents (complete)
- **Architecture**: 1 comprehensive document

### Story Sizing Breakdown
- **XS (1-2 hours)**: 15 stories (~25%)
- **S (3-5 hours)**: 20 stories (~33%)
- **M (1-2 days)**: 15 stories (~25%)
- **L (3-5 days)**: 8 stories (~13%)
- **XL (1-2 weeks)**: 2 stories (~3%)

### Priority Distribution
- **P0 (MVP Critical)**: 42 stories (70%)
- **P1 (Post-MVP)**: 12 stories (20%)
- **P2 (Nice-to-have)**: 6 stories (10%)

## 🔗 External Resources

### Product
- **Website**: https://zapcut.video
- **App**: https://app.zapcut.video
- **API Docs**: https://api.zapcut.video/docs (Swagger)

### Development
- **GitHub**: Internal repository
- **CI/CD**: GitHub Actions
- **Cloud**: AWS (us-east-1)
- **Design**: Figma (link internal)

### AI & Models
- **Replicate**: https://replicate.com
- **Replicate Docs**: https://replicate.com/docs
- **API Reference**: https://replicate.com/docs/reference/http
- **Model Guide**: [REPLICATE-MODELS.md](./REPLICATE-MODELS.md)

### Communication
- **Slack**: #zapcut-general, #zapcut-engineering
- **Jira**: (if using)
- **Engineering Wiki**: (link internal)

## ❓ FAQ

### Q: Where do I find information about a specific feature?
**A**: 
1. Check `EPICS-INDEX.md` for high-level overview
2. Find the relevant epic (e.g., E004 for video generation)
3. Drill down to specific stories if needed

### Q: How do I know what to work on next?
**A**: 
1. Check `EPICS-INDEX.md` → Roadmap Timeline
2. Look for stories marked 🔴 "Ready" status
3. Consult with team lead for sprint planning

### Q: Where's the technical implementation guide?
**A**: Each story contains detailed technical specs, code examples, and testing plans. Start with the story related to your task.

### Q: How do I propose a new feature?
**A**:
1. Create a GitHub issue describing the feature
2. Draft an epic document following existing templates
3. Break down into stories
4. Get approval from product/engineering leads

### Q: What's the difference between Epic and Story?
**A**:
- **Epic**: Large feature (e.g., "Authentication System") - multiple weeks
- **Story**: Specific task (e.g., "Set up Cognito User Pool") - hours to days

## 📞 Contact

**Questions about:**
- **Product**: product@zapcut.video
- **Engineering**: engineering@zapcut.video
- **DevOps**: devops@zapcut.video
- **Documentation**: Update this README or file an issue

---

**Last Updated**: 2025-11-15  
**Maintained By**: Zapcut Engineering Team  
**Status**: Living Document (updated continuously)

