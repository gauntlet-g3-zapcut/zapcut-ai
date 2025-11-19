"""Input sanitization utilities to prevent prompt injection attacks."""
import re
import logging

logger = logging.getLogger(__name__)

# Common prompt injection patterns to detect and neutralize
DANGEROUS_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+(instructions?|prompts?|context)",
    r"disregard\s+(all\s+)?(previous|prior)\s+(instructions?|prompts?|context)",
    r"forget\s+(all\s+)?(previous|prior)\s+(instructions?|prompts?|context)",
    r"system\s*:",
    r"assistant\s*:",
    r"user\s*:",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"###\s*instruction",
    r"###\s*response",
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS]


def sanitize_user_input(text: str, max_length: int = 2000, field_name: str = "input") -> str:
    """
    Sanitize user input to prevent prompt injection attacks.

    Args:
        text: The user-provided text to sanitize
        max_length: Maximum allowed length for the text
        field_name: Name of the field being sanitized (for logging)

    Returns:
        Sanitized text safe for use in prompts

    Raises:
        ValueError: If text contains dangerous patterns that can't be safely sanitized
    """
    if not text or not isinstance(text, str):
        return ""

    original_text = text

    # Step 1: Normalize whitespace
    text = " ".join(text.split())

    # Step 2: Limit length
    if len(text) > max_length:
        logger.warning(f"Input too long for {field_name}: {len(text)} chars, truncating to {max_length}")
        text = text[:max_length]

    # Step 3: Check for dangerous patterns
    for pattern in COMPILED_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            logger.warning(f"Detected potential prompt injection in {field_name}: {matches}")
            # Replace dangerous patterns with sanitized version
            text = pattern.sub("[content removed for security]", text)

    # Step 4: Remove excessive special characters that might be used for injection
    # Allow normal punctuation but limit consecutive special chars
    text = re.sub(r'([^\w\s,.\-!?\'"])\1{2,}', r'\1\1', text)

    # Step 5: Check if too much was removed (indicates potential attack)
    if len(text) < len(original_text) * 0.3 and len(original_text) > 50:
        logger.error(f"Excessive content removal from {field_name} - possible injection attempt")
        # Log the original for security review
        logger.error(f"Original suspicious input: {original_text[:200]}")

    return text.strip()


def validate_user_input(text: str, field_name: str, min_length: int = 0, max_length: int = 2000) -> None:
    """
    Validate user input meets requirements.

    Args:
        text: The text to validate
        field_name: Name of the field for error messages
        min_length: Minimum required length
        max_length: Maximum allowed length

    Raises:
        ValueError: If validation fails
    """
    if not isinstance(text, str):
        raise ValueError(f"{field_name} must be a string")

    if len(text) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters")

    if len(text) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters")

    # Check for null bytes
    if "\x00" in text:
        raise ValueError(f"{field_name} contains invalid characters")


def sanitize_scene_description(description: str) -> str:
    """
    Sanitize scene description for storyline updates.

    Args:
        description: Scene description text

    Returns:
        Sanitized description
    """
    return sanitize_user_input(description, max_length=2000, field_name="scene_description")


def sanitize_ideas(ideas: str) -> str:
    """
    Sanitize user ideas/concepts for campaign creation.

    Args:
        ideas: User-provided ideas text

    Returns:
        Sanitized ideas text
    """
    return sanitize_user_input(ideas, max_length=2000, field_name="campaign_ideas")
