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

## Recent UI Improvements

### Combined Brands & Campaigns View (November 2025)

The dashboard has been redesigned to provide a unified view of brands and their associated campaigns:

**Key Changes:**
- **Unified List View:** Replaced separate grid-based Brands and Campaigns pages with a single list-based interface
- **Expandable Brand Items:** Each brand can be expanded to reveal all associated campaigns
- **Visual Hierarchy:** 
  - Brands display with preview images (80x80px from product_image_1)
  - Campaigns display with preview images (60x60px from product_image_2 or brand image)
  - Clear visual distinction between parent brands and child campaigns
- **Improved Navigation:** Consolidated "Brands" and "Campaigns" into single "Brands & Campaigns" menu item
- **Better UX:** All brand and campaign actions accessible from one screen
  - Create new campaigns directly from brand row
  - View campaign status and progress inline
  - Quick access to edit brand, view videos, or delete items

**Technical Implementation:**
- New component: `BrandsCampaignsList.tsx`
- Combines data from `/api/brands/` and `/api/campaigns/` endpoints
- Maintains existing session-based caching (5-minute TTL)
- Preserves all existing functionality while improving information architecture

### Scene Video Edit & Regenerate Feature (November 2025)

Added the ability to edit and regenerate individual scene videos with custom prompts:

**Key Features:**
- **Edit Button:** Each video in the "All Scene Videos" section now has an "Edit" button alongside the Download button
- **Lightbox Modal:** Clicking Edit opens a modal showing:
  - Scene title and number
  - Current video preview
  - Editable prompt text area (pre-filled with original sora_prompt)
  - Regenerate Video button with loading state
- **Real-time Updates:** After regeneration starts, the UI:
  - Shows loading spinner on the scene card
  - Polls for status updates every 3 seconds
  - Updates the video automatically when generation completes
- **Failed Scene Retry:** Failed scenes show a "Retry" button instead of "Edit"

**Technical Implementation:**
- **Frontend:**
  - New component: `EditVideoModal.jsx` - Reusable modal for prompt editing
  - Updated `VideoPlayer.jsx` with edit functionality and status polling
  - Updated `api.ts` with `regenerateScene()` endpoint
- **Backend:**
  - New endpoint: `POST /api/campaigns/{campaign_id}/regenerate-scene`
  - Accepts `scene_number` and `prompt` in request body
  - Updates campaign's `sora_prompts` array with new prompt
  - Triggers Celery task (or async fallback) for video regeneration
  - Reuses existing `generate_single_scene_task` with custom prompt

**User Experience:**
1. User clicks "Edit" button next to any completed video
2. Modal opens showing current prompt and video preview
3. User modifies the prompt to change video generation
4. User clicks "Regenerate Video"
5. Modal closes, scene card shows "Generating..." with spinner
6. Page automatically updates when new video is ready (polling)
7. New video replaces old video in both grid and main player

---

**Status:** Active development - Scene regeneration feature complete
**Documentation:** Complete PRD, design decisions, technical architecture, and frontend specification available
**Next Step:** Continue development of video generation pipeline and editor integration
