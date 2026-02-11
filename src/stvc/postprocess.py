import re


def fix_missing_question_marks(text: str) -> str:
    """Add question marks to interrogative sentences Whisper missed."""
    interrogative = r'((?:^|[.\!?]\s+)(?:who|what|where|when|why|how|can|could|would|should|is|are|do|does|did|will|shall|have|has|had)\b[^.\!?]*)\.'
    return re.sub(interrogative, r'\1?', text, flags=re.IGNORECASE)


def remove_filler_words(text: str) -> str:
    """Remove common filler words (um, uh, like, you know)."""
    text = re.sub(r'\b(um|uh|like|you know)\b', '', text, flags=re.IGNORECASE)
    return re.sub(r'  +', ' ', text).strip()


def process(text: str, fix_questions: bool = True, remove_fillers: bool = True) -> str:
    """Run all post-processing stages on transcribed text."""
    if fix_questions:
        text = fix_missing_question_marks(text)
    if remove_fillers:
        text = remove_filler_words(text)
    return text.strip()
