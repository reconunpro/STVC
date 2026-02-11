---
title: STVC Implementation Plan
created: 07-02-2026
tags: [implementation, tooling, stt, whisper, windows, voice-coding]
status: active
priority: high
---

# STVC Implementation Plan

**Created:** 07 February 2026
**Updated:** 08 February 2026 (revised — VAD, LLM polish, wake word moved to future-upgrades.md)

## 1. Overview

**STVC (Speech-to-Text for Vibe Coding)** is a system-wide, locally-processed speech-to-text tool for Windows that converts spoken natural language into text and injects it into any application — Claude Code (Windows Terminal), Obsidian, Google Docs, VS Code, or any text field.

### Why We're Building This

Existing tools have critical gaps for AI-assisted coding workflows:

| Gap                                     | Detail                                                                                    |
| --------------------------------------- | ----------------------------------------------------------------------------------------- |
| **claude-stt uses Moonshine**           | 27-62M param models lack vocabulary depth for long-form dictation vs 809M+ Whisper models |
| **Injection breaks on snapped windows** | Current claude-stt injection unreliable with window management                            |
| **No custom vocabulary**                | Technical terms (API, TypeScript, MCP) frequently misrecognized                           |
| **No post-processing pipeline**         | Raw transcription output without cleanup                                                  |

### Target Use Cases

- **Claude Code** — Dictate natural language instructions into the terminal
- **Obsidian** — Write notes, documentation, and knowledge base entries
- **Google Docs / Web apps** — Draft prose and technical writing
- **Any application** — System-wide text injection via SendInput Unicode

### What STVC Is NOT

STVC dictates **intent in natural language**, not code syntax. Users say "add a function that validates email addresses" — not "def validate underscore email open paren."

> See: [Code-Aware Dictation Research](Code-Aware%20Dictation%20Research%202026-02-07.md) §6 for vibe coding specifics.

---

## 2. Hardware & Environment

| Component          | Specification                     |
| ------------------ | --------------------------------- |
| **GPU**            | NVIDIA RTX 4070 (12 GB VRAM)      |
| **OS**             | Windows 11                        |
| **Runtime**        | Python 3.10+                      |
| **VRAM Budget**    | ~1.6 GB (model)                   |
| **Remaining VRAM** | ~10.4 GB free for other workloads |

The RTX 4070's 12 GB VRAM and Tensor Cores easily accommodate the large-v3-turbo model with FP16 inference, leaving substantial headroom.

---

## 3. Architecture

### Pipeline

```
┌─────────────────────────────────────────────────┐
│  PUSH-TO-TALK HOTKEY (Alt+E)                     │
│  - Hold to record, release to transcribe         │
└────────────────────┬────────────────────────────┘
                     │
                     ▼ (key held)
┌─────────────────────────────────────────────────┐
│  MICROPHONE (16kHz Audio Capture)                │
│  - Records while hotkey is held                  │
│  - Stops on key release                          │
└────────────────────┬────────────────────────────┘
                     │
                     ▼ (key released)
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
│  - Auto-punctuation (Whisper native)             │
│  - Question mark fix for interrogatives          │
│  - Filler word removal (um, uh, like)            │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  TEXT INJECTION                                   │
│  - SendInput Unicode (KEYEVENTF_UNICODE)         │
│  - Direct to focused window, no clipboard        │
│  - No focus stealing, no snapped window movement │
└─────────────────────────────────────────────────┘
```

### Design Principles

1. **Push-to-talk** — User controls when recording starts/stops via hotkey. Simple, reliable, no false activations.
2. **Batch processing** — Full utterance context produces highest accuracy. Streaming is explicitly rejected (lower accuracy, Whisper not designed for it).
3. **Warm model** — Keep faster-whisper loaded in GPU memory. Cold start ~2-3s; warm inference <500ms.
4. **Direct SendInput injection** — Text is injected character-by-character via SendInput Unicode into the already-focused window. No clipboard manipulation, no focus stealing, no snapped window rearrangement.

---

## 4. Core Components

### 4.1 STT Engine: faster-whisper with large-v3-turbo

**Decision:** Use faster-whisper (CTranslate2-based) with the large-v3-turbo model.

| Attribute        | Value                        |
| ---------------- | ---------------------------- |
| **Engine**       | faster-whisper (CTranslate2) |
| **Model**        | large-v3-turbo               |
| **Parameters**   | 809M                         |
| **VRAM**         | ~1.6 GB                      |
| **Device**       | CUDA (RTX 4070)              |
| **Compute type** | float16                      |
| **Latency**      | ~0.3-0.5s for 10s audio      |
| **WER**          | ~7-8% (LibriSpeech)          |
| **License**      | MIT                          |

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

### 4.2 Text Injection: SendInput Unicode (Direct)

**Decision:** SendInput with `KEYEVENTF_UNICODE` flag — direct character injection into the focused window. No clipboard involvement.

| Attribute                   | Value                                                |
| --------------------------- | ---------------------------------------------------- |
| **Method**                  | `SendInput` with `KEYEVENTF_UNICODE`                 |
| **Speed**                   | ~1ms per character (~50-200ms for typical dictation) |
| **Clipboard disruption**    | None                                                 |
| **Focus stealing**          | None — injects into already-focused window           |
| **Snapped window movement** | None                                                 |
| **Admin required**          | No (unless target is elevated)                       |

**Why SendInput Unicode (not clipboard):**

- **No clipboard disruption** — user's clipboard is never touched
- **No snapped window rearrangement** — no `SetForegroundWindow` call needed; text goes to whatever window already has focus
- **No race conditions** — no clipboard save/restore timing issues
- **Full Unicode support** — `wScan` field carries the Unicode codepoint directly
- **Simple implementation** — no clipboard format detection, save, restore logic
- The user is already focused on their target app (Claude Code terminal, Obsidian, etc.) when they press the PTT hotkey and speak

**Why NOT clipboard + Ctrl+V:**

- Clipboard save/restore adds complexity and race conditions
- Clipboard managers (Ditto, etc.) log injected text
- The core reason for building STVC custom is to avoid window/focus disruption that clipboard approaches can cause

**Performance for typical dictation:**

| Utterance length | Characters | SendInput time |
| ---------------- | ---------- | -------------- |
| Short command    | ~30 chars  | ~30ms          |
| One sentence     | ~100 chars | ~100ms         |
| Long instruction | ~300 chars | ~300ms         |

These times are well within acceptable range — the user just finished speaking (1+ seconds of audio), so an additional 100-300ms for injection is imperceptible.

**Implementation:**

```python
import ctypes
from ctypes import wintypes

SendInput = ctypes.windll.user32.SendInput

def inject_text(text: str):
    """Inject text via SendInput KEYEVENTF_UNICODE into focused window."""
    events = []
    for char in text:
        # Key down
        events.append(make_unicode_input(char, flags=KEYEVENTF_UNICODE))
        # Key up
        events.append(make_unicode_input(char, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))

    array = (INPUT * len(events))(*events)
    SendInput(len(events), ctypes.pointer(array), ctypes.sizeof(INPUT))
```

**Edge cases:**

- UIPI: non-elevated process cannot inject into elevated windows (silent failure). Warn user if target appears to be admin.
- Very long text (>500 chars): still works, just takes longer (~500ms). Acceptable for dictation.

> Research basis: [Windows Text Injection Methods](research/Windows-Text-Injection-Methods-2026-02-07.md)

### 4.3 Post-Processing: Regex Pipeline

**Decision:** Layered regex post-processing for punctuation commands, filler removal, and normalization.

**Punctuation approach:** Whisper natively produces auto-punctuation (periods, commas, capitalization) in its transcription output — no spoken commands needed. However, Whisper sometimes drops question marks. Post-processing fixes this and cleans up filler words.

**Pipeline stages:**

1. **Question mark fix** — Detect interrogative patterns Whisper missed and insert `?`
2. **Filler word removal** — Strip "um", "uh", "like", "you know"
3. **Number normalization** — Context-dependent formatting
4. **Custom replacements** — User-configurable via dictionary file

**Example:**

```python
import re

def fix_missing_question_marks(text):
    """Add question marks to interrogative sentences Whisper missed."""
    interrogative = r'((?:^|[.!?]\s+)(?:who|what|where|when|why|how|can|could|would|should|is|are|do|does|did|will|shall|have|has|had)\b[^.!?]*)\.'
    return re.sub(interrogative, r'\1?', text, flags=re.IGNORECASE)

def remove_filler_words(text):
    text = re.sub(r'\b(um|uh|like|you know)\b', '', text, flags=re.IGNORECASE)
    return re.sub(r'  +', ' ', text).strip()  # clean up double spaces
```

> Research basis: [Code-Aware Dictation Research](Code-Aware%20Dictation%20Research%202026-02-07.md) §4

### 4.4 Custom Vocabulary Dictionary

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

## 5. Activation

Push-to-talk hotkey (default: `Alt+E`). Hold to record, release to transcribe and inject.

- Guaranteed start/stop control — no false activations
- No background mic monitoring — only records while key is held
- Configurable hotkey via `~/.stvc/config.toml`

> For hands-free alternatives (VAD, wake word), see [Future Upgrades](future-upgrades.md).

---

## 6. Phased Roadmap

### Phase 1: MVP — Core Pipeline

**Goal:** Working speech-to-text with SendInput injection and push-to-talk.

| Task             | Detail                                                       |
| ---------------- | ------------------------------------------------------------ |
| Audio capture    | `sounddevice` at 16kHz, mono                                 |
| STT engine       | faster-whisper `large-v3-turbo`, CUDA FP16                   |
| Text injection   | SendInput Unicode (`KEYEVENTF_UNICODE`) into focused window  |
| Activation       | Push-to-talk hotkey (configurable, default `Alt+E`)          |
| Status indicator | System tray icon showing state (idle/listening/transcribing) |
| Configuration    | TOML or JSON config file at `~/.stvc/config.toml`            |

**Expected performance:**

- Latency: ~0.3-0.5s transcription (warm model)
- Accuracy: ~7-8% WER on general speech

### Phase 2: Vocabulary + Post-Processing

**Goal:** Improved technical term accuracy and cleaner output.

| Task              | Detail                                                 |
| ----------------- | ------------------------------------------------------ |
| Custom dictionary | `~/.stvc/dictionary.json` loaded into `initial_prompt` |
| Post-processing   | Question mark fix, filler word removal                 |

### Phase 3: Polish

**Goal:** Production-quality settings and customization.

| Task                 | Detail                                                  |
| -------------------- | ------------------------------------------------------- |
| System tray UI       | Settings panel, microphone selection, dictionary editor |
| Hotkey customization | Full hotkey remapping in settings                       |

### Phase 4: Advanced

**Goal:** Context-aware transcription.

| Task                        | Detail                                                                   |
| --------------------------- | ------------------------------------------------------------------------ |
| Context-aware transcription | Extract terms from active file/conversation for dynamic `initial_prompt` |

> For other potential upgrades (VAD, wake word, LLM polish, multi-mic), see [Future Upgrades](future-upgrades.md).

---

## 7. Python Dependencies

```
# Core
faster-whisper       # CTranslate2-based Whisper inference (MIT)
sounddevice          # Cross-platform audio capture (MIT)

# Windows injection
pywin32              # win32gui for window detection, ctypes for SendInput
pynput               # Global hotkey listener (no admin needed)

# Optional
pystray              # System tray icon
Pillow               # Icon rendering for system tray
```

**Install:**

```bash
pip install faster-whisper sounddevice pywin32 pynput
```

---

## 8. Configuration

**Location:** `~/.stvc/config.toml`

```toml
[general]
language = "en"
activation = "ptt"

[model]
name = "large-v3-turbo"
device = "cuda"
compute_type = "float16"
beam_size = 5

[hotkey]
push_to_talk = "alt+e"

[injection]
method = "sendinput"        # "sendinput" | "clipboard" | "auto"

[post_processing]
remove_filler_words = true
fix_question_marks = true

[dictionary]
path = "~/.stvc/dictionary.json"
```

---

## 9. Research References

All architecture decisions in this plan are backed by comprehensive research conducted on 07 February 2026:

| Research Document                                                                       | Key Finding for STVC                                                                        |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| [STT Engine Comparison](research/STT-Engine-Comparison-2026-02-07.md)                   | faster-whisper large-v3-turbo is best speed/accuracy/Windows combo (score: 4.7/5)           |
| [STT Approach Analysis](research/STT-Approach-Analysis-2026-02-07.md)                   | Batch processing is optimal; streaming NOT recommended                                      |
| [Code-Aware Dictation Research](Code-Aware%20Dictation%20Research%202026-02-07.md)      | initial_prompt (224 token limit) + regex pipeline for technical vocabulary                  |
| [Windows Text Injection Methods](research/Windows-Text-Injection-Methods-2026-02-07.md) | SendInput Unicode — direct injection, no clipboard, no snapped window disruption            |
| [Existing STT Tools Survey](research/Existing-STT-Tools-Survey-2026-02-07.md)           | Key gaps in existing tools that STVC addresses (no vocabulary, no AI workflow optimization) |

### Key Corrections from Original Plan (Feb 4)

| Area                | Original (Feb 4)              | Updated (Research-backed)                                              |
| ------------------- | ----------------------------- | ---------------------------------------------------------------------- |
| **Text injection**  | AttachThreadInput + SendInput | SendInput Unicode — no clipboard, no window movement                   |
| **Model**           | "small or medium"             | large-v3-turbo (809M params, ~7% WER)                                  |
| **Activation**      | Push-to-talk only             | Push-to-talk (VAD moved to [Future Upgrades](future-upgrades.md))      |
| **Vocabulary**      | Not considered                | Custom dictionary file + initial_prompt                                |
| **Post-processing** | Not planned                   | Auto-punctuation (Whisper native) + question mark fix + filler removal |
| **Status**          | backlog / low priority        | **active / high priority**                                             |
