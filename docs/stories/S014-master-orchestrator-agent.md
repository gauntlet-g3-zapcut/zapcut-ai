# Story S014: Master Orchestrator Agent Implementation

## Epic
[E003: Creative Brief Chat Interface](../Epics/E003-creative-brief-chat.md)

## Story
**As a** user  
**I want to** be guided through video creation by an AI assistant  
**So that** I can easily provide all necessary information without confusion

## Priority
**P0 - MVP Critical**

## Size
**L** (3-5 days)

## Description
Implement Master Orchestrator Agent that guides users through stage-based workflow for creating video ads. The orchestrator uses Claude to understand user intent, validate inputs, and transition between stages naturally.

## Acceptance Criteria
- [ ] Orchestrator agent responds to user messages in chat interface
- [ ] Agent progresses through 7 defined stages sequentially
- [ ] User cannot skip required stages
- [ ] Agent validates inputs before stage transitions
- [ ] Agent blocks unsafe/inappropriate requests
- [ ] Agent maintains conversation context across messages
- [ ] Agent provides helpful error messages for invalid inputs
- [ ] Agent summarizes collected information at final review

## Technical Details

### Stage Flow
```
1. collect_brand_info     → Brand name, product type
2. collect_product_info   → Description, audience, benefit
3. collect_assets         → Upload 2-4 product images
4. collect_scenes         → Creative direction, preferences
5. final_review           → Confirm details
6. generate_video         → Trigger pipeline
7. export_video           → Download/publish options
```

### System Architecture
```python
# backend/app/agents/orchestrator.py

from anthropic import Anthropic
from typing import Dict, List, Optional
from enum import Enum

class OrchestratorStage(Enum):
    COLLECT_BRAND_INFO = "collect_brand_info"
    COLLECT_PRODUCT_INFO = "collect_product_info"
    COLLECT_ASSETS = "collect_assets"
    COLLECT_SCENES = "collect_scenes"
    FINAL_REVIEW = "final_review"
    GENERATE_VIDEO = "generate_video"
    EXPORT_VIDEO = "export_video"

class OrchestratorState:
    """Maintains conversation state"""
    stage: OrchestratorStage
    brand: Dict = {}
    product: Dict = {}
    assets: List[str] = []
    scenes: Dict = {}
    safety_flags: List[str] = []
    
class MasterOrchestrator:
    """
    Master Orchestrator Agent that guides users through video creation.
    Uses Claude to understand intent and progress through stages.
    """
    
    def __init__(self, anthropic_api_key: str):
        self.client = Anthropic(api_key=anthropic_api_key)
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        return """You are the Zapcut Orchestrator, the main assistant for an AI video generation platform.

Your job:
- Guide users through a stage-based workflow to create professional video ads
- Collect brand info, product details, visual assets, and creative direction
- Never skip forward if required information is missing
- Always respond in a friendly, conversational tone
- Control the following stages: collect_brand_info, collect_product_info, collect_assets, collect_scenes, final_review, generate_video, export_video

Stage Transitions:
- Only move to next stage when current stage requirements are met
- When ready to move forward, include: NEXT_STAGE: <stage_name>
- If user provides insufficient info, ask clarifying questions

Safety:
- Refuse unsafe requests (violence, nudity, drugs, hate speech)
- Suggest safe alternatives when blocking content
- Never generate content featuring real people without consent

Response Format:
- Be concise but friendly (2-4 sentences per response)
- Use emojis sparingly (1-2 per message)
- Ask open-ended questions to understand user intent
- Provide examples when helpful

Current State: {state_json}
Current Stage: {current_stage}
"""
    
    async def process_message(
        self, 
        user_message: str, 
        state: OrchestratorState,
        chat_history: List[Dict]
    ) -> Dict:
        """
        Process user message and return agent response.
        
        Returns:
            {
                "message": str,  # Response to display to user
                "next_stage": Optional[str],  # Stage transition if applicable
                "state_updates": Dict,  # Updates to apply to state
                "actions": List[str]  # Actions to trigger (e.g., "generate_video")
            }
        """
        
        # Build messages for Claude
        messages = self._format_chat_history(chat_history)
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Claude
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            system=self.system_prompt.format(
                state_json=state.to_json(),
                current_stage=state.stage.value
            ),
            messages=messages
        )
        
        # Parse response
        response_text = response.content[0].text
        result = self._parse_response(response_text, state)
        
        return result
    
    def _parse_response(
        self, 
        response_text: str, 
        state: OrchestratorState
    ) -> Dict:
        """
        Parse Claude's response to extract:
        - Message to display
        - Stage transition
        - State updates
        - Actions to trigger
        """
        
        result = {
            "message": response_text,
            "next_stage": None,
            "state_updates": {},
            "actions": []
        }
        
        # Check for stage transition
        if "NEXT_STAGE:" in response_text:
            stage_match = re.search(r"NEXT_STAGE:\s*(\w+)", response_text)
            if stage_match:
                next_stage = stage_match.group(1)
                result["next_stage"] = next_stage
                # Remove stage transition from displayed message
                result["message"] = response_text.replace(
                    f"NEXT_STAGE: {next_stage}", 
                    ""
                ).strip()
        
        # Extract structured data based on stage
        if state.stage == OrchestratorStage.COLLECT_BRAND_INFO:
            # Try to extract brand name
            brand_match = re.search(
                r"brand(?:\s+name)?(?:\s+is)?:\s*([^\n]+)", 
                response_text, 
                re.IGNORECASE
            )
            if brand_match:
                result["state_updates"]["brand_name"] = brand_match.group(1).strip()
        
        elif state.stage == OrchestratorStage.FINAL_REVIEW:
            # Check if user confirmed
            if any(word in response_text.lower() for word in ["yes", "confirmed", "looks good", "perfect"]):
                result["actions"].append("generate_video")
        
        return result
    
    def _format_chat_history(self, chat_history: List[Dict]) -> List[Dict]:
        """Format chat history for Claude API"""
        formatted = []
        for msg in chat_history:
            formatted.append({
                "role": "user" if msg["sender"] == "user" else "assistant",
                "content": msg["message"]
            })
        return formatted

    def validate_stage_transition(
        self, 
        current_stage: OrchestratorStage, 
        next_stage: OrchestratorStage, 
        state: OrchestratorState
    ) -> bool:
        """
        Validate that stage transition is allowed based on collected data.
        """
        
        if current_stage == OrchestratorStage.COLLECT_BRAND_INFO:
            return bool(state.brand.get("name"))
        
        elif current_stage == OrchestratorStage.COLLECT_PRODUCT_INFO:
            return (
                bool(state.product.get("description")) and
                bool(state.product.get("target_audience"))
            )
        
        elif current_stage == OrchestratorStage.COLLECT_ASSETS:
            return len(state.assets) >= 2  # Minimum 2 images
        
        elif current_stage == OrchestratorStage.COLLECT_SCENES:
            return bool(state.scenes.get("creative_direction"))
        
        elif current_stage == OrchestratorStage.FINAL_REVIEW:
            # All required data collected
            return True
        
        return False
```

### API Endpoint
```python
# backend/app/api/chat.py

from fastapi import APIRouter, Depends, HTTPException
from app.agents.orchestrator import MasterOrchestrator, OrchestratorState
from app.models import User, ChatMessage
from app.deps import get_current_user

router = APIRouter()

@router.post("/chat/message")
async def send_chat_message(
    message: str,
    session_id: str,
    user: User = Depends(get_current_user)
):
    """
    Process user's chat message and return orchestrator response.
    """
    
    # Get or create session
    session = await ChatSession.get_or_create(session_id, user.id)
    
    # Load state
    state = OrchestratorState.from_dict(session.state)
    
    # Get chat history
    chat_history = await ChatMessage.get_history(session_id, limit=20)
    
    # Process message
    orchestrator = MasterOrchestrator(settings.ANTHROPIC_API_KEY)
    result = await orchestrator.process_message(
        user_message=message,
        state=state,
        chat_history=chat_history
    )
    
    # Validate stage transition
    if result["next_stage"]:
        current_stage = state.stage
        next_stage = OrchestratorStage(result["next_stage"])
        
        if not orchestrator.validate_stage_transition(current_stage, next_stage, state):
            raise HTTPException(
                status_code=400,
                detail="Cannot transition to next stage: missing required information"
            )
        
        state.stage = next_stage
    
    # Update state
    for key, value in result["state_updates"].items():
        setattr(state, key, value)
    
    # Save session state
    session.state = state.to_dict()
    await session.save()
    
    # Save chat messages
    await ChatMessage.create(
        session_id=session_id,
        sender="user",
        message=message
    )
    await ChatMessage.create(
        session_id=session_id,
        sender="assistant",
        message=result["message"]
    )
    
    # Trigger actions
    if "generate_video" in result["actions"]:
        # Enqueue video generation job
        job_id = await enqueue_video_generation(session.project_id, state)
        result["job_id"] = job_id
    
    return {
        "message": result["message"],
        "stage": state.stage.value,
        "actions": result["actions"]
    }
```

### Frontend Integration
```typescript
// src/store/chatStore.ts
import { create } from 'zustand';

interface ChatState {
  messages: ChatMessage[];
  currentStage: string;
  isLoading: boolean;
  
  sendMessage: (message: string) => Promise<void>;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  currentStage: 'collect_brand_info',
  isLoading: false,
  
  sendMessage: async (message: string) => {
    set({ isLoading: true });
    
    // Add user message optimistically
    set(state => ({
      messages: [...state.messages, {
        sender: 'user',
        message,
        timestamp: new Date()
      }]
    }));
    
    try {
      const response = await fetch('/api/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: getSessionId() })
      });
      
      const data = await response.json();
      
      // Add assistant response
      set(state => ({
        messages: [...state.messages, {
          sender: 'assistant',
          message: data.message,
          timestamp: new Date()
        }],
        currentStage: data.stage
      }));
      
      // Trigger actions
      if (data.actions.includes('generate_video')) {
        // Redirect to generation progress page
        window.location.href = `/generate/${data.job_id}`;
      }
      
    } catch (error) {
      console.error('Chat error:', error);
      // Add error message
      set(state => ({
        messages: [...state.messages, {
          sender: 'assistant',
          message: 'Sorry, something went wrong. Please try again.',
          timestamp: new Date()
        }]
      }));
    } finally {
      set({ isLoading: false });
    }
  },
  
  reset: () => {
    set({
      messages: [],
      currentStage: 'collect_brand_info'
    });
  }
}));
```

## Testing Plan

### Unit Tests
```python
# tests/unit/test_orchestrator.py

async def test_orchestrator_stage_progression():
    """Test that orchestrator progresses through stages correctly"""
    orchestrator = MasterOrchestrator(api_key="test")
    state = OrchestratorState(stage=OrchestratorStage.COLLECT_BRAND_INFO)
    
    # User provides brand name
    result = await orchestrator.process_message(
        user_message="My brand is Luna Coffee",
        state=state,
        chat_history=[]
    )
    
    assert result["state_updates"]["brand_name"] == "Luna Coffee"
    assert result["next_stage"] == "collect_product_info"

async def test_orchestrator_blocks_stage_skip():
    """Test that orchestrator prevents skipping required stages"""
    orchestrator = MasterOrchestrator(api_key="test")
    state = OrchestratorState(stage=OrchestratorStage.COLLECT_BRAND_INFO)
    # Brand name not provided
    
    can_transition = orchestrator.validate_stage_transition(
        current_stage=OrchestratorStage.COLLECT_BRAND_INFO,
        next_stage=OrchestratorStage.COLLECT_PRODUCT_INFO,
        state=state
    )
    
    assert can_transition is False
```

### Integration Tests
```python
async def test_full_conversation_flow(test_client):
    """Test complete conversation from start to generation"""
    
    # Stage 1: Brand info
    response = await test_client.post("/api/chat/message", json={
        "message": "Luna Coffee",
        "session_id": "test-session"
    })
    assert response.json()["stage"] == "collect_brand_info"
    
    # Stage 2: Product info
    response = await test_client.post("/api/chat/message", json={
        "message": "Organic cold brew concentrate for busy professionals",
        "session_id": "test-session"
    })
    assert response.json()["stage"] == "collect_product_info"
    
    # ... continue through all stages
```

## Dependencies
- Claude API (Anthropic)
- FastAPI backend
- Chat UI component (S013)
- Session/state management

## Definition of Done
- [ ] Orchestrator agent code implemented and tested
- [ ] API endpoint created and documented
- [ ] Unit tests passing (>90% coverage)
- [ ] Integration tests passing
- [ ] Manual QA completed (full conversation flow)
- [ ] Code reviewed and merged

---
**Created**: 2025-11-15  
**Assigned To**: Backend AI Team  
**Status**: Ready
