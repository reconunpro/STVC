"""Prompt merging logic for context-aware transcription."""

import logging
from math import ceil

log = logging.getLogger(__name__)


def build_prompt(base_terms: str, context_terms: list[str], max_tokens: int = 224) -> str:
    """Merge base dictionary terms with context-extracted terms within token budget.

    Base terms are always included first. Context terms are appended in order
    until the estimated token count reaches max_tokens. Terms already present
    in base_terms are deduplicated.

    Token estimation: ceil(len(term) / 4) per term, plus 1 token per separator.
    This is a rough approximation of Whisper's tokenizer (GPT-2 based).

    Args:
        base_terms: Comma-separated base dictionary terms (always included)
        context_terms: List of context-extracted terms to append
        max_tokens: Maximum token budget (default 224, Whisper's prompt limit)

    Returns:
        Comma-separated string ready for Whisper's initial_prompt parameter
    """
    if not base_terms:
        base_terms = ""

    # Parse base terms into a set for deduplication (case-insensitive)
    base_set = set()
    if base_terms:
        base_set = {term.strip().lower() for term in base_terms.split(",")}

    # Estimate tokens for base terms
    # Each term: ceil(len/4), plus 1 for comma separator
    base_token_count = 0
    if base_terms:
        for term in base_terms.split(","):
            term = term.strip()
            if term:
                base_token_count += ceil(len(term) / 4) + 1  # +1 for separator

    log.debug(f"Base terms token estimate: {base_token_count}")

    # If base terms already exceed budget, return them truncated
    if base_token_count >= max_tokens:
        log.warning(f"Base terms ({base_token_count} tokens) exceed budget ({max_tokens})")
        return base_terms

    # Add context terms until budget is reached
    merged_parts = [base_terms] if base_terms else []
    current_tokens = base_token_count

    added_count = 0
    for term in context_terms:
        term = term.strip()
        if not term:
            continue

        # Skip if already in base terms (case-insensitive)
        if term.lower() in base_set:
            log.debug(f"Skipping duplicate term: '{term}'")
            continue

        # Estimate tokens for this term
        term_tokens = ceil(len(term) / 4) + 1  # +1 for separator

        # Check if adding this term would exceed budget
        if current_tokens + term_tokens > max_tokens:
            log.debug(f"Token budget reached ({current_tokens}/{max_tokens}), stopping")
            break

        # Add term
        merged_parts.append(term)
        current_tokens += term_tokens
        added_count += 1
        base_set.add(term.lower())  # Track for future dedup

    log.info(
        f"Built prompt: {current_tokens} estimated tokens "
        f"(base + {added_count} context terms)"
    )

    return ", ".join(merged_parts)
