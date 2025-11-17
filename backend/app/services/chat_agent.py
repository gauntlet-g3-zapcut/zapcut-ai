"""Chat agent service using Langchain."""
import logging
import json
from typing import Dict, List, Tuple, Optional
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from app.config import settings

logger = logging.getLogger(__name__)

# Define the 5 aspects in order
ASPECTS = ["audience", "style", "emotion", "pacing", "colors"]
ASPECT_NAMES = {
    "audience": "Target Audience",
    "style": "Visual Style",
    "emotion": "Emotion",
    "pacing": "Pacing",
    "colors": "Color Palette"
}

ASPECT_EXAMPLES = {
    "audience": "think about age, profession, lifestyle, values, aspirations",
    "style": "like minimalist and clean, bold and eye-catching, luxury and sophisticated, playful and fun, edgy and dramatic",
    "emotion": "making people excited, building trust, making them smile, feeling inspired",
    "pacing": "fast-paced and energetic, slow and elegant, smooth and flowing, dynamic build-up",
    "colors": "bold and vibrant, dark and moody, light and airy, natural and earthy, warm tones, cool tones"
}


def build_system_prompt(
    brand_name: str,
    brand_description: str,
    collected_aspects: List[str],
    next_aspect: Optional[str]
) -> str:
    """Build the system prompt for the agent."""
    aspects_collected = len(collected_aspects)
    list_of_collected = ", ".join([ASPECT_NAMES.get(a, a) for a in collected_aspects]) if collected_aspects else "None"
    next_to_ask = ASPECT_NAMES.get(next_aspect, next_aspect) if next_aspect else "None"
    
    prompt = f"""You are a friendly, creative ad consultant at a professional video ad agency. 
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
- Already have: {list_of_collected}
- Next to ask: {next_to_ask}

INSTRUCTIONS:

1. OPENING (first turn only):
   - Greet warmly
   - Show you understand their product
   - Make clear: no fancy vocabulary needed, they can describe however they want
   - Start with Target Audience

2. ASKING QUESTIONS:
   - Ask ONE aspect at a time
   - Use the next aspect to determine what to ask
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
      - Audience: [use their exact description]
      - Visual Style: [use their exact description]
      - Emotion: [use their exact description]
      - Pacing: [use their exact description]
      - Colors: [use their exact description]
      
      Let's get started generating the script! 🎬"
   - Signal completion (user will click button to proceed)

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
"""
    return prompt


def extract_keywords(description: str, aspect: str) -> List[str]:
    """Extract 2-3 keywords from a user description using OpenAI."""
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set, using simple keyword extraction")
        # Fallback: simple extraction
        words = description.lower().split()
        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "should", "could", "may", "might", "must", "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "what", "which", "who", "whom", "whose", "where", "when", "why", "how", "all", "each", "every", "both", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "just", "now"}
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return keywords[:3] if keywords else [description[:50]]
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""Extract 2-3 key words or short phrases (2-4 words max each) that capture the essence of this description for a video ad {aspect}:

Description: "{description}"

Return ONLY a JSON array of 2-3 keywords/phrases, nothing else. Example: ["keyword1", "keyword2", "keyword3"]
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts keywords from descriptions. Return only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        # Try to parse as JSON object first
        try:
            result = json.loads(content)
            if isinstance(result, dict):
                # If it's a dict, look for common keys
                keywords = result.get("keywords", result.get("key_words", list(result.values())[0] if result else []))
            else:
                keywords = result
        except:
            # If not JSON object, try as array
            keywords = json.loads(content) if content.startswith("[") else [description[:50]]
        
        if not isinstance(keywords, list):
            keywords = [str(keywords)]
        
        # Ensure we have 2-3 keywords
        keywords = keywords[:3] if len(keywords) > 3 else keywords
        if len(keywords) < 2 and description:
            # Fallback: split description into meaningful chunks
            words = description.split()[:3]
            keywords.extend([w for w in words if w not in keywords])
        
        return keywords[:3] if keywords else [description[:50]]
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        # Fallback
        words = description.split()[:3]
        return words if words else [description[:50]]


class ChatAgent:
    """Chat agent for gathering campaign preferences."""
    
    def __init__(self, brand_name: str, brand_description: str):
        """Initialize the chat agent."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for chat agent")
        
        self.brand_name = brand_name
        self.brand_description = brand_description
        self.collected_aspects: List[str] = []
        self.aspect_descriptions: Dict[str, str] = {}
        self.memory = ConversationBufferMemory()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
        self.conversation = None
        self._initialize_conversation()
    
    def _initialize_conversation(self):
        """Initialize the conversation chain."""
        system_prompt = build_system_prompt(
            self.brand_name,
            self.brand_description,
            self.collected_aspects,
            self._get_next_aspect()
        )
        
        # Use a simpler approach with ConversationChain but with proper template
        from langchain.prompts import PromptTemplate
        from langchain.chains import ConversationChain
        
        # Create template that only uses history and input (no other variables)
        prompt_template = PromptTemplate(
            input_variables=["history", "input"],
            template=f"""{system_prompt}

{{history}}
Human: {{input}}
Assistant:"""
        )
        
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=prompt_template,
            verbose=False
        )
    
    def _get_next_aspect(self) -> Optional[str]:
        """Get the next aspect to collect."""
        for aspect in ASPECTS:
            if aspect not in self.collected_aspects:
                return aspect
        return None
    
    def _update_system_prompt(self):
        """Update the system prompt with current progress."""
        # Reinitialize conversation with updated prompt
        self.memory.clear()
        self._initialize_conversation()
    
    def process_message(self, user_message: str) -> Tuple[str, Dict[str, any]]:
        """
        Process a user message and return agent response.
        
        Returns:
            Tuple of (agent_response, metadata)
            metadata contains:
                - progress: number of aspects collected
                - collected_aspects: list of collected aspect names
                - next_aspect: next aspect to ask about
                - is_complete: whether all 5 aspects are collected
                - extracted_preferences: dict of aspect -> {description, keywords}
        """
        # Get agent response using predict method
        response_text = self.conversation.predict(input=user_message)
        
        # Check if we should extract preferences from this exchange
        # We'll use a simple heuristic: if the response acknowledges and moves forward,
        # we likely collected the current aspect
        next_aspect = self._get_next_aspect()
        
        # Try to detect if user provided an answer for the current aspect
        # This is a heuristic - in a real implementation, we might use a more sophisticated approach
        # For now, we'll extract after the agent acknowledges and moves to next
        
        metadata = {
            "progress": len(self.collected_aspects),
            "collected_aspects": [ASPECT_NAMES.get(a, a) for a in self.collected_aspects],
            "next_aspect": ASPECT_NAMES.get(next_aspect, next_aspect) if next_aspect else None,
            "is_complete": len(self.collected_aspects) >= 5,
            "extracted_preferences": {}
        }
        
        return response_text, metadata
    
    def extract_and_store_preference(self, aspect: str, user_description: str):
        """Extract and store a preference for a specific aspect."""
        if aspect not in ASPECTS:
            logger.warning(f"Invalid aspect: {aspect}")
            return
        
        if aspect in self.collected_aspects:
            logger.warning(f"Aspect {aspect} already collected")
            return
        
        keywords = extract_keywords(user_description, aspect)
        self.aspect_descriptions[aspect] = user_description
        self.collected_aspects.append(aspect)
        
        # Update system prompt for next turn
        self._update_system_prompt()
        
        return {
            "description": user_description,
            "keywords": keywords
        }
    
    def get_extracted_preferences(self) -> Dict[str, Dict[str, any]]:
        """Get all extracted preferences."""
        preferences = {}
        for aspect in self.collected_aspects:
            description = self.aspect_descriptions.get(aspect, "")
            keywords = extract_keywords(description, aspect) if description else []
            preferences[aspect] = {
                "description": description,
                "keywords": keywords
            }
        return preferences
    
    def is_complete(self) -> bool:
        """Check if all 5 aspects have been collected."""
        return len(self.collected_aspects) >= 5
    
    def load_conversation_history(self, messages: List[Dict[str, str]]):
        """Load conversation history into memory."""
        # Skip if no messages to load - avoids unnecessary reinitialization
        if not messages:
            return
            
        self.memory.clear()
        for msg in messages:
            if msg.get("role") == "user":
                self.memory.chat_memory.add_user_message(msg.get("content", ""))
            elif msg.get("role") == "assistant":
                self.memory.chat_memory.add_ai_message(msg.get("content", ""))
        
        # Reinitialize conversation with loaded history
        self._initialize_conversation()
    
    def get_initial_greeting(self) -> str:
        """Get a template-based initial greeting without making an API call."""
        next_aspect = self._get_next_aspect()
        aspect_name = ASPECT_NAMES.get(next_aspect, next_aspect) if next_aspect else "preferences"
        aspect_name_lower = aspect_name.lower()
        
        greeting = f"""Hey there! 👋 

I'm excited to help you create an amazing video ad for {self.brand_name}!
No fancy vocabulary needed—just describe what you're picturing in your own words, and we'll build something great together. Let's start with your {aspect_name_lower}. {ASPECT_EXAMPLES.get(next_aspect, "Tell me what you're thinking!")}
What comes to mind?"""
        
        return greeting.strip()

