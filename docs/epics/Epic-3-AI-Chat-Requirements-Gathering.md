# Epic 3: AI Chat & Requirements Gathering

**Status:** Not Started
**Priority:** P0 (MVP)
**Estimated Effort:** 2-3 weeks
**Dependencies:** Epic 1 (Infrastructure), Epic 2 (Brands)

---

## Epic Overview

### Value Proposition
Users can naturally describe their video requirements through AI conversation, making complex video specification accessible without technical knowledge.

### Success Criteria
- [ ] Users can start chat session from brand dashboard
- [ ] AI asks exactly 5 follow-up questions to gather requirements
- [ ] Requirements extracted: target audience, platform, duration, key message, CTA
- [ ] Chat history persists and is resume-able
- [ ] User can proceed to script generation after conversation
- [ ] Complete conversational UI with typing indicators and real-time responses

### Demo Scenario
1. User clicks brand card from dashboard
2. Chat interface opens with AI greeting
3. User describes video concept
4. AI asks 5 targeted questions
5. User answers each question
6. AI confirms all requirements gathered
7. "Generate Script" button appears
8. User clicks → Proceeds to Epic 4

---

## User Stories

### Story 3.1: Create Ad Project
**As a** user
**I want** to start a new video project for my brand
**So that** I can begin creating content

**Acceptance Criteria:**
- [ ] Click

ing brand card creates new AdProject
- [ ] Project linked to brand and user
- [ ] Project has unique ID
- [ ] Initial status: "chat"
- [ ] Redirects to chat interface

**Frontend:**
```typescript
// Route
/brands → Click brand card → /brands/:brandId/chat

// State
adProjectStore.createProject(brandId)
```

**Backend:**
```python
POST /api/brands/:brandId/projects
Response: { id, brand_id, user_id, status: "chat" }
```

**Database:**
```sql
CREATE TABLE ad_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'chat',
    ad_details JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Tasks:**
- [ ] Create ad_projects table
- [ ] Implement POST endpoint
- [ ] Update BrandCard click handler
- [ ] Test project creation

---

### Story 3.2: Chat Interface Layout
**As a** user
**I want** a clean chat interface
**So that** I can focus on the conversation

**Acceptance Criteria:**
- [ ] Header shows brand name and "Step 1 of 3"
- [ ] Back button to brands dashboard
- [ ] Scrollable message area
- [ ] Fixed input at bottom
- [ ] Glassmorphism styling
- [ ] Auto-scroll to latest message

**Frontend:**
```typescript
// Pages
- ChatPage.tsx
  - ChatHeader
  - ChatMessages (scrollable)
  - ChatInput (fixed bottom)

// Routes
GET /brands/:brandId/chat
```

**Backend:** N/A (UI only)
**Database:** N/A

**Tasks:**
- [ ] Create ChatPage component
- [ ] Create ChatHeader component
- [ ] Create ChatMessages component
- [ ] Create ChatInput component
- [ ] Add auto-scroll logic
- [ ] Test responsive layout

---

### Story 3.3: AI Greeting Message
**As a** user
**I want** to receive an initial greeting from AI
**So that** I know where to start

**Acceptance Criteria:**
- [ ] First message auto-sent on chat load
- [ ] Message includes brand name
- [ ] Friendly, inviting tone
- [ ] Displays immediately (no delay)

**Frontend:**
```typescript
// On mount
useEffect(() => {
  if (messages.length === 0) {
    sendInitialGreeting()
  }
}, [])
```

**Backend:**
```python
GET /api/projects/:projectId/messages
Response: ChatMessage[]

# If empty, return initial message
```

**Database:**
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_project_id UUID REFERENCES ad_projects(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_project ON chat_messages(ad_project_id);
```

**Initial Message:**
```
Hi! I'm excited to help you create an amazing ad for [Brand Name].
To get started, could you tell me a bit about what you want to achieve with this ad?
```

**Tasks:**
- [ ] Create chat_messages table
- [ ] Implement greeting logic
- [ ] Test initial message display

---

### Story 3.4: User Message Submission
**As a** user
**I want** to send messages to AI
**So that** I can describe my video concept

**Acceptance Criteria:**
- [ ] Input field accepts text
- [ ] Enter key or Send button submits
- [ ] Message appears immediately (optimistic UI)
- [ ] Input clears after send
- [ ] Character limit: 2000
- [ ] Submit disabled while AI is responding

**Frontend:**
```typescript
// State
const [inputValue, setInputValue] = useState('')
const [isAIResponding, setIsAIResponding] = useState(false)

// Submit
const handleSubmit = async () => {
  const userMessage = { role: 'user', content: inputValue }
  addMessage(userMessage) // Optimistic
  setInputValue('')
  setIsAIResponding(true)

  await adProjectStore.sendMessage(projectId, inputValue)

  setIsAIResponding(false)
}
```

**Backend:**
```python
POST /api/projects/:projectId/chat
Body: { message: string }
Response: {
  user_message: ChatMessage,
  ai_response: ChatMessage,
  question_count: number
}
```

**Database:**
```sql
INSERT INTO chat_messages (ad_project_id, role, content)
VALUES (?, 'user', ?);
```

**Tasks:**
- [ ] Implement chat input logic
- [ ] Add optimistic UI updates
- [ ] Implement POST /chat endpoint
- [ ] Test message submission

---

### Story 3.5: AI Response Generation
**As a** user
**I want** AI to respond to my messages
**So that** I can have a guided conversation

**Acceptance Criteria:**
- [ ] AI responds within 5 seconds
- [ ] Response is contextually relevant
- [ ] Response considers brand voice
- [ ] Typing indicator shown while generating
- [ ] Response saved to database
- [ ] Error handling for API failures

**Frontend:**
```typescript
// Components
- TypingIndicator.tsx

// Display while isAIResponding === true
```

**Backend:**
```python
# OpenAI Integration
import openai

async def generate_ai_response(project_id, user_message):
    # Get conversation history
    messages = get_chat_history(project_id)

    # Get brand context
    brand = get_brand_for_project(project_id)

    # Build prompt
    system_prompt = f"""You are an expert ad strategist helping users create video ads.
    Brand: {brand.title}
    Brand Description: {brand.description}

    Ask exactly 5 follow-up questions to gather:
    1. Target audience
    2. Ad platform (Instagram, Facebook, TikTok, YouTube)
    3. Ad duration (15s, 30s, 60s)
    4. Key message/USP
    5. Call-to-action

    Be conversational, friendly, and concise."""

    # Call OpenAI
    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            *messages,
            {"role": "user", "content": user_message}
        ]
    )

    ai_message = response.choices[0].message.content

    # Save to DB
    save_message(project_id, 'assistant', ai_message)

    return ai_message
```

**Database:**
```sql
INSERT INTO chat_messages (ad_project_id, role, content)
VALUES (?, 'assistant', ?);
```

**Tasks:**
- [ ] Integrate OpenAI API
- [ ] Create system prompt
- [ ] Implement response generation
- [ ] Add typing indicator
- [ ] Test AI responses
- [ ] Test error handling

---

### Story 3.6: 5-Question Flow Logic
**As a** user
**I want** AI to ask exactly 5 questions
**So that** I provide all necessary information

**Acceptance Criteria:**
- [ ] AI tracks question count
- [ ] After 5 questions answered, AI confirms completion
- [ ] Questions cover: audience, platform, duration, message, CTA
- [ ] User can answer in any order
- [ ] AI adapts questions based on previous answers

**Frontend:**
```typescript
// Display question count
<ProgressIndicator currentStep={questionCount} totalSteps={5} />
```

**Backend:**
```python
# Track in ad_details JSONB
async def update_ad_details(project_id, new_info):
    project = get_project(project_id)

    # Extract structured info from conversation
    ad_details = project.ad_details or {}

    # Update fields based on AI extraction
    if 'target_audience' in new_info:
        ad_details['target_audience'] = new_info['target_audience']

    # ... similar for other fields

    # Update database
    update_project(project_id, {'ad_details': ad_details})

    # Check if all 5 questions answered
    required_fields = ['target_audience', 'ad_platform', 'ad_duration', 'key_message', 'call_to_action']
    all_answered = all(field in ad_details for field in required_fields)

    if all_answered:
        return {'complete': True, 'message': "Perfect! I have everything I need."}
```

**Database:**
```sql
-- ad_details JSONB structure
{
  "target_audience": "young athletes, 18-25",
  "ad_platform": "instagram",
  "ad_duration": 30,
  "key_message": "Performance and style combined",
  "call_to_action": "Shop now"
}
```

**Tasks:**
- [ ] Implement question tracking
- [ ] Add structured data extraction
- [ ] Update ad_details JSONB
- [ ] Test 5-question flow
- [ ] Test completion detection

---

### Story 3.7: Chat History Persistence
**As a** user
**I want** my conversation to be saved
**So that** I can return to it later

**Acceptance Criteria:**
- [ ] All messages saved to database
- [ ] Chat loads from database on page refresh
- [ ] Messages displayed in chronological order
- [ ] Timestamps shown for each message

**Frontend:**
```typescript
// On mount
useEffect(() => {
  fetchChatHistory(projectId)
}, [projectId])
```

**Backend:**
```python
GET /api/projects/:projectId/messages
Response: ChatMessage[]

SELECT * FROM chat_messages
WHERE ad_project_id = ?
ORDER BY created_at ASC;
```

**Database:** (Already created in Story 3.3)

**Tasks:**
- [ ] Implement GET /messages endpoint
- [ ] Load messages on mount
- [ ] Test persistence across refresh

---

### Story 3.8: Proceed to Script Generation
**As a** user
**I want** to proceed to script generation after conversation
**So that** I can create my video

**Acceptance Criteria:**
- [ ] "Generate Script" button appears after 5 questions
- [ ] Button disabled until all requirements gathered
- [ ] Click transitions to script review page (Epic 4)
- [ ] Project status updated to "script"

**Frontend:**
```typescript
// Conditional button
{allRequirementsGathered && (
  <PrimaryButton onClick={generateScript}>
    Generate Script →
  </PrimaryButton>
)}

// Navigate
navigate(`/brands/${brandId}/projects/${projectId}/script`)
```

**Backend:**
```python
POST /api/projects/:projectId/generate-script
Response: { script_id, status: "generating" }

# Update project status
UPDATE ad_projects
SET status = 'script'
WHERE id = ?;
```

**Database:**
```sql
-- Status transition: 'chat' → 'script'
```

**Tasks:**
- [ ] Add conditional button
- [ ] Implement navigation
- [ ] Update project status
- [ ] Test transition to Epic 4

---

## Database Schema

```sql
-- Migration 003: Add ad projects and chat

CREATE TABLE ad_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    brand_id UUID REFERENCES brands(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'chat',
    ad_details JSONB,
    zapcut_project_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_project_id UUID REFERENCES ad_projects(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ad_projects_user ON ad_projects(user_id);
CREATE INDEX idx_ad_projects_brand ON ad_projects(brand_id);
CREATE INDEX idx_chat_messages_project ON chat_messages(ad_project_id);
```

---

## API Endpoints

```
POST /api/brands/:brandId/projects
GET /api/projects/:projectId
GET /api/projects/:projectId/messages
POST /api/projects/:projectId/chat
POST /api/projects/:projectId/generate-script
```

---

## Frontend Routes

```
/brands/:brandId/chat → ChatPage (protected)
```

---

## State Management

### adProjectStore
```typescript
interface AdProjectStore {
  currentProject: AdProject | null
  messages: ChatMessage[]
  isAIResponding: boolean
  questionCount: number

  createProject: (brandId) => Promise<AdProject>
  sendMessage: (projectId, content) => Promise<void>
  fetchMessages: (projectId) => Promise<void>
}
```

---

## Testing Strategy

### Frontend Tests
- Chat UI component tests
- Message submission tests
- Auto-scroll tests
- Progress indicator tests

### Backend Tests
- OpenAI integration tests
- Message storage tests
- Structured data extraction tests
- 5-question flow tests

### Integration Tests
- End-to-end chat flow
- Conversation → Script generation transition

---

## Definition of Done

- [ ] All user stories completed
- [ ] Chat interface fully functional
- [ ] AI responses natural and relevant
- [ ] 5-question flow works correctly
- [ ] Requirements extracted accurately
- [ ] Chat persists and resumes correctly
- [ ] Transition to Epic 4 works
- [ ] Code deployed to staging
- [ ] Demo scenario executable

---

## Dependencies

**External:**
- OpenAI API key
- OpenAI GPT-4 access

**Internal:**
- Epic 2 (need brands to chat about)

---

## References

- **PRD:** `/docs/plans/AIVP_PRD.md` - Section 3.3 (Chat Interface)
- **UI Spec:** `/docs/plans/AIVP_UISpecification.md` - Screen 5-6
