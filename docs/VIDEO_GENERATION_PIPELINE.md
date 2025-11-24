# ZapCut Video Generation Pipeline

## End-to-End Flow: Brand Creation to Final Video

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  1. CREATE BRAND                                                                     │
│  POST /api/brands                                                                    │
│  • User uploads: title, description, 2 product images                                │
│  • Images stored in Supabase S3 (brand-images bucket)                                │
│  • Returns: brand_id                                                                 │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  2. GATHER PREFERENCES (Two paths)                                                   │
│                                                                                      │
│  PATH A: Form-based                        PATH B: Chat-based                        │
│  POST /api/brands/{id}/campaign-answers    POST /api/brands/{id}/chat-session        │
│                                            POST /api/brands/{id}/chat/{cb_id}        │
│                                                                                      │
│  Collects 5 aspects:                                                                 │
│  • Target Audience (who should see this?)                                            │
│  • Visual Style (minimalist, bold, luxury, playful, edgy)                            │
│  • Emotion (excitement, trust, joy, inspiration)                                     │
│  • Pacing (fast/energetic, slow/elegant, dynamic build)                              │
│  • Color Palette (bold, moody, airy, earthy, warm, cool)                             │
│                                                                                      │
│  Creates: CreativeBible with campaign_preferences                                    │
│  Returns: creative_bible_id                                                          │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  3. GENERATE STORYLINE                                                               │
│  GET /api/brands/{id}/storyline/{creative_bible_id}                                  │
│                                                                                      │
│  OpenAI (gpt-4o-mini) generates:                                                     │
│  • brand_style: "modern" | "energetic" | "luxurious" | "minimal" | "bold"            │
│  • vibe: "energetic" | "sophisticated" | "fun" | "elegant" | "dramatic"              │
│  • colors: ["#hex1", "#hex2", "#hex3"]                                               │
│  • energy_level: "high" | "medium" | "low"                                           │
│  • storyline.scenes[5]: Each scene has:                                              │
│      - scene_number (1-5)                                                            │
│      - title ("Hook & Attention Grab", "Product Introduction", etc.)                 │
│      - description (detailed action description)                                     │
│      - start_time, end_time, duration (6s each, 30s total)                           │
│      - energy_start, energy_end (0.0-1.0, builds throughout)                         │
│      - visual_notes (specific visual direction)                                      │
│  • sora_prompts[5]: "{title}. {description}. {visual_notes}" per scene               │
│  • suno_prompt: Music generation prompt                                              │
│                                                                                      │
│  Stored in: CreativeBible.creative_bible (JSON)                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  4. CREATE CAMPAIGN (Draft or Approved)                                              │
│  POST /api/campaigns                                                                 │
│                                                                                      │
│  Body: { brand_id, creative_bible_id, status: "draft" | "pending" }                  │
│                                                                                      │
│  Creates Campaign with:                                                              │
│  • storyline (copied from CreativeBible)                                             │
│  • sora_prompts (copied from CreativeBible)                                          │
│  • suno_prompt (copied from CreativeBible)                                           │
│  • video_urls: [] (empty, will be populated)                                         │
│  • audio_status: "pending"                                                           │
│                                                                                      │
│  If status="pending" → triggers video generation immediately                         │
│  If status="draft" → user can edit storyline first                                   │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  5. APPROVE CAMPAIGN (if draft)                                                      │
│  POST /api/campaigns/{id}/approve                                                    │
│                                                                                      │
│  Changes status: "draft" → "pending"                                                 │
│  Triggers: start_video_generation_task.delay(campaign_id)                            │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  6. VIDEO + AUDIO GENERATION (Parallel)                                              │
│                                                                                      │
│  ┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐    │
│  │  VIDEO (Celery + Replicate Sora-2)  │  │  AUDIO (Celery + ElevenLabs)        │    │
│  │                                     │  │                                     │    │
│  │  start_video_generation_task:       │  │  generate_audio_task:               │    │
│  │  1. Set status → "processing"       │  │  1. Build composition_plan from     │    │
│  │  2. Init video_urls[] with 5        │  │     scenes (durations, energy)      │    │
│  │     pending entries                 │  │  2. Determine genre by avg energy:  │    │
│  │  3. Dispatch 5 scene tasks with     │  │     <0.4 → ambient                  │    │
│  │     15s stagger (rate limit)        │  │     <0.6 → cinematic                │    │
│  │                                     │  │     <0.8 → modern pop               │    │
│  │  generate_single_scene_task:        │  │     ≥0.8 → electronic               │    │
│  │  • Build prompt from sora_prompts   │  │  3. Call compose_detailed()         │    │
│  │  • Map duration → 4, 8, or 12s      │  │  4. Upload MP3 to S3 (soundtracks)  │    │
│  │  • Create Replicate prediction      │  │  5. Update audio_url, audio_status  │    │
│  │    with webhook callback            │  │                                     │    │
│  │  • Return immediately               │  │  Retries: 3x exponential backoff    │    │
│  │                                     │  │                                     │    │
│  │  Retries: 2x + jitter               │  └─────────────────────────────────────┘    │
│  └─────────────────────────────────────┘                                             │
│                     │                                                                │
│                     ▼                                                                │
│  ┌─────────────────────────────────────┐                                             │
│  │  WEBHOOK CALLBACK                   │                                             │
│  │  POST /webhooks/replicate           │                                             │
│  │  ?campaign_id=X&scene_num=Y         │                                             │
│  │                                     │                                             │
│  │  On "succeeded":                    │                                             │
│  │  1. Verify HMAC signature           │                                             │
│  │  2. Download video from Replicate   │                                             │
│  │  3. Upload to S3 (videos bucket)    │                                             │
│  │  4. Update scene status →           │                                             │
│  │     "completed" with S3 URL         │                                             │
│  │  5. If all 5 complete →             │                                             │
│  │     campaign.status = "completed"   │                                             │
│  │                                     │                                             │
│  │  On "failed"/"canceled":            │                                             │
│  │  • Retry up to 3x with new          │                                             │
│  │    prediction                       │                                             │
│  │  • After 3 failures → mark failed   │                                             │
│  └─────────────────────────────────────┘                                             │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  7. POLL STATUS                                                                      │
│  GET /api/campaigns/{id}/status                                                      │
│                                                                                      │
│  Returns:                                                                            │
│  {                                                                                   │
│    "status": "processing" | "completed" | "failed",                                  │
│    "audio": { "status": "generating", "audio_url": null },                           │
│    "progress": {                                                                     │
│      "current_scene": 2,                                                             │
│      "completed_scenes": 1,                                                          │
│      "total_scenes": 5,                                                              │
│      "scenes": [                                                                     │
│        { "scene_number": 1, "status": "completed", "video_url": "https://..." },     │
│        { "scene_number": 2, "status": "generating", "video_url": null },             │
│        { "scene_number": 3, "status": "pending", "video_url": null },                │
│        { "scene_number": 4, "status": "pending", "video_url": null },                │
│        { "scene_number": 5, "status": "pending", "video_url": null }                 │
│      ]                                                                               │
│    }                                                                                 │
│  }                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  8. FINAL OUTPUT                                                                     │
│                                                                                      │
│  Campaign.video_urls[5]:                                                             │
│  [                                                                                   │
│    { "scene_number": 1, "video_url": "https://supabase.../scene-1.mp4", ... },       │
│    { "scene_number": 2, "video_url": "https://supabase.../scene-2.mp4", ... },       │
│    { "scene_number": 3, "video_url": "https://supabase.../scene-3.mp4", ... },       │
│    { "scene_number": 4, "video_url": "https://supabase.../scene-4.mp4", ... },       │
│    { "scene_number": 5, "video_url": "https://supabase.../scene-5.mp4", ... }        │
│  ]                                                                                   │
│                                                                                      │
│  Campaign.audio_url: "https://supabase.../soundtracks/{campaign_id}.mp3"             │
│  Campaign.final_video_url: (first scene URL - no compositing yet)                    │
│  Campaign.status: "completed"                                                        │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Data Models

### Brand
```
id, user_id, title, description
product_image_1_url, product_image_2_url  (S3 URLs)
```

### CreativeBible
```
id, brand_id, name
campaign_preferences: { style, audience, emotion, pacing, colors, ideas }
creative_bible: {
  brand_style, vibe, colors[], energy_level,
  storyline: { scenes[5] },
  sora_prompts[5],
  suno_prompt
}
```

### Campaign
```
id, brand_id, creative_bible_id
status: draft → pending → processing → completed | failed
storyline: { scenes[5] }
sora_prompts[5]
video_urls[5]: [{ scene_number, video_url, status, prediction_id, retry_count }]
audio_url, audio_status
final_video_url
```

---

## External Services

| Service | Purpose | Rate Limits |
|---------|---------|-------------|
| **OpenAI gpt-4o-mini** | Storyline generation | Standard |
| **Replicate Sora-2** | Video generation (4/8/12s clips) | ~10s reset, hence 15s stagger |
| **ElevenLabs Music** | Soundtrack generation | Standard |
| **Supabase S3** | Storage (brand-images, videos, soundtracks) | - |
| **Redis (Upstash)** | Celery broker | - |

---

## Current Limitations

1. **No video compositing** - 5 separate MP4s, not stitched together
2. **No voiceover/TTS** - Only background music, no narration
3. **No product image overlays** - FFmpeg compositing not implemented
4. **final_video_url** - Just points to scene 1, not a combined video

---

## Timing Estimates

| Step | Duration |
|------|----------|
| Brand creation | ~2s |
| Preference gathering | User-dependent |
| Storyline generation (OpenAI) | ~3-5s |
| Campaign creation | ~1s |
| Video generation (per scene) | ~2-3 min |
| Total video generation (5 scenes, staggered) | ~4-5 min |
| Audio generation | ~30-60s |
| **Total (approval to completion)** | **~5-6 min** |
