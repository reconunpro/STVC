---
title: STVC Implementation Plan
created: 07-02-2026
tags: [implementation, tooling, stt, whisper, windows, vad, voice-coding]
status: active
priority: high
---

# STVC Implementation Plan

**Created:** 07 February 2026
**Updated:** 07 February 2026 (complete rewrite based on research findings)

## 1. Overview

**STVC (Speech-to-Text for Vibe Coding)** is a system-wide, locally-processed speech-to-text tool for Windows that converts spoken natural language into text and injects it into any application — Claude Code (Windows Terminal), Obsidian, Google Docs, VS Code, or any text field.

### Why We're Building This

Existing tools have critical gaps for AI-assisted coding workflows:

| Gap | Detail |
|-----|--------|
| **claude-stt uses Moonshine** | 27-62M param models lack vocabulary depth for long-form dictation vs 809M+ Whisper models |
| **No VAD in current tools** | Push-to-talk only; no hands-free operation |
| **Injection breaks on snapped windows** | Current claude-stt injection unreliable with window management |
| **No custom vocabulary** | Technical terms (API, TypeScript, MCP) frequently misrecognized |
| **No post-processing pipeline** | Raw transcription output without cleanup |

### Target Use Cases

- **Claude Code** — Dictate natural language instructions into the terminal
- **Obsidian** — Write notes, documentation, and knowledge base entries
- **Google Docs / Web apps** — Draft prose and technical writing
- **Any application** — System-wide text injection via clipboard

### What STVC Is NOT

STVC dictates **intent in natural language**, not code syntax. Users say "add a function that validates email addresses" — not "def validate underscore email open paren."

> See: [Code-Aware Dictation Research](Code-Aware%20Dictation%20Research%202026-02-07.md) §6 for vibe coding specifics.

---

## 2. Hardware & Environment

| Component | Specification |
|-----------|---------------|
| **GPU** | NVIDIA RTX 4070 (12 GB VRAM) |
| **OS** | Windows 11 |
| **Runtime** | Python 3.10+ |
| **VRAM Budget** | ~1.6 GB (model) + ~50 MB (VAD) = **~1.65 GB** |
| **Remaining VRAM** | ~10.35 GB free for other workloads |

The RTX 4070's 12 GB VRAM and Tensor Cores easily accommodate the large-v3-turbo model with FP16 inference, leaving substantial headroom.

---

## 3. Architecture

### Pipeline

```
┌─────────────────────────────────────────────────┐
│  MICROPHONE (Continuous 16kHz Audio Stream)      │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  SILERO VAD (Real-time Speech Detection)         │
│  - Threshold: 0.5                                │
│  - Min silence: 1.0s (user finished speaking)    │
│  - Speech pad: 300ms pre/post                    │
│  - Processes 30ms chunks in <1ms on CPU          │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  AUDIO BUFFER                                    │
│  - Captures speech segments with padding         │
│  - Clears after transcription                    │
└────────────────────┬────────────────────────────┘
                     │
                     ▼ (silence detected → user stopped speaking)
┌─────────────────────────────────────────────────┐
│  FASTER-WHISPER (Batch Transcription on GPU)     │
│  - Model: large-v3-turbo (809M params, 1.6GB)   │
│  - Device: CUDA, Compute: float16                │
│  - initial_prompt: custom dictionary terms       │
│  - Latency: ~0.3-0.5s for 10s audio             │
│  - Accuracy: ~7-8% WER                          │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  POST-PROCESSING                                 │
│  - Punctuation commands → symbols                │
│  - Filler word removal (um, uh, like)            │
│  - Custom regex replacements                     │
│  - Formatting commands (optional)                │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  TEXT INJECTION                                   │
│  - Primary: Clipboard + Ctrl+V (9/10 reliable)   │
│  - Fallback: SendInput Unicode (<30 chars)       │
│  - Target: whatever window has focus             │
└─────────────────────────────────────────────────┘
```

### Design Principles

1. **VAD-first** — Silero VAD detects speech boundaries; only speech segments hit the GPU. Eliminates wasted cycles on silence.
2. **Batch processing** — Full utterance context produces highest accuracy. Streaming is explicitly rejected (lower accuracy, Whisper not designed for it).
3. **Warm model** — Keep faster-whisper loaded in GPU memory. Cold start ~2-3s; warm inference <500ms.
4. **Clipboard injection** — Battle-tested approach used by AutoHotkey, Dragon NaturallySpeaking. Works universally across Electron, terminals, and native apps.

---

## 4. Core Components

### 4.1 STT Engine: faster-whisper with large-v3-turbo

**Decision:** Use faster-whisper (CTranslate2-based) with the large-v3-turbo model.

| Attribute | Value |
|-----------|-------|
| **Engine** | faster-whisper (CTranslate2) |
| **Model** | large-v3-turbo |
| **Parameters** | 809M |
| **VRAM** | ~1.6 GB |
| **Device** | CUDA (RTX 4070) |
| **Compute type** | float16 |
| **Latency** | ~0.3-0.5s for 10s audio |
| **WER** | ~7-8% (LibriSpeech) |
| **License** | MIT |

**Why large-v3-turbo over other models:**
- 4x faster than vanilla OpenAI Whisper at identical accuracy
- ~7-8% WER is more than sufficient for natural language dictation
- Native CUDA with FP16/INT8 quantization leverages RTX 4070 Tensor Cores
- `pip install faster-whisper` just works on Windows — no WSL2 required
- 14k+ GitHub stars, actively maintained by SYSTRAN

**Why not Moonshine (current claude-stt default):**
Moonshine (27-62M params) is optimized for edge devices. On a desktop with an RTX 4070, its ONNX-based GPU path is less optimized than CTranslate2's CUDA path, and its smaller models have narrower vocabulary depth for long-form dictation.

**Why not NVIDIA Parakeet (6.05% WER):**
NeMo does not natively support Windows (requires WSL2). The `onnx-asr` package is an option to monitor for future upgrade.

> Research basis: [STT Engine Comparison](research/STT-Engine-Comparison-2026-02-07.md)

### 4.2 VAD: Silero VAD

**Decision:** Use Silero VAD for automatic speech detection (hands-free operation).

| Attribute | Value |
|-----------|-------|
| **Model** | Silero VAD |
| **Accuracy** | 87.7% TPR @ 5% FPR |
| **vs. WebRTC** | 4x fewer errors (WebRTC: 50% TPR) |
| **Latency** | <1ms per 30ms audio chunk |
| **Languages** | 6000+ |
| **License** | MIT |

**Recommended configuration for voice coding:**

```python
vad_config = {
    'threshold': 0.5,            # Medium sensitivity (0.3-0.4 for quiet rooms, 0.6-0.7 for noisy)
    'min_speech_duration': 0.3,  # Ignore clicks/sounds < 300ms
    'min_silence_duration': 1.0, # 1s pause = user finished speaking
    'speech_pad_ms': 300,        # 300ms padding before/after speech
}
```

**Why VAD instead of push-to-talk only:**
- Hands-free operation — speak whenever ready, no hotkey interruption
- Natural workflow — matches how people talk to AI assistants
- Home office friendly — Silero handles background noise well
- 0.5-1.5s total latency (silence detection + transcription) is acceptable since user waits for Claude anyway

> Research basis: [STT Approach Analysis](research/STT-Approach-Analysis-2026-02-07.md) §VAD Deep Dive

### 4.3 Text Injection: Clipboard + Ctrl+V

**Decision:** Clipboard paste as primary injection, SendInput Unicode as fallback.

| Method | Reliability | Speed | When to Use |
|--------|-------------|-------|-------------|
| **Clipboard + Ctrl+V** | 9/10 | Instant (any length) | Default for all injections ≥5 chars |
| **SendInput Unicode** | 7/10 | ~1ms/char | Fallback when clipboard unavailable, or <5 chars |

**Why Clipboard + Ctrl+V:**
- **Universal compatibility** — every text-accepting app supports paste (Electron, terminals, native)
- **Instant** — 100KB pastes as fast as 5 characters
- **No autocomplete triggers** — text appears atomically, not character-by-character
- **Battle-tested** — used by AutoHotkey, Dragon NaturallySpeaking, and many STT tools
- Works with CodeMirror (Obsidian), Monaco (VS Code), xterm.js (Windows Terminal)

**Why NOT the original AttachThreadInput + SendInput approach:**
- Character-by-character is slow for typical dictation output (50-200 chars)
- Triggers autocomplete/suggestions on each character
- Clipboard + Ctrl+V is dramatically faster above ~30 characters
- AttachThreadInput can cause deadlocks if not carefully managed

**Implementation strategy:**
1. Save clipboard (`CF_UNICODETEXT` only for fast save/restore)
2. Set clipboard to dictated text
3. SendInput Ctrl+V (4 INPUT events)
4. Sleep 30-50ms for paste processing
5. Restore original clipboard
6. Total overhead: ~50-80ms regardless of text length

**Edge cases:**
- Legacy console (not Windows Terminal): detect via window class, try Ctrl+Shift+V
- Clipboard locked by another app: fall back to SendInput Unicode
- Non-text clipboard data (images, files): warn user, best-effort restore

> Research basis: [Windows Text Injection Methods](research/Windows-Text-Injection-Methods-2026-02-07.md)

### 4.4 Post-Processing: Regex Pipeline

**Decision:** Layered regex post-processing for punctuation commands, filler removal, and normalization.

**Pipeline stages:**

1. **Punctuation commands** — "period" → `.`, "comma" → `,`, "question mark" → `?`
2. **Filler word removal** — Strip "um", "uh", "like", "you know"
3. **Number normalization** — Context-dependent formatting
4. **Custom replacements** — User-configurable via dictionary file
5. **Formatting commands (Phase 3)** — "camel case my variable" → `myVariable`

**Example:**
```python
import re

def process_punctuation_commands(text):
    replacements = {
        r'\bperiod\b': '.',
        r'\bcomma\b': ',',
        r'\bquestion mark\b': '?',
        r'\bexclamation point\b': '!',
        r'\bcolon\b': ':',
        r'\bsemicolon\b': ';',
        r'\bnew line\b': '\n',
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def remove_filler_words(text):
    return re.sub(r'\b(um|uh|like|you know)\b', '', text, flags=re.IGNORECASE)
```

> Research basis: [Code-Aware Dictation Research](Code-Aware%20Dictation%20Research%202026-02-07.md) §4

### 4.5 Custom Vocabulary Dictionary

**Decision:** JSON dictionary file loaded into Whisper's `initial_prompt` parameter.

**Location:** `~/.stvc/dictionary.json`

**Structure:**
```json
{
  "version": 1,
  "description": "Custom vocabulary for STVC speech recognition",
  "categories": {
    "ai_tools": [
      "Claude Code", "Claude", "Anthropic", "MCP",
      "Model Context Protocol", "Copilot", "ChatGPT"
    ],
    "languages": [
      "TypeScript", "JavaScript", "Python", "Rust", "Go"
    ],
    "frameworks": [
      "React", "Next.js", "FastAPI", "Express", "Node.js",
      "Django", "Flask", "Svelte", "Vue"
    ],
    "tools": [
      "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
      "Redis", "npm", "pip", "git", "GitHub", "VS Code"
    ],
    "protocols": [
      "REST", "GraphQL", "WebSocket", "JSON", "API",
      "OAuth", "JWT", "HTTPS", "SSH"
    ],
    "programming": [
      "async", "await", "boolean", "refactor", "middleware",
      "endpoint", "schema", "mutation", "resolver"
    ],
    "custom": []
  }
}
```

**How it works:**
- On startup, STVC loads the dictionary and flattens all categories into a comma-separated string
- The string is passed to faster-whisper's `initial_prompt` parameter
- Whisper uses the prompt as context, making it more likely to predict those terms correctly
- **224 token limit** — the prompt is truncated to fit within Whisper's half-context window

**Usage:**
```python
import json

def load_dictionary(path="~/.stvc/dictionary.json"):
    with open(os.path.expanduser(path)) as f:
        data = json.load(f)
    terms = []
    for category_terms in data["categories"].values():
        terms.extend(category_terms)
    return ", ".join(terms)

# In transcription:
initial_prompt = load_dictionary()
segments, info = model.transcribe(
    audio,
    initial_prompt=initial_prompt,
    language="en"
)
```

**User management:**
- Edit `~/.stvc/dictionary.json` manually
- Future: CLI command `stvc dict add "MyCustomTerm"` → appends to `custom` category
- Future: Auto-extract terms from current codebase/conversation context

> Research basis: [Code-Aware Dictation Research](Code-Aware%20Dictation%20Research%202026-02-07.md) §1 (initial_prompt), §8 (recommendations)

---

## 5. Activation Modes

### Primary: Silero VAD (Hands-Free)

- VAD continuously monitors microphone in background
- Automatically detects when user starts speaking
- Buffers audio while speech is detected
- When silence exceeds `min_silence_duration` (1.0s), triggers transcription
- No hotkey needed — completely hands-free

**Best for:** Extended dictation sessions, vibe coding with Claude Code

### Secondary: Push-to-Talk Hotkey

- User holds configurable hotkey (default: `Alt+E`)
- Audio captured while key is held
- Transcription triggers on key release
- Bypasses VAD entirely — guaranteed start/stop control

**Best for:** Noisy environments, short commands, precision control

### Future: Wake Word (Porcupine)

- User says "Hey Claude" or custom wake phrase
- Wake word engine activates VAD → transcription pipeline
- Completely hands-free, no always-listening overhead
- Porcupine: >95% TPR, <1 false alarm/hour, custom words trainable in seconds

**Planned for:** Phase 4

> Research basis: [STT Approach Analysis](research/STT-Approach-Analysis-2026-02-07.md) §Wake Word Detection

---

## 6. Phased Roadmap

### Phase 1: MVP — Core Pipeline

**Goal:** Working speech-to-text with clipboard injection and push-to-talk.

| Task | Detail |
|------|--------|
| Audio capture | `sounddevice` at 16kHz, mono |
| STT engine | faster-whisper `large-v3-turbo`, CUDA FP16 |
| Text injection | Clipboard + Ctrl+V with save/restore |
| Activation | Push-to-talk hotkey (configurable, default `Alt+E`) |
| Status indicator | System tray icon showing state (idle/listening/transcribing) |
| Configuration | TOML or JSON config file at `~/.stvc/config.toml` |

**Expected performance:**
- Latency: ~0.3-0.5s transcription (warm model)
- Accuracy: ~7-8% WER on general speech

### Phase 2: VAD + Vocabulary

**Goal:** Hands-free operation with improved technical term accuracy.

| Task | Detail |
|------|--------|
| Silero VAD | Hands-free speech detection (threshold 0.5, silence 1.0s, pad 300ms) |
| Custom dictionary | `~/.stvc/dictionary.json` loaded into `initial_prompt` |
| Basic post-processing | Punctuation commands → symbols, filler word removal |
| Audio feedback | Subtle sound on transcription complete |

**Expected performance:**
- Latency: 1.0-1.7s total (1.0s silence detection + 0.3-0.5s transcription)
- Accuracy: Improved on technical terms via initial_prompt

### Phase 3: Polish

**Goal:** Production-quality experience with formatting and optional LLM cleanup.

| Task | Detail |
|------|--------|
| Formatting commands | "camel case X" → `camelCase`, "snake case X" → `snake_case` |
| LLM polish (optional) | On-demand Claude cleanup for critical text |
| System tray UI | Settings panel, microphone selection, dictionary editor |
| Terminal detection | Auto-detect Windows Terminal vs legacy console for paste shortcut |
| Hotkey customization | Full hotkey remapping in settings |

### Phase 4: Advanced

**Goal:** Context-aware transcription and cutting-edge features.

| Task | Detail |
|------|--------|
| Context-aware transcription | Extract terms from active file/conversation for dynamic `initial_prompt` |
| Fine-tuned model | Train Whisper on synthetic technical speech dataset |
| Wake word | Porcupine integration for "Hey Claude" activation |
| Multi-microphone | Beam forming for better noise rejection |
| Adaptive silence threshold | ML-based adjustment to user speech patterns |

---

## 7. Python Dependencies

```
# Core
faster-whisper       # CTranslate2-based Whisper inference (MIT)
torch                # PyTorch for Silero VAD (BSD)
silero-vad           # Voice Activity Detection model (MIT)
sounddevice          # Cross-platform audio capture (MIT)

# Windows injection
pywin32              # win32clipboard, win32gui for clipboard operations
pynput               # Global hotkey listener (no admin needed)

# Optional
pystray              # System tray icon
Pillow               # Icon rendering for system tray
```

**Install:**
```bash
pip install faster-whisper torch silero-vad sounddevice pywin32 pynput
```

---

## 8. Configuration

**Location:** `~/.stvc/config.toml`

```toml
[general]
language = "en"
activation = "vad"          # "vad" | "ptt" | "both"

[model]
name = "large-v3-turbo"
device = "cuda"
compute_type = "float16"
beam_size = 5

[vad]
threshold = 0.5
min_speech_duration = 0.3
min_silence_duration = 1.0
speech_pad_ms = 300

[hotkey]
push_to_talk = "alt+e"

[injection]
method = "clipboard"        # "clipboard" | "sendinput" | "auto"
clipboard_restore = true
paste_delay_ms = 50

[post_processing]
remove_filler_words = true
punctuation_commands = true
formatting_commands = false  # Enable in Phase 3

[dictionary]
path = "~/.stvc/dictionary.json"
```

---

## 9. Research References

All architecture decisions in this plan are backed by comprehensive research conducted on 07 February 2026:

| Research Document | Key Finding for STVC |
|-------------------|---------------------|
| [STT Engine Comparison](research/STT-Engine-Comparison-2026-02-07.md) | faster-whisper large-v3-turbo is best speed/accuracy/Windows combo (score: 4.7/5) |
| [STT Approach Analysis](research/STT-Approach-Analysis-2026-02-07.md) | Hybrid VAD + Batch is the clear winner; streaming NOT recommended |
| [Code-Aware Dictation Research](Code-Aware%20Dictation%20Research%202026-02-07.md) | initial_prompt (224 token limit) + regex pipeline for technical vocabulary |
| [Windows Text Injection Methods](research/Windows-Text-Injection-Methods-2026-02-07.md) | Clipboard + Ctrl+V scores 9/10 reliability; SendInput fallback for edge cases |
| [Existing STT Tools Survey](research/Existing-STT-Tools-Survey-2026-02-07.md) | Key gaps in existing tools that STVC addresses (no VAD, no vocabulary, no AI workflow optimization) |

### Key Corrections from Original Plan (Feb 4)

| Area | Original (Feb 4) | Updated (Research-backed) |
|------|-------------------|---------------------------|
| **Text injection** | AttachThreadInput + SendInput | Clipboard + Ctrl+V (9/10 reliability) |
| **Model** | "small or medium" | large-v3-turbo (809M params, ~7% WER) |
| **VAD** | None planned | Silero VAD (87.7% TPR, 4x fewer errors than WebRTC) |
| **Activation** | Push-to-talk only | VAD hands-free + PTT fallback |
| **Vocabulary** | Not considered | Custom dictionary file + initial_prompt |
| **Post-processing** | Not planned | Regex pipeline (punctuation, fillers, formatting) |
| **Status** | backlog / low priority | **active / high priority** |
