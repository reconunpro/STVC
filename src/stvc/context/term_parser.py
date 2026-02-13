"""Term extraction from source code and technical content."""

import re
from collections import Counter
from typing import List

# Common English stop words to filter out
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
    'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall',
    'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
    'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
    'not', 'no', 'yes', 'if', 'then', 'else', 'than', 'so', 'up', 'out',
}


def extract_terms(text: str, max_terms: int = 50) -> List[str]:
    """
    Extract technical terms from text using regex patterns.

    Identifies:
    - camelCase identifiers (e.g., getUserName)
    - snake_case identifiers (e.g., get_user_name)
    - PascalCase class names (e.g., UserService)
    - UPPER_CASE constants (e.g., MAX_RETRIES)
    - Dotted module paths (e.g., stvc.config)
    - Framework/library names (capitalized patterns)

    Args:
        text: Source text to extract terms from
        max_terms: Maximum number of terms to return (default 50)

    Returns:
        List of terms ordered by frequency (most common first)
    """
    if not text:
        return []

    all_terms = []

    # Pattern 1: camelCase identifiers (e.g., getUserName, myVariable)
    # Must start with lowercase, have at least one uppercase letter
    camel_pattern = r'\b[a-z]+[A-Z][a-zA-Z0-9]*\b'
    all_terms.extend(re.findall(camel_pattern, text))

    # Pattern 2: PascalCase identifiers (e.g., UserService, MyClass)
    # Must start with uppercase, have at least one more uppercase letter
    pascal_pattern = r'\b[A-Z][a-z]+[A-Z][a-zA-Z0-9]*\b'
    all_terms.extend(re.findall(pascal_pattern, text))

    # Pattern 3: snake_case identifiers (e.g., get_user_name, my_var)
    # Lowercase with underscores, at least 2 parts
    snake_pattern = r'\b[a-z]+_[a-z0-9_]+\b'
    all_terms.extend(re.findall(snake_pattern, text))

    # Pattern 4: UPPER_CASE constants (e.g., MAX_RETRIES, API_KEY)
    # All uppercase with underscores, at least 2 parts
    upper_pattern = r'\b[A-Z]+_[A-Z0-9_]+\b'
    all_terms.extend(re.findall(upper_pattern, text))

    # Pattern 5: Dotted paths (e.g., stvc.config, os.path.join)
    # At least 2 parts separated by dots
    dotted_pattern = r'\b[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_.]*\b'
    all_terms.extend(re.findall(dotted_pattern, text))

    # Pattern 6: Single capitalized words (potential framework/library names)
    # Single word starting with uppercase, at least 3 chars
    capital_pattern = r'\b[A-Z][a-z]{2,}\b'
    all_terms.extend(re.findall(capital_pattern, text))

    # Filter out stop words and invalid terms
    filtered_terms = []
    for term in all_terms:
        # Convert to lowercase for stop-word check
        term_lower = term.lower()

        # Skip if:
        # - It's a stop word
        # - Single character
        # - Pure numbers
        # - Too short (less than 2 chars)
        if (term_lower in STOP_WORDS or
            len(term) < 2 or
            term.isdigit()):
            continue

        filtered_terms.append(term)

    # Count frequency and rank by most common
    term_counts = Counter(filtered_terms)

    # Get unique terms ordered by frequency (case-insensitive deduplication)
    seen_lower = set()
    ranked_terms = []

    for term, count in term_counts.most_common():
        term_lower = term.lower()
        if term_lower not in seen_lower:
            seen_lower.add(term_lower)
            ranked_terms.append(term)

            if len(ranked_terms) >= max_terms:
                break

    return ranked_terms
