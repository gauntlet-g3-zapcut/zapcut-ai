# Zapcut AI: Epics & Stories Index

## Overview
This document provides a comprehensive index of all epics and user stories for the Zapcut AI project, organized by functional area and priority.

**Last Updated**: 2025-11-15  
**Total Epics**: 8  
**Total Stories**: 60+

---

## Epic Status Legend
- 🟢 **Complete**: Fully implemented and deployed
- 🟡 **In Progress**: Active development
- 🔴 **Not Started**: Planned but not yet begun
- 📋 **Backlog**: Lower priority, future consideration

---

## AI Video Generation Platform

### E001: User Authentication & Authorization 🔴
**Priority**: P0 (MVP Critical)  
**Effort**: 3-5 days  
**Owner**: Backend Team

Implement secure user authentication using AWS Cognito with JWT-based session management.

**Stories**:
- S001: AWS Cognito User Pool Setup
- S002: Email/Password Authentication Flow
- S003: Google OAuth Integration
- S004: JWT Session Management
- S005: User Profile Management
- S006: Frontend Auth UI Components

[View Epic Details](./Epics/E001-authentication-authorization.md)

---

### E002: Project & Brand Management 🔴
**Priority**: P0 (MVP Critical)  
**Effort**: 4-6 days  
**Owner**: Full-Stack Team

Enable users to create and manage brand/project entities with visual assets.

**Stories**:
- S007: Project CRUD Operations
- S008: Asset Upload to S3
- S009: Image Processing & Validation
- S010: Project List & Search UI
- S011: Asset Gallery Component
- S012: Color Palette Extraction

[View Epic Details](./Epics/E002-project-brand-management.md)

---

### E003: Creative Brief Chat Interface 🔴
**Priority**: P0 (MVP Critical)  
**Effort**: 6-8 days  
**Owner**: Frontend + Backend Team

Implement ChatGPT-style conversational interface guided by Master Orchestrator Agent.

**Stories**:
- S013: Chat UI Component Architecture
- S014: Master Orchestrator Agent Implementation
- S015: Stage-Based State Machine
- S016: File Upload in Chat
- S017: Safety Content Filtering
- S018: Chat History Persistence
- S019: Stage Progress Indicator

[View Epic Details](./Epics/E003-creative-brief-chat.md)

---

### E004: Multi-Agent Video Generation Pipeline 🔴
**Priority**: P0 (MVP Critical)  
**Effort**: 10-14 days  
**Owner**: Backend AI Team

Orchestrated multi-agent system transforming briefs into complete video ads.

**Stories**:
- S020: Style & Brand Consistency Agent
- S021: Story Structuring Agent
- S022: Safety Validation Agent
- S023: Prompt Synthesis Agent
- S024: Continuity Back-Propagation Agent
- S025: Creative Bible Data Model
- S026: Reference Image Generation
- S027: Parallel Scene Generation
- S028: API Retry Logic & Error Handling

[View Epic Details](./Epics/E004-multi-agent-video-generation.md)

---

### E005: Video Composition & Export 🔴
**Priority**: P0 (MVP Critical)  
**Effort**: 5-7 days  
**Owner**: Backend Media Team

FFmpeg-based video composition pipeline that stitches scenes, adds audio, and exports MP4 files.

**Stories**:
- S029: FFmpeg Scene Stitching
- S030: Audio Mixing & Synchronization
- S031: Text Overlay Rendering
- S032: Video Encoding & Optimization
- S033: Thumbnail Generation
- S034: S3 Upload & CDN Distribution
- S035: Multiple Aspect Ratio Support

[View Epic Details](./Epics/E005-video-composition-export.md)

---

### E006: Social Media Publishing 🔴
**Priority**: P1 (Post-MVP Polish)  
**Effort**: 4-6 days  
**Owner**: Backend + Frontend Team

OAuth integrations with X (Twitter) and LinkedIn for one-click video publishing.

**Stories**:
- S036: X/Twitter OAuth Integration
- S037: LinkedIn OAuth Integration
- S038: X Video Upload API Client
- S039: LinkedIn Video Upload & Post Creation
- S040: Caption Editor UI Component
- S041: Post Confirmation Modal
- S042: Published Post Tracking
- S043: Social Account Management UI

[View Epic Details](./Epics/E006-social-media-publishing.md)

---

### E007: Infrastructure & Deployment 🔴
**Priority**: P0 (MVP Critical)  
**Effort**: 7-10 days  
**Owner**: DevOps + Backend Team

Production-ready AWS infrastructure using Terraform with CI/CD pipelines.

**Stories**:
- S044: Terraform AWS Infrastructure Setup
- S045: PostgreSQL RDS Configuration
- S046: S3 Buckets & CloudFront CDN
- S047: AWS Cognito Setup
- S048: Elastic Beanstalk Application Deployment
- S049: Celery Worker EC2 Auto-Scaling Group
- S050: GitHub Actions CI/CD Pipeline
- S051: CloudWatch Monitoring & Dashboards
- S052: Centralized Logging Setup
- S053: Alert Rules & On-Call Configuration

[View Epic Details](./Epics/E007-infrastructure-deployment.md)

---

## Video Editor (Existing Implementation)

### E008: Video Editor Core 🟢
**Priority**: P0 (Already Implemented)  
**Effort**: Complete (30+ days prior work)  
**Owner**: Desktop Team

Core video editing functionality within Electron desktop application.

**Stories**:
- S054: Electron Main Process Setup ✅
- S055: Video Ingestion & Metadata Extraction ✅
- S056: Canvas Video Renderer ✅
- S057: VideoPoolManager (Preloading) ✅
- S058: AudioManager (Web Audio API) ✅
- S059: Timeline Playback Synchronization ✅
- S060: Clip Manipulation (Trim, Split, Move) ✅
- S061: Export Pipeline ✅

[View Epic Details](./Epics/E008-video-editor-core.md)

---

## Roadmap Timeline

### Phase 1: MVP Foundation (Weeks 1-2)
- ✅ E008: Video Editor Core (Complete)
- 🔴 E001: Authentication
- 🔴 E002: Project Management
- 🔴 E007: Infrastructure Setup

### Phase 2: AI Generation Core (Weeks 3-4)
- 🔴 E003: Creative Brief Chat
- 🔴 E004: Multi-Agent Video Generation
- 🔴 E005: Video Composition & Export

### Phase 3: Polish & Publishing (Weeks 5-6)
- 🔴 E006: Social Media Publishing
- 🔴 Testing & optimization
- 🔴 Beta launch

---

## Story Sizing Guide

**XS (1-2 hours)**: Simple UI component, configuration change  
**S (3-5 hours)**: Single API endpoint, basic feature  
**M (1-2 days)**: Complex component, API integration  
**L (3-5 days)**: Multi-component feature, agent implementation  
**XL (1-2 weeks)**: Major subsystem, complex integration

---

## Priority Levels

**P0 - MVP Critical**: Must have for initial launch  
**P1 - Post-MVP Polish**: Important for user experience  
**P2 - Nice-to-Have**: Future enhancements  
**P3 - Enterprise**: Advanced features for scale

---

## Story Workflow

```
Backlog → Ready → In Progress → In Review → Testing → Done
```

**Backlog**: Prioritized list of upcoming work  
**Ready**: Fully specified, ready to start  
**In Progress**: Active development  
**In Review**: Code review, QA testing  
**Testing**: Manual QA, integration testing  
**Done**: Merged, deployed, verified

---

## Quick Links

- [All Epics](./Epics/)
- [All Stories](./Stories/)
- [Product Vision](./PRD/01-product-vision.md)
- [Technical Architecture](./Architecture.md)
- [User Flows](./PRD/03-user-flows.md)
- [Features & Requirements](./PRD/04-features.md)

---

**Questions?** Contact: engineering@zapcut.video
