# Epic 4: Script Generation & Review

**Status:** Not Started
**Priority:** P0 (MVP)
**Estimated Effort:** 2 weeks
**Dependencies:** Epic 1-3

---

## Epic Overview

### Value Proposition
Users receive AI-generated video scripts with scene-by-scene breakdown, which they can review, edit, and approve before video production.

### Success Criteria
- [ ] Script generated from chat requirements and brand context
- [ ] Script includes storyline, 3-5 scenes, visual descriptions, voiceover text
- [ ] User can view complete script in structured format
- [ ] User can regenerate script with feedback
- [ ] User can approve script to proceed to video generation
- [ ] Complete review UI with editing capabilities

### Demo Scenario
1. User completes chat (Epic 3) → Clicks "Generate Script"
2. Loading indicator shows "Generating script..."
3. Script displays with storyline and scenes
4. User reviews each scene
5. User clicks "Approve & Generate Video"
6. Proceeds to Epic 5

---

## User Stories

### Story 4.1: Trigger Script Generation
- Generate script from conversation context
- Show loading state during generation
- Store script in database
- **Backend:** OpenAI API call with structured JSON output
- **Database:** `scripts` table

### Story 4.2: Display Script Structure
- Show storyline (2-3 sentences)
- Display scenes in cards (scene number, duration, visuals, voiceover)
- Expandable Sora prompts
- **Frontend:** ScriptReviewPage, SceneCard components

### Story 4.3: Script Regeneration
- "Regenerate Script" button
- User can provide feedback for changes
- New version generated
- **Backend:** Call OpenAI with feedback context

### Story 4.4: Script Approval
- "Approve & Generate Video" button
- Locks script from editing
- Updates project status to "generating"
- Navigates to Epic 5

---

## Database Schema

```sql
CREATE TABLE scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_project_id UUID REFERENCES ad_projects(id) ON DELETE CASCADE UNIQUE,
    storyline TEXT NOT NULL,
    scenes JSONB NOT NULL, -- Array of scene objects
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- scenes JSONB structure
[
  {
    "sceneNumber": 1,
    "duration": 5,
    "description": "Runner lacing up shoes",
    "visualPrompt": "Cinematic close-up...",
    "voiceoverText": "Every journey starts with the right first step"
  }
]
```

---

## API Endpoints

```
POST /api/projects/:projectId/script/generate
GET /api/projects/:projectId/script
POST /api/projects/:projectId/script/regenerate
POST /api/projects/:projectId/script/approve
```

---

## Frontend Routes

```
/brands/:brandId/projects/:projectId/script → ScriptReviewPage
```

---

## References

- **PRD:** Section 3.4 (Script Review & Approval)
- **UI Spec:** Screen 8 (Script Review)
