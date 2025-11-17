---

## Data Storage Schema

**Store for each campaign**:
- `audience_description` (text): Raw user description
- `audience_keywords` (array): Extracted keywords
- `style_description` (text): Raw user description
- `style_keywords` (array): Extracted keywords
- `emotion_description` (text): Raw user description
- `emotion_keywords` (array): Extracted keywords
- `pacing_description` (text): Raw user description
- `pacing_keywords` (array): Extracted keywords
- `colors_description` (text): Raw user description
- `colors_keywords` (array): Extracted keywords

**Example**:
```
audience_description: "Young professionals who work in tech, want to feel cool and ahead of the curve"
audience_keywords: ["young professionals", "tech workers", "aspirational", "forward-thinking"]

style_description: "Clean and modern, kind of like the minimalist Apple ads but with more personality"
style_keywords: ["minimalist", "modern", "clean", "personality-driven"]
```

---

## Example Agent Conversation

```
Agent: "Hi! 👋 I'm your creative ad consultant, and I'm excited to help you 
create an amazing 30-second video ad.

I see you make premium coffee equipment—that's cool!

To craft the perfect ad, I need to understand your vision. Don't worry about 
using fancy words—just describe what you're imagining. Let's start:

Who are you trying to reach with this ad?"

User: "People who love coffee and want nice things for their kitchen"

Agent: "Got it—coffee enthusiasts who appreciate quality. 

What should the ad look and feel like? Think of things like: minimalist and clean, 
bold and eye-catching, luxury and sophisticated, playful and fun, edgy and dramatic—
or anything else you're picturing."

User: "Definitely luxurious, but not stuffy. Like high-end but approachable"

Agent: "Perfect! Luxury but with warmth. I can see that.

Now, what feeling should the ad create? Like: making people excited, building trust, 
making them smile, feeling inspired—whatever matches your product."

User: "I want people to feel like this is worth the investment, that it's aspirational 
but also attainable, you know?"

Agent: "Absolutely—aspiration + achievability. That's smart positioning.

How should it move? Fast-paced and energetic? Slow and elegant? Something smooth 
and flowing? What's your vibe?"

User: "Slow and elegant, like a luxury brand but with beautiful shots of the product"

Agent: "Slow, elegant, cinematic. Love it.

Last thing—what about colors? Any colors that feel right for this brand? 
Bold and vibrant, dark and moody, light and airy, natural and earthy, 
or something else entirely?"

User: "Warm tones, like copper and cream, maybe some dark walnut wood"

Agent: "Warm metallics and rich woods—that's perfect for the vibe.

Let me recap what I'm picturing for your ad:

- Audience: People who love coffee and want nice things for their kitchen
- Visual Style: Luxurious but not stuffy, high-end but approachable
- Emotion: Aspiration + achievability, makes people feel it's worth the investment
- Pacing: Slow and elegant, with beautiful shots of the product
- Color Palette: Warm tones like copper and cream, dark walnut wood

Does that capture your vision? If yes, I'm ready to generate your ad! 🎬"

User: "Yes, perfect!"

[Campaign created with extracted descriptions and keywords]
```# Zapcut AI - Chat-Based Campaign Creation PRD

## Overview

Replace the existing form-based ad preference input with a conversational AI agent. Users will have a natural chat dialogue with the agent to gather the 5 required preferences (style, audience, emotion, pacing, colors) before campaign generation.

---

## User Flow

1. User navigates to Brand List
2. User clicks "Create Campaign" button on a brand
3. Backend creates a new campaign session
4. Frontend redirects to chat interface
5. Chat interface loads with agent greeting (mentions brand details)
6. User and agent exchange messages to gather 5 preferences
7. Once all 5 fields collected, agent asks for confirmation
8. User confirms → Campaign marked as ready
9. Frontend redirects to campaign review page
10. Existing storyline generation flow continues (unchanged)

---

## Feature Requirements

### 1. Data Storage

**Store chat messages**:
- Each user-agent exchange should be persisted
- Track message sender (user or agent)
- Track timestamp
- Track any preferences extracted from each message

**Store extracted preferences**:
- After chat completes, save final 5 preferences to campaign
- Structure matches existing form data format
- Reuse this data for storyline generation (no changes to downstream pipeline)

---

### 2. Chat Interface

#### Opening Message
Agent greets user with:
```
"Hi! 👋 I'm your creative ad consultant, and I'm excited to help you 
create an amazing 30-second video ad.

I see you make {brand_description}—that's cool! 

To craft the perfect ad, I need to understand your vision. Don't worry about 
using fancy words—just describe what you're imagining. Let's start:

Who are you trying to reach with this ad?"
```

#### Question Flow
Ask about these 5 aspects in this order:
1. Target Audience (who should see this?)
2. Visual Style (what should it look/feel like?)
3. Emotion (what should people feel when watching?)
4. Pacing (how should it move? Fast? Slow? Smooth?)
5. Color Palette (what colors resonate with you?)

#### Agent Behavior
- Ask ONE question at a time
- Acknowledge user's previous response
- **Provide helpful examples for each aspect** to guide users without constraining them
  - Example for style: "Think of things like: minimalist and clean, bold and eye-catching, luxury and sophisticated, playful and fun, edgy and dramatic—or anything else you're picturing"
  - Example for emotion: "Like: making people excited, building trust, making them smile, feeling inspired—whatever matches your product"
- Be warm, conversational, enthusiastic (not robotic)
- Keep responses concise (2-3 sentences max)
- Use light emojis
- **Accept any description** from user—they don't need to match predefined options

#### Confirmation Message
When all 5 aspects gathered:
```
"Perfect! Let me recap what I'm picturing for your ad:

- Audience: {user_description_audience}
- Visual Style: {user_description_style}
- Emotion: {user_description_emotion}
- Pacing: {user_description_pacing}
- Color Palette: {user_description_colors}

Does that capture your vision? If yes, I'm ready to generate your ad! 🎬"
```

#### User Confirmation
After confirmation message, user clicks button to proceed to campaign generation.

---

### 3. Preference Extraction

**What to collect**:
- Gather free-form descriptions from user for each of the 5 aspects
- Users describe in their own words—no constraints or predefined options
- Accept any language, metaphors, examples, references

**Extraction approach**:
- Store user's raw descriptions as-is in database
- Do not force to canonical values
- Extract 2-3 **keywords/themes** from each description for use in storyline generation
  - Example: User says "energetic but not chaotic, like a music video vibe" → Keywords: "energetic", "music video", "dynamic but controlled"
  - Example: User says "young professionals who want to look cool at work" → Keywords: "young professionals", "aspirational", "workplace"

**How it works**:
1. Agent asks question with helpful examples
2. User responds freely
3. Agent acknowledges and extracts keywords internally
4. Store both: full user response + extracted keywords
5. Move to next aspect

**Handling unclear responses**:
- If user response is too vague (e.g., "I dunno, just make it good"), agent can:
  - Acknowledge: "I get it—let me make this easier"
  - Ask follow-up: "What's one word you'd use? Or what's an ad you've seen that you liked?"
  - Accept answer and move forward

**Progress tracking**:
- Display to user how many of 5 aspects collected
- Update after each message

---

### 4. Agent Implementation & Intelligence

**Technology**: Use **Langchain** with the following setup:
- Use Langchain's conversation chain with memory
- Agent role: Creative ad consultant gathering campaign vision
- LLM model: GPT-4o-mini
- Use Langchain's built-in tools for:
  - Extracting keywords from user descriptions
  - Tracking conversation progress
  - Determining when to move to next aspect

**Context awareness**:
- Know which aspects already collected
- Know which aspect to ask about next
- Reference brand details in conversation
- Acknowledge previous responses
- Track number of turns to detect if user is stuck/confused

**Field inference**:
- Extract keywords and themes from natural language descriptions
- Capture user intent even when expressed in their own words
- Build rich context understanding rather than forcing to predefined categories

**Agent System Prompt**:

```
You are a friendly, creative ad consultant at a professional video ad agency. 
Your role is to help users visualize and articulate their ideal video ad campaign 
in a natural, conversational way.

CRITICAL INFORMATION:
- Brand: {brand_name}
- Brand Description: {brand_description}
- Brand Images: User has uploaded 2 product images

YOUR TASK:
Gather 5 aspects of the user's vision through natural conversation:
1. Target Audience (who should see this ad?)
2. Visual Style (what should it look/feel like?)
3. Emotion (what should people feel?)
4. Pacing (how fast/slow should it move?)
5. Color Palette (what colors resonate?)

CURRENT PROGRESS:
- Collected: {aspects_collected}/5
- Already have: {list_of_collected_aspects}
- Next to ask: {next_aspect}

INSTRUCTIONS:

1. OPENING (first turn only):
   - Greet warmly
   - Show you understand their product
   - Make clear: no fancy vocabulary needed, they can describe however they want
   - Start with Target Audience

2. ASKING QUESTIONS:
   - Ask ONE aspect at a time
   - Use {next_aspect} to determine what to ask
   - Provide 3-4 helpful examples for the aspect
     - Examples for Style: "like minimalist and clean, bold and eye-catching, luxury and sophisticated, playful and fun, edgy and dramatic"
     - Examples for Emotion: "making people excited, building trust, making them smile, feeling inspired"
     - Examples for Pacing: "fast-paced and energetic, slow and elegant, smooth and flowing, dynamic build-up"
     - Examples for Audience: "think about age, profession, lifestyle, values, aspirations"
     - Examples for Colors: "bold and vibrant, dark and moody, light and airy, natural and earthy, warm tones, cool tones"
   - Make clear: these are just suggestions, they can describe differently

3. ACKNOWLEDGING RESPONSES:
   - Thank them for their response
   - Briefly reflect back what they said (shows you're listening)
   - Extract the key sentiment/keywords internally
   - Example: "Got it—so luxury but approachable. I can see that."

4. MOVING FORWARD:
   - After acknowledging, transition naturally to next aspect
   - Keep responses conversational (2-3 sentences max)
   - Use light emojis occasionally

5. WHEN ALL 5 COLLECTED:
   - Show confirmation message with all 5 aspects recap
   - Use their exact words/descriptions (not your interpretation)
   - Example format:
     "Perfect! Let me recap what I'm picturing:
      - Audience: {their_description}
      - Visual Style: {their_description}
      - Emotion: {their_description}
      - Pacing: {their_description}
      - Colors: {their_description}
      
      Does that capture your vision?"
   - Wait for "yes" confirmation from user
   - Then signal completion (user will click button to proceed)

6. HANDLING UNCLEAR RESPONSES:
   - If response is too vague ("I dunno", "something good", "I'm not sure"):
     - Stay warm and encouraging
     - Offer to make it easier: "I get it—let me make this simpler"
     - Ask for one word, a reference, or an ad they liked
     - Accept their answer and move forward (don't get stuck)
   - Never force them to choose from predefined options
   - Let them express themselves freely

7. TONE & PERSONALITY:
   - Warm, encouraging, enthusiastic
   - Not robotic or corporate
   - Show genuine interest in their product
   - Use "we" and "I" naturally (e.g., "I can see that", "we're building")
   - Be concise but friendly
   - Light emoji use (but not overdone)

8. REMEMBER:
   - They don't need perfect vocabulary
   - Raw descriptions are MORE valuable than polished ones
   - Your job is to understand intent, not judge expression
   - This should feel like talking to a creative partner, not filling out a form
```

**Why Langchain**:
- Handles conversation memory automatically (no manual state management)
- Makes it easy to track which aspects collected
- Can use tools for keyword extraction and progress tracking
- Cleaner code for multi-turn conversations
- Built-in error handling for malformed responses

---

### 5. Integration with Existing System

#### No Changes Required
- Existing campaign generation workflow
- Existing video/audio generation

#### Changes Required
- Add persistent storage for chat messages and user descriptions
- Add keyword extraction logic
- Add chat UI page
- Modify "Create Campaign" button to start chat instead of form
- **Update storyline generation to use extracted keywords instead of predefined form values**

#### Data Handoff
- After chat completes, save 5 free-form descriptions to campaign
- Extract and save 2-3 keywords for each aspect
- When calling storyline generation, pass:
  - **User descriptions** (raw text)
  - **Extracted keywords** (for context)
- No longer feed predefined form values to storyline generation
- Storyline generation uses natural language descriptions for richer context

---

## Preference Options (Reference)

### Style
- Modern & Sleek
- Energetic & Fun
- Luxurious & Sophisticated
- Minimal & Clean
- Bold & Dramatic

### Audience
- Young Adults (18-25)
- Professionals (25-40)
- Families
- Seniors (50+)
- Everyone

### Emotion
- Excitement
- Trust & Reliability
- Joy & Happiness
- Luxury & Prestige
- Innovation

### Pacing
- Fast-paced & Exciting
- Slow & Elegant
- Dynamic Build-up
- Steady & Calm

### Colors
- Bold & Vibrant
- Dark & Moody
- Light & Airy
- Natural & Earthy
- Match Product Colors

---

## Success Criteria

- ✅ User can create campaign via chat instead of form
- ✅ Agent collects all 5 preferences through conversation
- ✅ Extracted preferences match existing form value format
- ✅ Agent asks questions in logical order
- ✅ Chat completes and transitions to campaign generation
- ✅ Campaign generation works end-to-end (chat → storyline → video)
- ✅ Chat messages persisted for audit/future reference