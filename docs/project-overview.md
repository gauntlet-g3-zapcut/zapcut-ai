# Zapcut AI - Project Overview

## Executive Summary

Zapcut AI is an AI-powered video ad generation platform that transforms the creation of professional video advertisements from hours to minutes. By combining conversational AI, automated asset generation, and intelligent video composition, the platform enables small business owners and marketers to create high-quality video ads through simple natural language conversations.

## What We're Building

An end-to-end video ad creation pipeline that extends the existing Zapcut video editor with cloud-based AI capabilities. Users describe their product and campaign goals through a conversational interface, and the system generates a complete video advertisement with professional voiceover, music, and brand-specific styling. The generated video loads directly into Zapcut's editor for final refinement and export.

## Target Market

**Primary:** Small business owners and marketers creating social media ads (Instagram, Facebook, TikTok, YouTube)

**Secondary:** Content creators and agencies managing multiple brand campaigns

**Tertiary:** E-commerce sellers needing product advertisement videos

Total addressable market: 500M+ English speakers across US, UK, Canada, and Australia.

## Core Value Proposition

- **Speed:** Generate professional video ads in 6-8 minutes vs. hours of manual editing
- **Accessibility:** No creative expertise required - AI guides the entire process
- **Quality:** Professional voiceover, custom music, and brand-specific visual styling
- **Control:** Full editing capabilities in Zapcut for final refinement

## Key Features

**AI-Guided Creation Flow:**
- Conversational interface asks strategic questions about target audience, platform, duration, and messaging
- GPT-4 generates detailed video scripts with scene-by-scene breakdowns
- User reviews and approves storyline before generation

**Automated Video Production:**
- Sora (via Replicate) generates high-quality video scenes from text descriptions
- Professional voiceover using Replicate TTS models with multiple accent options
- Custom background music from Suno AI matched to brand tone
- Intelligent product image integration throughout scenes

**Brand Customization:**
- LoRA fine-tuning creates brand-specific visual styles after first video
- Consistent look and feel across all ads for a brand
- User preview and approval of custom style before application

**Flexible Business Model:**
- Two free videos (15s + 30s) to experience full value
- Pay-per-video credits or monthly subscriptions
- Platform-aligned length limits (30s for social, 60s for YouTube)

## Technical Architecture

**Frontend:**
- Electron desktop application with React + TypeScript
- Glassmorphism design system with TailwindCSS
- Hybrid cloud/local architecture for optimal performance

**Backend:**
- Python/FastAPI server for AI orchestration
- PostgreSQL database with JSONB for flexible data
- Redis Queue (RQ) for sequential video generation jobs
- AWS S3 for media storage and delivery

**AI Services:**
- OpenAI GPT-4: Conversational interface and script generation
- Sora (Replicate): Text-to-video scene generation
- Replicate TTS: Professional voiceover in multiple accents
- Suno AI: Custom background music composition
- FFmpeg: Final video composition and audio mixing

**Infrastructure:**
- Cloud-hosted backend for AI processing
- Local video editor for offline-capable editing
- HTTP polling for generation progress tracking
- Download-first approach for seamless editor integration

## Development Timeline

**12-Week MVP Development Plan:**

- **Weeks 1-2:** Foundation (backend API, database, authentication, S3 integration)
- **Week 3:** Brand management (dashboard, creation modal, image uploads)
- **Week 4:** Chat interface (GPT-4 integration, 5-question flow)
- **Week 5:** Script generation (GPT-4 prompts, review UI)
- **Weeks 6-8:** Video generation pipeline (Sora, audio services, FFmpeg composition)
- **Week 9:** Editor integration (asset loading, navigation)
- **Weeks 10-11:** Polish and testing (error handling, optimization, UX refinement)
- **Week 12:** Launch preparation (deployment, monitoring, beta testing)

## Success Metrics

**Launch Criteria:**
- User can complete full flow from brand creation to exported video
- 95%+ video generation success rate
- Generated videos include user product images
- Average generation time under 5 minutes for 30s ads

**30-Day Post-Launch Goals:**
- 100+ users create brands
- 60+ users complete both free videos
- 25% conversion from free to paid
- 90%+ generation success rate
- 70%+ LoRA style approval rate

## Competitive Advantages

1. **End-to-End Solution:** Unlike fragmented tools, Zapcut AI handles everything from concept to final video
2. **Professional Quality:** Full audio production (voiceover + music + effects) matches high-end ad agencies
3. **Brand Consistency:** LoRA fine-tuning ensures recognizable brand identity across campaigns
4. **Editing Flexibility:** Generated videos aren't locked - full editing control in professional editor
5. **Platform Optimization:** Built-in understanding of social media platform requirements

## Market Positioning

Zapcut AI positions between DIY video tools (too manual, time-consuming) and expensive agency services (too costly, slow turnaround). We deliver agency-quality results at DIY tool pricing with unprecedented speed.

---

**Status:** Technical architecture validated, ready for implementation
**Documentation:** Complete PRD, design decisions, technical architecture, and frontend specification available
**Next Step:** Begin Phase 1 development (Foundation & Authentication)
