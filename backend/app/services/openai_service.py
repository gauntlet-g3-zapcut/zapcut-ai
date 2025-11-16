from openai import OpenAI
from app.config import settings

# Lazy initialization - only create client when needed and if API key is available
_client = None

def get_openai_client():
    """Get OpenAI client, creating it if needed"""
    global _client
    if _client is None:
        if settings.OPENAI_API_KEY:
            _client = OpenAI(api_key=settings.OPENAI_API_KEY)
            print("✅ OpenAI client initialized")
        else:
            print("⚠️  OPENAI_API_KEY not configured - OpenAI features will not work")
            # Create a dummy client that will fail on actual use
            _client = OpenAI(api_key="dummy-key")
    return _client

# For backward compatibility, try to create client at import time
# but don't fail if API key is missing
try:
    if settings.OPENAI_API_KEY:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        print("✅ OpenAI client initialized")
    else:
        client = None
        print("⚠️  OPENAI_API_KEY not configured - OpenAI features will not work")
except Exception as e:
    print(f"⚠️  OpenAI client initialization failed: {e}")
    client = None

CREATIVE_DIRECTOR_SYSTEM_PROMPT = """You are an expert creative director specializing in product advertisement videos.

Your role is to ask EXACTLY 5 strategic questions (one at a time) to understand the user's vision for their video ad.

STRICT QUESTION STRATEGY (ask in this exact order):
1. "How do you want this ad to look and feel? (e.g., modern and sleek, energetic and fun, luxurious and sophisticated, minimal and clean)"
2. "Who is your target audience? Who should this ad appeal to?"
3. "What's the key message or emotion you want viewers to feel when they see this ad?"
4. "What should be the pacing and energy? (e.g., fast-paced and exciting, slow and elegant, dynamic with build-up)"
5. "Are there any specific colors or visual elements you want to emphasize in the ad?"

CRITICAL RULES:
- Ask EXACTLY one question at a time
- Ask questions in the exact order listed above
- NEVER skip questions or ask multiple questions at once
- NEVER repeat a question that has already been answered
- After asking the 5th question and receiving the answer, say EXACTLY: "Perfect! I think I've got a great idea for your ad. Click 'Get Started' below to see the concept!"

Do NOT ask more than 5 questions under any circumstances. After the 5th answer, end with the completion message.
"""


def chat_with_creative_director(conversation_history, questions_asked=0):
    """Chat with OpenAI Creative Director"""
    # Add question count to system prompt
    system_prompt = CREATIVE_DIRECTOR_SYSTEM_PROMPT
    
    # Count user responses to determine which question to ask next
    user_message_count = len([m for m in conversation_history if m["role"] == "user"])
    next_question_number = user_message_count + 1
    
    if next_question_number <= 5:
        system_prompt += f"\n\nCRITICAL: You are about to ask question #{next_question_number} of 5. Ask ONLY question #{next_question_number} from the list above. Do not ask multiple questions."
    else:
        system_prompt += f"\n\nCRITICAL: You have already asked all 5 questions. DO NOT ask any more questions. End the conversation with the completion message."
    
    messages = [
        {"role": "system", "content": system_prompt}
    ] + conversation_history
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.5,  # Lower temperature for more consistent behavior
    )
    
    return response.choices[0].message.content


def generate_creative_bible_from_answers(answers, brand_info):
    """Generate Creative Bible from structured answers"""
    prompt = f"""Based on these campaign preferences for the brand "{brand_info['title']}" ({brand_info['description']}):

Style: {answers.get('style', 'Modern & Sleek')}
Target Audience: {answers.get('audience', 'Everyone')}
Key Message/Emotion: {answers.get('emotion', 'Excitement')}
Pacing & Energy: {answers.get('pacing', 'Dynamic Build-up')}
Colors/Visual Style: {answers.get('colors', 'Match Product Colors')}

Create a comprehensive Creative Bible in JSON format with:
- brand_style (string: derived from the style preference)
- vibe (string: derived from emotion and pacing)
- colors (array of 3-4 hex color codes that match the visual style preference)
- lighting (string: describe lighting style)
- camera (string describing camera movement based on pacing)
- motion (string describing motion style)
- energy_level (string: low, medium, or high based on pacing)

Return ONLY valid JSON, no markdown or extra text."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        timeout=30.0  # 30 second timeout
    )

    import json
    content = response.choices[0].message.content.strip()

    # Safely parse JSON response with fallback
    try:
        # Remove markdown code blocks if present
        if content.startswith("```"):
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1]
                if content.startswith("json"):
                    content = content[4:]

        creative_bible = json.loads(content.strip())

        # Validate required fields
        required_fields = ['brand_style', 'vibe', 'colors', 'lighting', 'camera', 'motion', 'energy_level']
        missing_fields = [f for f in required_fields if f not in creative_bible]

        if missing_fields:
            print(f"⚠️  OpenAI response missing fields: {missing_fields}, using defaults")
            # Add default values for missing fields
            defaults = {
                'brand_style': answers.get('style', 'Modern & Professional'),
                'vibe': answers.get('pacing', 'Steady & Engaging'),
                'colors': ['#3b82f6', '#1e40af', '#60a5fa', '#93c5fd'],
                'lighting': 'Bright and professional',
                'camera': 'Smooth, professional movements',
                'motion': 'Clean and purposeful',
                'energy_level': 'Medium'
            }
            for field in missing_fields:
                creative_bible[field] = defaults.get(field, 'Professional')

        # Validate colors is an array with at least 3 items
        if not isinstance(creative_bible.get('colors'), list) or len(creative_bible['colors']) < 3:
            print(f"⚠️  Invalid colors format, using defaults")
            creative_bible['colors'] = ['#3b82f6', '#1e40af', '#60a5fa', '#93c5fd']

        return creative_bible

    except (json.JSONDecodeError, IndexError, KeyError) as e:
        print(f"❌ Failed to parse OpenAI response: {e}")
        print(f"   Raw content: {content[:200]}...")
        # Return fallback creative bible based on user answers
        return {
            'brand_style': answers.get('style', 'Modern & Professional'),
            'vibe': answers.get('pacing', 'Steady & Engaging'),
            'colors': ['#3b82f6', '#1e40af', '#60a5fa', '#93c5fd'],
            'lighting': 'Bright and professional to highlight the product',
            'camera': 'Smooth, professional camera movements',
            'motion': 'Clean and purposeful transitions',
            'energy_level': 'Medium - engaging but professional'
        }


def generate_storyline_and_prompts(creative_bible, brand_info):
    """Generate storyline, Sora prompts, and Suno prompt"""
    prompt = f"""Based on this Creative Bible for the brand "{brand_info['title']}":

{format_creative_bible(creative_bible)}

Generate a complete video ad plan with:

1. A 1-scene storyline (3 seconds total)
2. Sora video prompts for the scene
3. A Suno music prompt

Return as JSON with this structure:
{{
  "storyline": {{
    "total_duration": 3,
    "scenes": [
      {{
        "scene_number": 1,
        "title": "Scene Title",
        "duration": 3,
        "start_time": 0,
        "end_time": 3,
        "description": "Detailed description",
        "energy_start": 3,
        "energy_end": 5,
        "visual_notes": "Notes about visual style"
      }}
    ]
  }},
  "suno_prompt": "Detailed music prompt for 3 seconds..."
}}

Make the Suno prompt VERY specific about timing for the single 3-second scene.
Return ONLY the JSON object."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    
    import json
    return json.loads(response.choices[0].message.content)


def generate_sora_prompts(storyline, creative_bible, reference_images, brand_info):
    """Generate Sora prompts for each scene"""
    sora_prompts = []

    # Safe access to creative_bible with defaults
    brand_style = creative_bible.get('brand_style', 'Modern and professional')
    vibe = creative_bible.get('vibe', 'Engaging and dynamic')
    colors = creative_bible.get('colors', ['#3b82f6', '#1e40af'])
    lighting = creative_bible.get('lighting', 'Professional lighting')
    camera = creative_bible.get('camera', 'Smooth camera movements')
    motion = creative_bible.get('motion', 'Dynamic motion')

    for scene in storyline["scenes"]:
        prompt = f"""SCENE {scene['scene_number']} PROMPT

Creative Direction (locked):
- Style: {brand_style}
- Vibe: {vibe}
- Colors: {', '.join(colors)}
- Lighting: {lighting}
- Camera: {camera}
- Motion: {motion}

Reference Images (style anchors):
{format_reference_images(reference_images)}

Scene {scene['scene_number']}: {scene['title']}
Duration: 6 seconds at 30fps
Description: {scene['description']}
Energy: {scene['energy_start']} → {scene['energy_end']}

Product: {brand_info['title']}

Requirements:
- Use reference images as visual style guide
- Maintain EXACT product appearance from user-uploaded images
- Use ONLY the locked colors above
- Keep {motion} motion style
- Match energy progression: {scene['energy_start']} to {scene['energy_end']}
- Professional, cinematic quality
- Follow visual notes: {scene['visual_notes']}

Generate video matching all constraints above."""
        
        sora_prompts.append({
            "scene_number": scene['scene_number'],
            "prompt": prompt
        })
    
    return sora_prompts


def generate_reference_image_prompts(creative_bible, brand_info):
    """Generate prompts for Replicate image generation"""
    prompt = f"""Based on this Creative Bible for "{brand_info['title']}":

{format_creative_bible(creative_bible)}

Generate 3 image generation prompts for:
1. Hero shot (product centered, premium)
2. Detail shot (close-up, texture focus)
3. Lifestyle shot (product in context)

Return as JSON array with this structure:
[
  {{
    "type": "hero",
    "prompt": "Professional product photography. [Product]..."
  }},
  {{
    "type": "detail",
    "prompt": "Close-up detail photography..."
  }},
  {{
    "type": "lifestyle",
    "prompt": "Lifestyle product photography..."
  }}
]

Make prompts detailed and include style, colors, lighting from Creative Bible.
Return ONLY the JSON array."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    
    import json
    return json.loads(response.choices[0].message.content)


def format_conversation(conversation_history):
    """Format conversation for prompt"""
    formatted = []
    for msg in conversation_history:
        role = "User" if msg["role"] == "user" else "AI"
        formatted.append(f"{role}: {msg['content']}")
    return "\n".join(formatted)


def format_creative_bible(creative_bible):
    """Format Creative Bible for prompt"""
    import json
    return json.dumps(creative_bible, indent=2)


def format_reference_images(reference_images):
    """Format reference images list"""
    formatted = []
    for key, url in reference_images.items():
        formatted.append(f"- {key.replace('_', ' ').title()}: {url}")
    return "\n".join(formatted)

