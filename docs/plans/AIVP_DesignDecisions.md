# AI Video Generation Pipeline - Design Decisions
**Date:** 2025-11-15
**Status:** Validated
**Related:** PRD-AI-Video-Generation-Pipeline.md

---

## Overview

This document captures the validated design decisions for Zapcut's AI video generation pipeline, resolving all open questions from the PRD through collaborative brainstorming.

---

## 1. Audio Architecture - Full Suite via Mixed Services

### Decision
Implement professional-quality audio with voiceover, background music, and sound effects using a multi-service approach.

### Services

**Voiceover:**
- Service: Replicate TTS models (Bark or Coqui XTTS)
- Use case: Scene-by-scene narration from script text
- Accents: American, British, Australian English
- Cost: ~$0.05-0.10 per 30s ad

**Music:**
- Service: Suno AI (standalone API at suno.ai)
- Use case: Custom 30-60 second background tracks from text prompts
- Quality: Premium musical structure and composition
- Cost: $10-30/month subscription (unlimited on higher tiers)
- Rationale: Music quality is critical for emotional impact; worth separate integration

**Sound Effects:**
- Service: Replicate audio models or Freesound API
- Use case: Product sounds, transitions, ambient audio
- Cost: Minimal (~$0.01-0.05 per ad)

### Generation Flow
1. After script approval, create parallel audio generation jobs
2. Voiceover: Generate narration for each scene with voiceover text
3. Music: Generate single continuous track matching ad tone (from chat context)
4. SFX: Add triggered effects based on visual events (can be manual in editor for MVP)
5. FFmpeg composites all audio layers with video, auto-mixing levels

### Total Audio Cost
~$0.20-0.30 per ad (excluding Suno subscription amortized across users)

---

## 2. LoRA Fine-Tuning Strategy - Progressive Training

### Decision
Train brand-specific LoRA models after first video generation with user preview and approval.

### Timeline

**First Video (Day 1):**
- Use base Sora with brand-aware prompts
- Prompts include brand colors, product descriptions from brand profile
- Fast generation: 3-5 minutes
- User gets immediate value

**Background Training (Automatic):**
- Triggers after first video completes
- Training data:
  - 2+ original product images
  - Generated video frames from first ad
  - ~10-15 high-quality training images total
- Duration: 30-45 minutes
- Runs as backend job in Redis queue
- Persists if user closes app
- Model saved to S3 when complete

**Before Second Video (User Choice):**
- Notification: "Your custom brand style is ready!"
- Preview UI: Side-by-side comparison
  - Left: Sample frame with standard Sora
  - Right: Sample frame with custom LoRA style
- User decision: "Use custom style for future ads?" (Yes/No)
- If approved: All future videos use LoRA model
- If rejected: Continue with base Sora, can retry training later

### Backend Schema
```typescript
Brand.loraModel = {
  status: 'none' | 'training' | 'ready' | 'failed',
  trainingJobId: string,
  modelUrl: string, // S3 location
  trainedAt: Date,
  userApproved: boolean,
  previewImageUrl: string // Sample frame for comparison
}
```

### Rationale
- First video needs speed (user validation)
- After first video, user is invested and willing to wait
- Training from generated content produces better results than 2 images alone
- User preview builds trust and demonstrates value

---

## 3. Pricing Model - Hybrid Free Trial + Flexible Monetization

### Decision
Two free videos (15s + 30s) followed by credits or subscription options.

### Free Tier
**Allowance:**
- Video 1: Up to 15 seconds (free)
- Video 2: Up to 30 seconds (free)
- After 2 videos: Must purchase

**Features:**
- Full AI chat + script generation
- Complete audio suite (voiceover, music, SFX)
- 1080p export
- No watermark
- LoRA custom style (after first video)

**Rationale:**
- 15s lets users try short-form (Instagram Stories, TikTok)
- 30s lets users try medium-form (Facebook Feed, longer social)
- Experience full value before payment
- Clear upgrade path after 2 videos

### Pay-Per-Video (Credits)

**Single Videos:**
- $5 per 30s video
- $8 per 60s video

**Credit Packs:**
- $40 = 10 credits (30s videos) → $4/video
- $70 = 10 credits (60s videos) → $7/video
- Credits never expire

**Best for:** Occasional users, seasonal campaigns, testing

### Subscription Tiers

**Starter - $29/month:**
- 10 videos/month
- Up to 30 seconds per video
- 1080p export
- Full audio suite
- LoRA custom styles

**Pro - $79/month:**
- 30 videos/month
- Up to 60 seconds per video
- 1080p export
- Priority processing (faster queue)
- Full audio suite
- LoRA custom styles

**Agency - $199/month:**
- 100 videos/month
- Up to 60 seconds per video
- 4K export
- Priority processing
- Full audio suite
- LoRA custom styles
- API access (future)

**Best for:** Regular users, agencies, high-volume creators

### Feature Comparison Table

| Feature | Free (2 videos) | Credits | Starter | Pro | Agency |
|---------|----------------|---------|---------|-----|--------|
| Video count | 2 total | Pay per video | 10/month | 30/month | 100/month |
| Max length | 15s, then 30s | 30s or 60s | 30s | 60s | 60s |
| Resolution | 1080p | 1080p | 1080p | 1080p | 4K |
| LoRA style | ✅ | ✅ | ✅ | ✅ | ✅ |
| Priority queue | - | - | - | ✅ | ✅ |
| API access | - | - | - | - | ✅ |
| Cost per video | Free | $4-8 | $2.90 | $2.63 | $1.99 |

### In-App Flow
1. User completes 2 free videos
2. On 3rd video attempt: Modal appears
3. Header: "Choose your plan to continue creating"
4. Two-column layout: Credits (left) vs Subscription (right)
5. Highlight Pro tier as "Most Popular"
6. Clear value proposition for each option

---

## 4. Video Length Limits - Platform-Aligned

### Decision
Length limits aligned with social media platform requirements.

### Length by Tier

**Free Tier:**
- Video 1: 15 seconds → Instagram Stories, TikTok, Reels
- Video 2: 30 seconds → Instagram Feed, Facebook, extended TikTok

**Credits/Starter ($29/mo):**
- Up to 30 seconds per video
- Platforms: Instagram, TikTok, Facebook Feed, LinkedIn, Twitter/X

**Pro ($79/mo) & Agency ($199/mo):**
- Up to 60 seconds per video
- Platforms: All above + YouTube pre-roll, YouTube Shorts (extended), in-stream ads

### Chat Integration
During AI conversation (Question 3/5):
- AI asks: "How long should your ad be?"
- Provides context:
  - "15 seconds is perfect for Instagram Stories and TikTok"
  - "30 seconds works great for Facebook and Instagram Feed"
  - "60 seconds is ideal for YouTube"
- Validates against user's tier
- If user requests length beyond tier: Inline upgrade prompt

### Technical Validation
- Frontend: Disable length options beyond tier in UI
- Backend: Validate requested duration against user tier before job creation
- Error: "60-second videos require Pro plan. Upgrade now?"

### Rationale
- Limits match real platform needs (not arbitrary)
- Natural upgrade incentive (want YouTube? Need Pro)
- Clear value at each tier
- Industry-standard durations

---

## 5. Multi-Language Support - English-Only MVP

### Decision
Launch with English only, build foundation for future localization.

### MVP Scope (English Only)

**UI/UX:**
- All interface text in English
- Date/time formats: US standard
- Currency: USD

**AI Services:**
- GPT-4 conversations: English prompts and responses
- Voiceover: English voice models
  - Accents available: American, British, Australian
  - Male and female voices
- Script generation: English-optimized prompts

**Target Market:**
- United States
- United Kingdom
- Canada
- Australia
- Total addressable market: ~500M English speakers

### Technical Foundation

**i18n Setup (Day 1):**
- Install react-i18next
- All UI strings in translation files: `en/common.json`, `en/chat.json`, etc.
- No hardcoded strings in components
- Example: `{t('button.createBrand')}` instead of `"Create Brand"`

**Database Schema:**
```typescript
User {
  preferredLocale: string, // 'en-US' for now, future: 'es-MX', 'fr-FR'
}

AdProject {
  scriptLocale: string, // Language of generated script
}
```

**Benefits:**
- Future localization is just adding translation files
- No code refactoring needed later
- Can A/B test international demand with landing pages

### Post-MVP Expansion Roadmap

**Phase 1 (v2.0) - Spanish:**
- Unlock: Latin America, Spain (~500M users)
- Voiceover: Spanish TTS models
- UI translation
- Cultural adaptation of prompts
- Timeline: 3-6 months post-launch

**Phase 2 (v2.5) - European Languages:**
- French, German, Italian
- Combined market: ~200M users
- Timeline: 6-9 months post-launch

**Phase 3 (v3.0) - Asian Languages:**
- Mandarin, Hindi, Japanese
- Significant cultural and technical challenges
- Timeline: 12+ months post-launch

### User Communication

**FAQ:**
- Q: "What languages do you support?"
- A: "Currently English, with Spanish and other languages coming soon. Want to be notified? Join our waitlist!"

**Waitlist Strategy:**
- "Get notified when we launch in [Your Language]"
- Email capture form
- Validates international demand
- Builds pre-launch user base for each locale

### Rationale
- Focus on product-market fit first
- English market is large enough for validation
- Avoid complexity of multi-language testing in MVP
- Technical foundation enables fast expansion later
- 2-3 months faster to market

---

## Implementation Priority

Based on these decisions, the implementation order should be:

1. **Core Infrastructure** (Week 1-2)
   - Backend API, database, authentication
   - S3 integration, Redis queue
   - Replicate API integration (Sora, TTS)

2. **Brand & Chat** (Week 3-4)
   - Brands dashboard
   - Chat interface with GPT-4
   - 5-question conversation flow

3. **Script & Video Generation** (Week 5-8)
   - Script generation and review UI
   - Sora video generation pipeline
   - Suno music integration
   - Audio composition with FFmpeg

4. **LoRA Training** (Week 9)
   - Background job for LoRA training
   - Preview comparison UI
   - User approval flow

5. **Pricing & Limits** (Week 10)
   - Free tier tracking (2 videos)
   - Credit system
   - Subscription tiers
   - Length validation

6. **Editor Integration** (Week 11)
   - Load generated video into Zapcut
   - Pre-populate assets
   - Navigation flow

7. **Polish & Launch** (Week 12)
   - Testing, bug fixes
   - Performance optimization
   - Production deployment

---

## Open Items for Future Discussion

1. **Voice Selection**: Should users choose voice gender/accent, or should AI auto-select based on brand tone?
2. **Music Customization**: Allow users to regenerate just music without re-generating video?
3. **SFX Library**: Build custom SFX library vs use Freesound API?
4. **API Rate Limits**: What rate limits per tier to prevent abuse?
5. **Export Formats**: Just MP4, or also MOV, WebM for different platforms?

---

## Success Metrics (First 30 Days)

Based on these decisions, success looks like:

- **Activation**: 100+ users create brands
- **Free Tier Completion**: 60+ users create both free videos (15s + 30s)
- **Conversion**: 25% of free users upgrade to paid (credits or subscription)
- **LoRA Adoption**: 70%+ approve custom brand styles when prompted
- **Video Quality**: 90%+ generation success rate
- **Performance**: <5 minutes average generation time (30s video)

---

**End of Design Document**
