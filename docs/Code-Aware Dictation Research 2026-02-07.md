---
title: Code-Aware Dictation Research for Speech-to-Text Tool
created: 07-02-2026
tags: [research, speech-to-text, whisper, dictation, vibe-coding, technical-vocabulary, post-processing]
---

# Code-Aware Dictation Research for Speech-to-Text Tool

**Research Date:** 07 February 2026

## Coverage Key
<span style="color:#3498db">🌍</span> Global | <span style="color:#2ecc71">🇺🇸</span> United States

## Executive Summary

This research explores approaches for implementing code-aware dictation in STVC (Speech-to-Text for Vibe Coding), focusing on handling technical terminology in natural language instructions rather than code syntax dictation. Key findings:

- **Whisper handles technical jargon reasonably well** but benefits from initial_prompt parameter and fine-tuning for domain-specific vocabulary
- **Contextual biasing** (prefix trees, keyword spotting) can improve accuracy without fine-tuning
- **Post-processing pipelines** using regex, LLMs, or neural text normalization are essential for production quality
- **Existing tools** (Talon, Serenade, Wispr Flow) demonstrate successful approaches to formatting commands and technical term recognition
- **LLM-based cleanup** (Claude, GPT) is increasingly popular for polishing raw transcriptions
- **For vibe coding specifically**: Focus on technical TERM accuracy (API, JSON, TypeScript) rather than syntax elements (brackets, semicolons)

---

## 1. Programming Vocabulary & Technical Terms

### Whisper's Baseline Performance <span style="color:#3498db">🌍</span>

**Accuracy Metrics:**
- **2.7% WER** on LibriSpeech clean English audio
- **5.2% WER** on challenging audio conditions
- **7.88% WER** (Large-v3) and **7.75% WER** (Turbo) on mixed real-world audio
- **Technical jargon limitation**: Heavy background noise, strong accents, or technical jargon often trip up the model

**Key Insight**: Whisper is relatively good at handling background noise, different accents, and technical jargon, but published WER benchmarks often use clean audio. Real-world audio with domain jargon can see 15-20% WER vs 5% on benchmarks.

### Initial Prompt Parameter <span style="color:#3498db">🌍</span>

**Usage:**
The `initial_prompt` (or `prompt_ids`) parameter provides context for transcription, such as custom vocabularies or proper nouns to make it more likely to predict those words correctly.

**Limitations:**
- **224 token limit** (half the context size) restricts vocabulary size
- **Only affects first 30 seconds** of audio - subsequent segments use previous transcription as prompt
- **Degradation risk**: Some users report quality degradation on first chunk with faster-distil-whisper models

**Best Practices:**
- Use for high-priority technical terms and proper nouns
- Focus on terms most critical to your domain (e.g., "React, TypeScript, API, JSON, Claude Code, MCP, WebSocket")
- Consider it a steering mechanism rather than a complete vocabulary solution

### Fine-Tuning Approach <span style="color:#3498db">🌍</span>

**Why Fine-Tune:**
- Whisper can be fine-tuned with a small amount of dataset to make domain-specific terminology recognizable
- Since Whisper predicts UTF8 bytecodes directly, **no vocabulary updates needed** when adding new words
- Significantly improves accuracy on technical jargon, accents, and domain-specific terms

**Requirements:**
- Dataset with both audio and high-quality text transcriptions
- Both training and validation sets required
- Data preparation needed for Hugging Face sequence-to-sequence pipeline compatibility

**Synthesized Speech Approach:**
By creating a dataset with synthesized speech, you can create a Whisper model that recognizes technical terms without recording hundreds of hours of real audio.

### Contextual Biasing (Cutting-Edge) <span style="color:#3498db">🌍</span>

**Recent Research (2024-2026):**

Multiple approaches enhance transcription accuracy **without explicit fine-tuning**:

1. **Prefix Tree Integration**: Neural-symbolic prefix tree structure guides model output toward specific vocabulary
2. **Keyword-Spotting (CB-Whisper)**: Performs open-vocabulary keyword-spotting before the decoder to recognize user-defined entities
3. **Dynamic Prompting**: Prompting Speech Foundation Models (SFMs) with contextual words improves recognition accuracy
4. **Instruction-Tuning**: Data-efficient supervised learning improves Whisper performance through strategic prompting and weighted loss

**Advantages:**
- No extensive labeled datasets required
- No full model fine-tuning needed
- Can be applied dynamically based on context (current file, recent code)

---

## 2. Punctuation Commands

### Standard Voice Commands <span style="color:#2ecc71">🇺🇸</span> <span style="color:#3498db">🌍</span>

**Common Implementations:**
- Say "period," "comma," "question mark" in appropriate places
- Example: "Hello comma how are you question mark" → "Hello, how are you?"

**Platform Support (2026):**

| Platform | Features |
|----------|----------|
| **Windows 11** | Fluid dictation with automatic grammar, spelling, and punctuation correction |
| **Google Cloud** | Automatic punctuation inference (periods, commas, question marks) |
| **Apple Dictation** | Built-in punctuation command support |
| **Dragon NaturallySpeaking** | Comprehensive punctuation vocabulary |

**Best Practice:**
Say punctuation immediately after the word it follows without pausing—maintain natural speaking rhythm and treat punctuation commands as part of sentence flow.

### Nerd Dictation Approach <span style="color:#3498db">🌍</span>

**Post-Processing Features:**
- `--punctuate-from-previous-timeout SECONDS`: Automatically adds comma or full stop when resuming dictation
- `--full-sentence`: Capitalizes first character and adds punctuation
- **User configuration as Python script**: Full Python feature set for text manipulation

**Key Advantage**: Hackable architecture allows custom post-processing logic beyond built-in features.

---

## 3. Variable Name Dictation (Formatting Commands)

### Talon Voice Approach <span style="color:#3498db">🌍</span>

**Formatter Commands:**
- "camel hello world" → `helloWorld`
- "snake hello world" → `hello_world`
- "allcaps snake dark colors" → `DARK_COLORS`

**Philosophy**: Explicit formatting commands with composable formatters (can combine multiple formatters in sequence).

**Phonetic Alphabet:**
Talon uses shortened phonetic alphabet (one syllable per letter) vs NATO alphabet (2-3 syllables), enabling faster dictation with less than half the syllables.

### Serenade Approach <span style="color:#3498db">🌍</span>

**AI-Powered Inference:**
- Machine learning infers formatting from context
- If variable `foo_bar` exists in scope, saying "insert foo bar" automatically formats as `foo_bar`
- Natural way to speak code: "delete import" or "add function factorial" handles syntax automatically

**Philosophy**: Minimize explicit formatting commands by inferring intent from codebase context.

### Standard Naming Conventions <span style="color:#3498db">🌍</span>

| Convention | Pattern | Common Use |
|------------|---------|-----------|
| **Camel Case** | `personOne`, `textUtil` | Variables, functions, methods (JS/TS, Java) |
| **Snake Case** | `person_one`, `text_util` | Variables, functions (Python, Ruby) |
| **Pascal Case** | `PersonOne`, `TextUtil` | Classes, interfaces, namespaces |
| **Kebab Case** | `person-one`, `text-util` | CSS classes, file names, URLs |
| **Screaming Snake** | `PERSON_ONE`, `MAX_SIZE` | Constants |

---

## 4. Post-Processing Pipeline Architecture

### Modern Pipeline Components <span style="color:#3498db">🌍</span>

**Standard Architecture:**
```
Raw Audio → Speech Recognition → Post-Processing → User-Ready Text
                                       ↓
                    ┌──────────────────┴──────────────────┐
                    ↓                                      ↓
        Text Normalization                    Rich Transcription
        - Punctuation restoration             - Emotion detection
        - Capitalization                      - Event detection
        - Number expansion                    - Timestamp alignment
        - Abbreviation handling               - Sentence segmentation
```

### Text Normalization Techniques <span style="color:#3498db">🌍</span>

**Inverse Text Normalization (ITN):**
Converts ASR output into written form to improve readability:
- Expand abbreviations: "Dr." → "doctor"
- Handle numbers: "627" → context determines "six two seven" vs "six twenty-seven"
- Format dates, times, phone numbers
- Acronyms with spaces between letters when spoken letter-by-letter

**Technology Approaches:**

| Approach | Description | Pros/Cons |
|----------|-------------|-----------|
| **WFST-based** | Weighted Finite State Transducers with grammars | Fast, deterministic; hard to scale to new languages |
| **WFST + LM** | WFST with neural language models | Better disambiguation; improved ambiguous examples |
| **Audio-based TN** | Uses audio context to disambiguate | Handles "six two seven" vs "six twenty-seven" correctly |
| **Neural TN/ITN** | End-to-end neural models | Easy to scale with training data; requires data |

**NVIDIA NeMo** offers all four approaches as production-ready solutions.

### Regex-Based Post-Processing <span style="color:#3498db">🌍</span>

**Common Applications:**
- Find and replace with simple text or regex patterns
- Clean filler words, normalize whitespace
- Remove HTML tags from web-scraped text
- Pronunciation correction dictionaries with pattern matching

**Python Implementation:**
```python
import re

# Example: Remove filler words
text = re.sub(r'\b(um|uh|like|you know)\b', '', text, flags=re.IGNORECASE)

# Example: Normalize spacing
text = re.sub(r'\s+', ' ', text).strip()

# Example: Command replacement
text = re.sub(r'\bperiod\b', '.', text)
text = re.sub(r'\bcomma\b', ',', text)
```

**Best Practice**: Test regex in find mode multiple times before applying replacements to avoid unintended changes.

### LLM-Based Post-Processing <span style="color:#2ecc71">🇺🇸</span> <span style="color:#3498db">🌍</span>

**Modern Approach (2024-2026):**
Using Claude, GPT, or other LLMs to clean up raw transcriptions has become increasingly popular.

**Capabilities:**
- Remove filler words automatically
- Correct grammar and spelling
- Adapt tone based on context
- Format transcripts for readability
- Fix punctuation and capitalization

**Implementation Considerations:**
- Use **Instruct-class models** (fine-tuned for tasks) rather than chat models
- Return output in **structured format (JSON)** to prevent unwanted LLM adjustments
- VTTCleaner approach: Transform verbose transcripts into compact format to reduce token count before LLM processing

**Example Workflow:**
```
Raw Whisper Output → LLM Cleanup Prompt → Polished Text
"um so we need to like implement the uh API handler"
↓
"We need to implement the API handler."
```

---

## 5. Context-Aware Transcription

### IDE Integration & File Context <span style="color:#2ecc71">🇺🇸</span> <span style="color:#3498db">🌍</span>

**Modern Tools (2026):**

**Wispr Flow:**
- Recognizes context (drafting email, writing code, managing files)
- Automatically learns technical terminology, company names, product names
- **Personal dictionary**: Learns "async await function", "SQLAlchemy ORM query" automatically
- **95%+ accuracy** with technical terminology through contextual awareness
- **Native IDE integrations**: Cursor, Windsurf, Replit for "vibe coding"
- Reduces editing time by 67% vs traditional dictation

**Cursor + Claude:**
- AI understands entire project, not just current file
- 200K token context window for codebase awareness
- Model Context Protocol (MCP) for IDE-specific features

**GPT-5.2-Codex:**
- Repo-scale reasoning with production CLI/web/IDE workflows
- Long-horizon coding tasks with full project context

### PromptASR Framework <span style="color:#3498db">🌍</span>

**Content Prompts:**
- Semantic and context-related information
- Sentences or lists of rare words from current file/conversation
- Previous audio segment transcripts to preserve context

**Implementation:**
To preserve context across split segments, prompt the model with the transcript of the preceding segment. The model uses relevant information from previous audio to improve accuracy.

### Multi-Pass Contextualization <span style="color:#3498db">🌍</span>

**Second-Pass Refinement:**
Rather than confining second-pass processing to predetermined candidates, modern approaches harness LLM linguistic knowledge to generate contextually coherent transcriptions using zero-shot prompting.

**Benefits:**
- Captures intricate contextual nuances
- Improves rare-word recognition
- Better handling of domain-specific terminology

---

## 6. Vibe Coding Specifics

### Natural Language vs. Code Syntax <span style="color:#2ecc71">🇺🇸</span> <span style="color:#3498db">🌍</span>

**Key Distinction:**

<span style="color:#e67e22;font-weight:bold">Vibe coding dictates INTENT in natural language, NOT code syntax.</span>

**Examples:**

| Vibe Coding (Natural) | Traditional Code Dictation |
|-----------------------|----------------------------|
| "add a function that validates email addresses" | "def validate underscore email open paren email colon string close paren arrow bool colon" |
| "implement error handling for the API call" | "try colon new line tab await fetch open paren API underscore URL close paren" |
| "create a React component for user profile" | "function user profile open paren props colon user props close paren colon JSX dot element open brace" |

**Focus Areas for STVC:**
1. **Technical TERMS** (API, JSON, TypeScript, React, WebSocket) - High priority
2. **Framework names** (Next.js, FastAPI, PostgreSQL) - High priority
3. **Action verbs** (implement, refactor, validate) - Medium priority
4. **NOT syntax elements** (brackets, semicolons, indentation) - Not needed

### Performance Reality Check <span style="color:#2ecc71">🇺🇸</span>

**Current State (2026):**
- Developers use dictation for **planning, commenting, prompting, and drafting** code-related text
- Most developers **don't ship production code entirely by voice**
- Dictation saves time on **everything around the code** (commit messages, documentation, planning)
- For syntax-heavy sections, **typing remains faster**
- Voice dictation enables **4x speed increase**: 150 WPM speaking vs 40 WPM typing

### Dragon NaturallySpeaking Lessons <span style="color:#2ecc71">🇺🇸</span>

**Customization Features:**
- Manual vocabulary addition
- Document/email browsing to learn common words
- Import lists: personnel, products, departments, glossaries, acronyms
- Custom voice commands via Dragonfly framework

**Key Takeaway:**
Even with extensive customization, "it is difficult to do programming with voice" for actual syntax. Focus on natural language instruction.

---

## 7. Existing Solutions Analysis

### Talon Voice <span style="color:#3498db">🌍</span>

**Architecture:**
- Command-based (not continuous dictation) by default
- Scriptable via Python
- Eye tracking integration for cursor positioning
- Phonetic alphabet optimized for speed

**Strengths:**
- Precise control over formatting
- Composable commands
- Highly customizable
- Active community with shared command sets

**Limitations:**
- Steep learning curve
- Requires memorizing many commands
- Not ideal for natural language flow

### Serenade <span style="color:#3498db">🌍</span>

**Architecture:**
- ML-based intent inference
- Context-aware formatting from codebase
- Natural language command interpretation

**Strengths:**
- Lower learning curve
- More natural speaking style
- Automatic syntax handling

**Limitations:**
- Less precise control than Talon
- Requires existing code context for best results

### Wispr Flow <span style="color:#3498db">🌍</span>

**Architecture (2026):**
- Whisper + LLM post-processing
- Personal dictionary with automatic learning
- Context-aware (email, code, file management)
- Native IDE integrations

**Strengths:**
- 95%+ accuracy with technical terms
- 179 WPM dictation speed
- Automatic filler word removal
- 67% reduction in editing time
- Perfect for vibe coding workflow

**Limitations:**
- Commercial product (not open-source)
- May have subscription costs

### Nerd Dictation <span style="color:#3498db">🌍</span>

**Architecture:**
- VOSK-API based (offline)
- Python script configuration
- Hackable post-processing

**Strengths:**
- Completely open-source
- Offline operation
- Full customization via Python
- Simple, focused tool

**Limitations:**
- Basic features by default
- Requires coding to extend
- VOSK models less accurate than Whisper

---

## 8. Practical Recommendations for STVC

### Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STVC Pipeline                             │
└─────────────────────────────────────────────────────────────┘

1. Audio Input (microphone)
         ↓
2. faster-whisper Transcription
   - Initial prompt with top 50 technical terms
   - Large-v3 or Turbo model
         ↓
3. Regex Post-Processing
   - Punctuation commands → symbols
   - Filler word removal
   - Number/abbreviation normalization
         ↓
4. Formatting Commands (Optional)
   - "camel case X" → camelCase
   - "snake case X" → snake_case
         ↓
5. LLM Polish (Optional/On-Demand)
   - Claude/GPT cleanup for critical text
   - Grammar and tone adjustment
         ↓
6. Output to Claude Code interface
```

### Priority 1: Technical Term Handling

**Approach 1 - Initial Prompt (Quick Win):**
```python
TECH_TERMS = """
React, TypeScript, JavaScript, Python, API, JSON, REST, GraphQL,
WebSocket, PostgreSQL, MongoDB, Redis, Docker, Kubernetes,
Next.js, FastAPI, Express, Node.js, npm, pip, git, GitHub,
Claude Code, MCP, Anthropic, OpenAI, async, await, fetch
"""

segments, info = model.transcribe(
    audio,
    initial_prompt=TECH_TERMS,
    language="en"
)
```

**Approach 2 - Fine-Tuning (Best Accuracy):**
1. Collect 50-100 example transcriptions with technical terms
2. Use text-to-speech to generate synthetic audio dataset
3. Fine-tune Whisper model on Hugging Face
4. Deploy fine-tuned model with faster-whisper

**Approach 3 - Contextual Biasing (Advanced):**
1. Implement prefix tree with technical vocabulary
2. Extract terms from current Claude Code conversation context
3. Bias recognition toward recently used technical terms

### Priority 2: Punctuation Post-Processing

**Simple Regex Replacement:**
```python
import re

def process_punctuation_commands(text):
    """Replace spoken punctuation with symbols."""
    replacements = {
        r'\bperiod\b': '.',
        r'\bcomma\b': ',',
        r'\bquestion mark\b': '?',
        r'\bexclamation point\b': '!',
        r'\bopen paren\b': ' (',
        r'\bclose paren\b': ')',
        r'\bopen bracket\b': ' [',
        r'\bclose bracket\b': ']',
        r'\bopen brace\b': ' {',
        r'\bclose brace\b': '}',
        r'\bcolon\b': ':',
        r'\bsemicolon\b': ';',
        r'\bdash\b': ' -',
        r'\bnew line\b': '\n',
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text
```

**User Configuration:**
Allow users to add custom replacement rules in config file:
```json
{
  "custom_replacements": {
    "lambda function": "λ",
    "right arrow": "→",
    "less than or equal": "≤"
  }
}
```

### Priority 3: Formatting Commands (Optional)

**Talon-Style Formatters:**
```python
def apply_formatting(text, formatter):
    """Apply formatting to text."""
    words = text.split()

    if formatter == "camel":
        return words[0].lower() + ''.join(w.capitalize() for w in words[1:])
    elif formatter == "snake":
        return '_'.join(w.lower() for w in words)
    elif formatter == "pascal":
        return ''.join(w.capitalize() for w in words)
    elif formatter == "kebab":
        return '-'.join(w.lower() for w in words)
    elif formatter == "screaming":
        return '_'.join(w.upper() for w in words)
    else:
        return text

# Example usage:
# Input: "camel case my variable name"
# Parse: formatter="camel", text="my variable name"
# Output: "myVariableName"
```

**Detection Pattern:**
```python
import re

def detect_formatting_command(text):
    """Detect and apply formatting commands."""
    pattern = r'^(camel|snake|pascal|kebab|screaming)(?:\s+case)?\s+(.+)$'
    match = re.match(pattern, text.strip(), re.IGNORECASE)

    if match:
        formatter = match.group(1).lower()
        content = match.group(2)
        return apply_formatting(content, formatter)

    return text
```

### Priority 4: LLM Polish (On-Demand)

**Use Cases:**
- Critical communications (PRs, documentation, announcements)
- User explicitly requests "polish that"
- Detected low confidence transcription (WER > 15%)

**Implementation:**
```python
async def llm_polish(text, context="general"):
    """Polish transcription using Claude."""
    prompt = f"""Clean up this voice transcription:

Original: {text}

Tasks:
- Remove filler words (um, uh, like)
- Fix grammar and punctuation
- Preserve technical terms exactly
- Maintain original meaning
- Context: {context}

Return only the cleaned text, no explanations."""

    response = await anthropic.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )

    return response.content[0].text
```

**Cost Consideration:**
Only use LLM polish when user explicitly requests or for critical text (not every transcription).

### Priority 5: Context Integration

**Current Conversation Context:**
```python
def get_conversation_context(recent_messages, max_terms=30):
    """Extract technical terms from recent Claude Code conversation."""
    # Extract code blocks
    code_blocks = extract_code_blocks(recent_messages)

    # Extract common identifiers, function names, variable names
    terms = set()
    for code in code_blocks:
        terms.update(extract_identifiers(code))

    # Return top N most frequent terms
    return list(terms)[:max_terms]

# Use in initial_prompt
context_terms = get_conversation_context(recent_messages)
full_prompt = BASE_TECH_TERMS + ", " + ", ".join(context_terms)
```

**File Context:**
```python
def get_file_context(current_file_path):
    """Extract relevant terms from currently open file."""
    with open(current_file_path) as f:
        content = f.read()

    # Extract imports, class names, function names
    terms = extract_code_entities(content)
    return terms
```

---

## 9. Testing & Evaluation

### Metrics to Track

| Metric | Target | Measurement |
|--------|--------|-------------|
| **WER (Word Error Rate)** | < 10% | Levenshtein distance / total words |
| **Technical Term Accuracy** | > 90% | Correct technical terms / total technical terms |
| **Punctuation Accuracy** | > 85% | Correct punctuation / total punctuation |
| **User Edit Rate** | < 20% | Characters edited / total characters |
| **Latency** | < 2s | Time from speech end to text output |

### Test Dataset Creation

**Approach:**
1. Record 50-100 natural language instructions for coding tasks
2. Include mix of:
   - Simple requests ("add error handling")
   - Technical jargon heavy ("implement GraphQL mutation resolver")
   - Multi-sentence instructions
   - Various accents (if possible)
3. Manually transcribe ground truth
4. Benchmark baseline Whisper vs. post-processing pipeline

**Test Categories:**
- Technical vocabulary accuracy
- Punctuation command recognition
- Formatting command accuracy
- Context-aware improvements
- Multi-speaker handling (if applicable)

---

## 10. Implementation Phases

### Phase 1: MVP (2-3 weeks)
- [ ] faster-whisper integration with initial_prompt
- [ ] Basic regex post-processing (punctuation commands)
- [ ] Simple UI for recording and transcription
- [ ] Output to clipboard or text file
- [ ] 50 top technical terms in prompt

### Phase 2: Enhanced Accuracy (2-3 weeks)
- [ ] User-configurable technical term dictionary
- [ ] Context extraction from Claude Code conversation
- [ ] Improved post-processing (filler words, normalization)
- [ ] Confidence scoring for transcriptions
- [ ] Basic metrics tracking

### Phase 3: Advanced Features (3-4 weeks)
- [ ] Formatting commands (camel, snake, pascal, etc.)
- [ ] LLM polish integration (on-demand)
- [ ] File context awareness
- [ ] Fine-tuned Whisper model for programming domain
- [ ] User feedback and correction mechanism

### Phase 4: Production Polish (2-3 weeks)
- [ ] Performance optimization
- [ ] Error handling and recovery
- [ ] User preferences and settings
- [ ] Documentation and tutorials
- [ ] Integration testing with Claude Code

---

## Key Technologies Summary

### Recommended Stack

| Component | Technology | Reason |
|-----------|-----------|--------|
| **Speech Recognition** | faster-whisper (Large-v3 or Turbo) | 4x faster than OpenAI Whisper, same accuracy, less memory |
| **Post-Processing** | Python regex + optional LLM | Flexible, customizable, proven approach |
| **Context Biasing** | Initial prompt → Fine-tuning (later) | Quick wins first, better accuracy later |
| **LLM Polish** | Claude 3.5 Sonnet (on-demand) | Best balance of quality and cost |
| **Text Normalization** | Custom Python + NVIDIA NeMo (optional) | Start simple, scale to neural approaches |

---

## Sources

### Whisper & Technical Vocabulary
- [OpenAI Whisper - GeeksforGeeks](https://www.geeksforgeeks.org/artificial-intelligence/openai-whisper/)
- [openai/whisper-large-v3 · Hugging Face](https://huggingface.co/openai/whisper-large-v3)
- [Prompt Engineering in Whisper - Medium](https://medium.com/axinc-ai/prompt-engineering-in-whisper-6bb18003562d)
- [Fine-Tune Whisper For Multilingual ASR - Hugging Face](https://huggingface.co/blog/fine-tune-whisper)
- [Whisper Fine Tuning To Transcribe Jargon - Medium](https://medium.com/axinc-ai/whisper-fine-tuning-to-transcribe-jargon-976164a5eac8)

### faster-whisper
- [Choosing between Whisper variants - Modal](https://modal.com/blog/choosing-whisper-variants)
- [GitHub - SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [What is Faster Whisper? - Deepchecks](https://www.deepchecks.com/llm-tools/faster-whisper/)

### Contextual Biasing
- [Contextual Biasing to Improve Domain-specific Custom Vocabulary - arXiv](https://arxiv.org/html/2410.18363v1)
- [GitHub - BriansIDP/WhisperBiasing](https://github.com/BriansIDP/WhisperBiasing)
- [CB-Whisper: Contextual Biasing Whisper - ACL Anthology](https://aclanthology.org/2024.lrec-main.262/)

### Punctuation Commands
- [Dictate text with voice - Microsoft Support](https://support.microsoft.com/en-us/topic/dictate-text-with-voice-4ddaf335-a835-4e63-9a30-e24b9f361deb)
- [How to Use Punctuation Commands in Voice Dictation - Vomo AI](https://vomo.ai/blog/how-to-use-punctuation-commands-in-voice-dictation)
- [Enable automatic punctuation - Google Cloud](https://cloud.google.com/speech-to-text/docs/automatic-punctuation)

### Talon Voice
- [Coding with voice dictation using Talon Voice - Josh W. Comeau](https://www.joshwcomeau.com/blog/hands-free-coding/)
- [Speaking in code: hands-free input with Talon - Blake Watson](https://blakewatson.com/journal/speaking-in-code-hands-free-input-with-talon/)
- [Talon: In-Depth Review - Hands-Free Coding](https://handsfreecoding.org/2021/12/12/talon-in-depth-review/)
- [GitHub - talonhub/community](https://github.com/talonhub/community)

### Nerd Dictation
- [GitHub - ideasman42/nerd-dictation](https://github.com/ideasman42/nerd-dictation)
- [Punctuation and capitalization commands for nerd-dictation - GitHub Gist](https://gist.github.com/xenotropic/d1ccab53e0bba34f280c93955958afbd)

### Voice Coding & Natural Language
- [What is vibe coding - Youware](https://www.youware.com/blog/what-is-vibe-coding)
- [AI Dictation for Developers & Coders - Speechify](https://speechify.com/blog/ai-dictation-for-developers-coders-voice-coding-2026/)
- [Serenade | Code with voice](https://serenade.ai/)
- [Programming by Voice May Be the Next Frontier - IEEE Spectrum](https://spectrum.ieee.org/programming-by-voice-may-be-the-next-frontier-in-software-development)

### Post-Processing & Text Normalization
- [Text Normalization and Inverse Text Normalization - NVIDIA](https://developer.nvidia.com/blog/text-normalization-and-inverse-text-normalization-with-nvidia-nemo/)
- [Pipeline speech recognition - FasterCapital](https://fastercapital.com/content/Pipeline-speech-recognition--How-to-process-and-understand-speech-and-audio-data-using-your-pipeline.html)
- [Display text formatting with speech to text - Microsoft](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/display-text-format)

### LLM Post-Processing
- [Using LLM to get cleaner voice transcriptions - Shing's Blog](https://shinglyu.com/ai/2024/01/17/using-llm-to-get-cleaner-voice-transcriptions.html)
- [GitHub - itsmevictor/clean-transcribe](https://github.com/itsmevictor/clean-transcribe)

### Context-Aware Transcription
- [PromptASR for contextualized ASR - arXiv](https://arxiv.org/html/2309.07414v3)
- [Wispr Flow 2026 Review - Max Productive AI](https://max-productive.ai/ai-tools/wispr-flow/)
- [Wispr Flow Review - Willow Voice](https://willowvoice.com/blog/wispr-flow-review-voice-dictation)
- [Top 6 speech to text AI solutions in 2026 - Fingoweb](https://www.fingoweb.com/blog/top-6-speech-to-text-ai-solutions-in-2026/)

### Benchmarks & Accuracy
- [Best Speech-to-Text APIs in 2026 - Deepgram](https://deepgram.com/learn/best-speech-to-text-apis-2026)
- [WhisperX vs Competitors - Brass Transcripts](https://brasstranscripts.com/blog/whisperx-vs-competitors-accuracy-benchmark)
- [Best open source speech-to-text model in 2026 - Northflank](https://northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2026-benchmarks)
- [Speech-to-Text Benchmark: Deepgram vs. Whisper in 2026](https://research.aimultiple.com/speech-to-text/)

### Naming Conventions
- [Snake Case or Camel Case? - Boot.dev](https://blog.boot.dev/clean-code/casings-in-coding/)
- [Camel Case vs. Snake Case vs. Pascal Case - Khalil Stemmler](https://khalilstemmler.com/blogs/camel-case-snake-case-pascal-case/)
- [Programming Naming Conventions Explained - FreeCodeCamp](https://www.freecodecamp.org/news/programming-naming-conventions-explained/)

### IDE Integration
- [Claude Code Complete Guide 2026 - Jitendra Zaa](https://www.jitendrazaa.com/blog/ai/claude-code-complete-guide-2026-from-basics-to-advanced-mcp-2/)
- [Enhancing LLM-Based Coding Tools - arXiv](https://arxiv.org/html/2402.03630v2)

### Python Libraries
- [GitHub - KoljaB/RealtimeSTT](https://github.com/KoljaB/RealtimeSTT)
- [SpeechRecognition · PyPI](https://pypi.org/project/SpeechRecognition/)
- [Python Speech Recognition in 2025 - AssemblyAI](https://www.assemblyai.com/blog/the-state-of-python-speech-recognition)

### Dragon NaturallySpeaking
- [GitHub - dictation-toolbox/dragonfly](https://github.com/dictation-toolbox/dragonfly)
- [Dragon Speech Recognition - Nuance](https://www.nuance.com/dragon.html)

### Regex & Text Processing
- [Regex.Replace Method - Microsoft Learn](https://learn.microsoft.com/en-us/dotnet/api/system.text.regularexpressions.regex.replace?view=net-7.0)
- [Text Preprocessing in Python Using Regex - GeeksforGeeks](https://www.geeksforgeeks.org/python/text-preprocessing-in-python-using-regex/)
