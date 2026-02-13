# STVC Phases 3 & 4 Implementation Plan

**Created:** 13 February 2026
**Status:** Ready for execution
**Project:** C:\Users\ReconUnPro\Documents\GitHub\STVC

---

## Context

### Original Request
Implement Phase 3 (Settings GUI) and Phase 4 (Context-Aware Transcription) of STVC, the Windows speech-to-text tool for vibe coding workflows.

### Current State (Phases 1 & 2 Complete)
- Working PTT pipeline: hotkey -> audio capture -> faster-whisper transcription -> post-processing -> SendInput injection
- System tray icon with color-coded states (idle/listening/transcribing)
- Custom dictionary loaded into Whisper's `initial_prompt`
- Post-processing pipeline (question mark fix, filler removal)
- Config via `~/.stvc/config.toml`, dictionary via `~/.stvc/dictionary.json`

### Codebase Architecture
```
src/stvc/
  __init__.py      # Version string
  __main__.py      # python -m stvc entry point
  app.py           # STVCApp orchestrator — ties all components together
  config.py        # TOML config loader, dictionary loader, defaults
  audio.py         # AudioRecorder — sounddevice InputStream capture
  transcriber.py   # Transcriber — faster-whisper wrapper
  postprocess.py   # Regex pipeline (question marks, filler removal)
  injector.py      # SendInput Unicode text injection (ctypes)
  hotkey.py        # HotkeyListener — pynput global keyboard hook
  tray.py          # TrayIcon — pystray with colored circle icons
```

### Key Integration Points
- `STVCApp.__init__()` loads config, creates components
- `STVCApp.start()` initializes AudioRecorder, Transcriber, TrayIcon, HotkeyListener
- `TrayIcon._build_menu()` returns pystray.Menu with status label + Quit
- `TrayIcon.__init__(on_quit=)` takes a single callback
- `AudioRecorder.__init__()` uses default sounddevice device (no device param)
- `HotkeyListener.__init__(hotkey_str=, on_press=, on_release=)` parses hotkey string
- `Transcriber.__init__(initial_prompt=)` sets prompt at construction time
- `config.load_config()` returns dict, `config.load_dictionary()` returns comma-separated string
- Config defaults in `config.DEFAULTS` dict, dictionary defaults in `config.DEFAULT_DICTIONARY`

### Dependencies
- Python 3.10+, faster-whisper, sounddevice, pywin32, pynput, pystray, Pillow

---

## Work Objectives

### Core Objective
Add a settings GUI accessible from the system tray and implement context-aware transcription that dynamically enriches the Whisper vocabulary based on the active window content.

### Deliverables
1. **Settings Window** (tkinter) — opened from system tray right-click menu
2. **Microphone Selection** — dropdown listing available input devices, persisted to config
3. **Dictionary Editor** — add/remove/view custom vocabulary terms
4. **Hotkey Remapping** — change PTT hotkey from the GUI with live capture
5. **Window Detection** — identify the active foreground application
6. **Content Extraction** — read text from VS Code, Notepad++, terminals
7. **Term Extraction** — parse identifiers, function names, technical terms from content
8. **Dynamic Prompt Merging** — combine base dictionary + context terms for `initial_prompt`

### Definition of Done
- Settings window opens from tray menu, all fields save to `~/.stvc/config.toml` and `~/.stvc/dictionary.json`
- Microphone selection works and persists across restarts
- Dictionary editor can add/remove terms from the `custom` category
- Hotkey remapping captures a new key combo and applies it live (no restart)
- Context extraction detects VS Code, Notepad++, and terminal windows
- Extracted terms are merged into `initial_prompt` before each transcription
- All new modules have docstrings and logging consistent with existing code
- No regressions in existing PTT pipeline

---

## Must Have / Must NOT Have

### MUST Have
- tkinter for the settings GUI (stdlib, no new dependencies)
- Settings window opened via tray menu item (not a separate process)
- Config changes persist to `~/.stvc/config.toml` and `~/.stvc/dictionary.json`
- Microphone selection uses `sounddevice.query_devices()` to list devices
- AudioRecorder accepts an optional `device` parameter
- Hotkey remapping applies live without app restart
- Window detection via `win32gui.GetForegroundWindow()` + `GetWindowText()`
- Content extraction via Windows Automation API (UI Automation) for editor text
- Term extraction is a simple regex/heuristic parser (no NLP library)
- Dynamic prompt merging happens per-transcription, not on a timer
- 224-token limit respected when building merged `initial_prompt`

### MUST NOT Have
- No new heavyweight dependencies (no Qt, no wxPython, no electron)
- No background polling of window content on a timer (extract only at PTT press time)
- No clipboard-based content extraction (use UI Automation or file reading)
- No internet connectivity requirements for context extraction
- No modification to the existing SendInput injection logic
- No changes to the faster-whisper model or compute configuration
- No breaking changes to existing config.toml format (additive only)

---

## Architecture Design

### Phase 3: Settings GUI

**New file: `src/stvc/settings.py`**

A tkinter-based settings window with tabbed interface (ttk.Notebook):
- **General tab**: Microphone selection dropdown, language selector
- **Hotkey tab**: Current hotkey display, "Press new hotkey" capture button
- **Dictionary tab**: List of terms by category, add/remove buttons for custom terms
- **About tab**: Version, links

The settings window is a `tk.Toplevel` spawned from the main `tk.Tk` root that lives hidden. This is necessary because tkinter requires a root window, but we do not want one visible. The root is created once on app start and withdrawn immediately.

**Integration with tray.py:**
- Add "Settings" menu item to `TrayIcon._build_menu()`
- TrayIcon gets a new `on_settings` callback
- `STVCApp` creates the settings window and passes config/callbacks

**Config write-back: `config.py` additions:**
- `save_config(config: dict)` — serialize config dict to TOML and write to `~/.stvc/config.toml`
- `save_dictionary(categories: dict)` — write dictionary JSON
- Requires `tomli-w` (or manual TOML serialization) for writing TOML

**Audio device selection: `audio.py` changes:**
- `AudioRecorder.__init__(device=None)` — accept optional device index/name
- `AudioRecorder.start()` passes `device=` to `sd.InputStream()`
- New function `list_audio_devices() -> list[dict]` returning input devices from `sd.query_devices()`

**Live hotkey remapping: `hotkey.py` changes:**
- `HotkeyListener.update_hotkey(hotkey_str)` — stop current listener, re-parse, restart
- Settings UI calls this method when user confirms new hotkey

### Phase 4: Context-Aware Transcription

**New file: `src/stvc/context/window_detect.py`**

Detects the foreground window using Win32 API:
- `get_active_window() -> WindowInfo` — returns dataclass with `hwnd`, `title`, `process_name`, `exe_path`
- Uses `win32gui.GetForegroundWindow()`, `GetWindowText()`, `GetWindowThreadProcessId()`, `psutil.Process().name()` (or ctypes equivalent)

**New file: `src/stvc/context/extractors.py`**

Content extraction strategies per application type:
- `VSCodeExtractor` — reads from VS Code's active file via the window title (which contains the file path), then reads the file directly from disk
- `NotepadPPExtractor` — same approach: parse file path from title bar, read from disk
- `TerminalExtractor` — for Windows Terminal / cmd: use UI Automation to read visible text from the terminal buffer
- `GenericExtractor` — fallback: attempt UI Automation `TextPattern` on the active window
- Factory function `get_extractor(window_info: WindowInfo) -> BaseExtractor`

**New file: `src/stvc/context/term_parser.py`**

Extracts technical terms from raw text:
- `extract_terms(text: str, max_terms: int = 50) -> list[str]`
- Regex patterns for: camelCase identifiers, snake_case identifiers, PascalCase class names, UPPER_CASE constants, dotted module paths, quoted strings that look like tech terms
- Deduplication and frequency-based ranking (most frequent terms first)
- Filter out common English words (small stop-word list)

**New file: `src/stvc/context/merger.py`**

Merges base dictionary with context terms:
- `build_prompt(base_terms: str, context_terms: list[str], max_tokens: int = 224) -> str`
- Base dictionary terms come first (always included)
- Context terms appended until token budget is reached
- Simple token estimation: `len(term) / 4` (Whisper tokenizer averages ~4 chars/token)

**Integration with `app.py`:**

The context pipeline runs at PTT release time (after audio capture, before transcription):

```
PTT released
  -> recorder.stop()
  -> get_active_window()           # ~1ms, win32 call
  -> get_extractor(window).extract()  # ~5-50ms, file read or UI Automation
  -> extract_terms(content)        # ~1ms, regex
  -> build_prompt(base, context)   # ~0ms
  -> transcriber.transcribe(audio, initial_prompt=merged_prompt)
```

This requires `Transcriber.transcribe()` to accept an optional `initial_prompt` override parameter, so the dynamic prompt can be passed per-call without changing the base prompt.

**New dependency:** `comtypes` (for UI Automation COM interface) — or use `ctypes` directly with `UIAutomationCore.dll`. The `comtypes` approach is cleaner.

---

## Task Flow and Dependencies

```
PHASE 3 (Settings GUI)
=======================

[T1] config.py: add save_config() and save_dictionary()
  |
  v
[T2] audio.py: add device param + list_audio_devices()
  |
  v
[T3] hotkey.py: add update_hotkey() method  ----+
  |                                              |
  v                                              v
[T4] settings.py: build tkinter settings window (uses T1, T2, T3)
  |
  v
[T5] tray.py: add Settings menu item + on_settings callback
  |
  v
[T6] app.py: wire settings window, tray menu, config persistence (uses T4, T5)


PHASE 4 (Context-Aware Transcription)
=======================================

[T7] context/window_detect.py: active window detection
  |
  v
[T8] context/extractors.py: content extraction per app type (uses T7)
  |
  v
[T9] context/term_parser.py: regex term extraction  (independent)
  |
  v
[T10] context/merger.py: prompt merging logic (independent)
  |
  v
[T11] transcriber.py: add per-call initial_prompt override
  |
  v
[T12] app.py: integrate context pipeline into PTT release flow (uses T7-T11)


CROSS-PHASE
============

[T13] pyproject.toml + requirements.txt: add new dependencies (comtypes, tomli-w)
[T14] Integration testing: full flow test with settings + context
```

### Dependency Graph

```
T1 ──────────────────┐
T2 ──────────────────┤
T3 ──────────────────┼──> T4 ──> T5 ──> T6
                     |
T7 ──> T8 ───┐      |
T9 ───────────┼──> T12
T10 ──────────┘      |
T11 ─────────────────┘
T13 (independent, do early)
T14 (after T6 + T12)
```

### Parallelization Groups

**Wave 1 (fully parallel, no dependencies):**
- T1: config save functions
- T2: audio device selection
- T3: hotkey update method
- T7: window detection
- T9: term parser
- T10: prompt merger
- T11: transcriber override
- T13: dependency updates

**Wave 2 (depends on Wave 1):**
- T4: settings window (needs T1, T2, T3)
- T8: content extractors (needs T7)

**Wave 3 (depends on Wave 2):**
- T5: tray menu update (needs T4)
- T6: app.py Phase 3 wiring (needs T4, T5)
- T12: app.py Phase 4 wiring (needs T8, T9, T10, T11)

**Wave 4 (depends on Wave 3):**
- T14: integration testing (needs T6, T12)

---

## Detailed TODOs

### T1: Config Save Functions
**File:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\config.py`
**Acceptance Criteria:**
- Add `save_config(config: dict) -> None` that writes TOML to `~/.stvc/config.toml`
- Add `save_dictionary(data: dict) -> None` that writes JSON to `~/.stvc/dictionary.json`
- Add `load_dictionary_raw(path: str | None = None) -> dict` that returns the full dictionary dict (not just flattened string) for the editor UI
- Handle file write errors gracefully (log warning, do not crash)
- Use `tomli_w` for TOML serialization (add to dependencies)
- Preserve existing `load_config()` and `load_dictionary()` unchanged

### T2: Audio Device Selection
**File:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\audio.py`
**Acceptance Criteria:**
- Add `list_audio_devices() -> list[dict]` function returning `[{"index": int, "name": str, "channels": int, "sample_rate": float}]` for input-capable devices
- Modify `AudioRecorder.__init__()` to accept `device: int | str | None = None`
- Pass `device=` to `sd.InputStream()` constructor in `start()`
- Add `[audio]` section to `config.DEFAULTS` with `device = ""` (empty = system default)
- Default behavior (device=None) unchanged from current

### T3: Hotkey Update Method
**File:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\hotkey.py`
**Acceptance Criteria:**
- Add `HotkeyListener.update_hotkey(hotkey_str: str) -> None` method
- Method stops current listener, re-parses hotkey string, restarts listener
- Thread-safe (uses existing listener lifecycle)
- Log old and new hotkey on change

### T4: Settings Window (tkinter)
**New file:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\settings.py`
**Acceptance Criteria:**
- Class `SettingsWindow` that creates a `tk.Toplevel`
- Uses `ttk.Notebook` with 3 tabs: General, Hotkey, Dictionary
- **General tab:**
  - Microphone dropdown (`ttk.Combobox`) populated from `list_audio_devices()`
  - "Refresh" button to re-scan devices
  - Currently selected device shown
- **Hotkey tab:**
  - Label showing current hotkey (e.g., "ctrl+f13")
  - "Record New Hotkey" button that enters capture mode
  - In capture mode, next key combination is captured and displayed
  - "Apply" button to confirm new hotkey
- **Dictionary tab:**
  - `tk.Listbox` showing all terms (grouped by category headers)
  - "Add Term" button + text entry for custom category
  - "Remove" button for selected custom term (cannot remove non-custom terms)
  - Term count display
- "Save" button at bottom saves all changes via `save_config()` and `save_dictionary()`
- "Cancel" button closes without saving
- Window is modal (grabs focus) and centered on screen
- Accepts callbacks: `on_hotkey_change(hotkey_str)`, `on_device_change(device)`, `on_dictionary_change(terms_str)`
- Accepts current config dict and dictionary dict for initial population

### T5: Tray Menu Update
**File:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\tray.py`
**Acceptance Criteria:**
- Add `on_settings` callback parameter to `TrayIcon.__init__()`
- Add "Settings..." menu item between status label and Quit in `_build_menu()`
- Clicking "Settings..." invokes `on_settings` callback
- Menu order: Status (disabled) | separator | Settings... | Quit

### T6: App.py Phase 3 Wiring
**File:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\app.py`
**Acceptance Criteria:**
- Create hidden `tk.Tk()` root window in `STVCApp.__init__()` (withdrawn immediately)
- Instantiate `SettingsWindow` manager (lazy, created on first open)
- Pass `on_settings=self._open_settings` to `TrayIcon`
- `_open_settings()` creates/shows settings window with current config
- On hotkey change: call `self._hotkey.update_hotkey(new_str)` + update config
- On device change: update config, restart AudioRecorder with new device
- On dictionary change: update `self._transcriber.initial_prompt`
- Periodically pump tkinter event loop (`root.update()`) from the main wait loop OR use `root.after()` from a dedicated thread
- Save config on every settings change

### T7: Window Detection
**New file:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\context\__init__.py`
**New file:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\context\window_detect.py`
**Acceptance Criteria:**
- Dataclass `WindowInfo` with fields: `hwnd: int`, `title: str`, `process_name: str`, `exe_path: str`
- Function `get_active_window() -> WindowInfo`
- Uses `win32gui.GetForegroundWindow()` and `GetWindowText()`
- Uses `win32process.GetWindowThreadProcessId()` + `psutil.Process()` or ctypes `OpenProcess` + `QueryFullProcessImageName` for process info
- Returns `WindowInfo` with best-effort fields (empty string if unavailable)
- Helper `detect_app_type(info: WindowInfo) -> str` returns one of: "vscode", "notepadpp", "terminal", "unknown"
- Detection based on process name and/or window title patterns

### T8: Content Extractors
**New file:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\context\extractors.py`
**Acceptance Criteria:**
- Abstract base class `BaseExtractor` with `extract(window_info: WindowInfo) -> str`
- `FileBasedExtractor` — reads file path from window title, reads file from disk
  - Used for VS Code (title format: "filename - folder - Visual Studio Code")
  - Used for Notepad++ (title format: "filename - Notepad++")
  - Reads up to first 50KB of the file
- `TerminalExtractor` — uses UI Automation `TextPattern` to read visible terminal text
  - Fallback: return empty string if UI Automation fails
- `GenericExtractor` — returns empty string (no extraction for unknown apps)
- Factory function `get_extractor(app_type: str) -> BaseExtractor`
- All extractors catch exceptions and return empty string on failure (never crash the pipeline)

### T9: Term Parser
**New file:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\context\term_parser.py`
**Acceptance Criteria:**
- Function `extract_terms(text: str, max_terms: int = 50) -> list[str]`
- Regex patterns to identify:
  - camelCase words (e.g., `getUserName`)
  - snake_case words (e.g., `get_user_name`)
  - PascalCase words (e.g., `UserService`)
  - UPPER_CASE constants (e.g., `MAX_RETRIES`)
  - Dotted paths (e.g., `stvc.config`)
  - Common framework/library names (detected by capitalization patterns)
- Stop-word filter: remove common English words, single characters, pure numbers
- Frequency-based ranking: most-used terms first
- Deduplication (case-insensitive)
- Returns ordered list capped at `max_terms`

### T10: Prompt Merger
**New file:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\context\merger.py`
**Acceptance Criteria:**
- Function `build_prompt(base_terms: str, context_terms: list[str], max_tokens: int = 224) -> str`
- Base terms always included first
- Context terms appended in order until estimated token count reaches `max_tokens`
- Token estimation: `ceil(len(term) / 4)` per term, plus 1 token per separator
- Deduplication: context terms already in base_terms are skipped
- Returns comma-separated string ready for `initial_prompt`

### T11: Transcriber Per-Call Prompt Override
**File:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\transcriber.py`
**Acceptance Criteria:**
- Modify `Transcriber.transcribe()` signature to accept optional `initial_prompt: str | None = None`
- If provided, use it instead of `self.initial_prompt` for that call
- If `None`, fall back to `self.initial_prompt` (current behavior preserved)
- Add `update_base_prompt(prompt: str)` method for settings UI to update base prompt

### T12: App.py Phase 4 Integration
**File:** `C:\Users\ReconUnPro\Documents\GitHub\STVC\src\stvc\app.py`
**Acceptance Criteria:**
- Import context modules: `window_detect`, `extractors`, `term_parser`, `merger`
- In `_on_ptt_release()`, after `recorder.stop()` and before `transcriber.transcribe()`:
  1. Call `get_active_window()` to get window info
  2. Call `detect_app_type()` and `get_extractor()` to get content
  3. Call `extract_terms()` on the content
  4. Call `build_prompt()` with base dictionary + context terms
  5. Pass merged prompt to `transcriber.transcribe(audio, initial_prompt=merged_prompt)`
- Add config option `[context] enabled = true` to toggle context extraction
- If context extraction is disabled or fails, fall back to base dictionary only
- Log extracted context terms at DEBUG level
- Entire context pipeline must complete in <100ms (file reads are the bottleneck)

### T13: Dependency Updates
**Files:** `pyproject.toml`, `requirements.txt`
**Acceptance Criteria:**
- Add `tomli-w` to dependencies (TOML write support, needed for config save)
- Add `comtypes` to dependencies (UI Automation for terminal content extraction)
- Add `psutil` to dependencies (process name detection for window identification)
- Keep all existing dependencies unchanged

### T14: Integration Testing
**Acceptance Criteria:**
- Manual test: open settings from tray, change microphone, save, verify next recording uses new mic
- Manual test: remap hotkey in settings, verify new hotkey works immediately
- Manual test: add custom term in dictionary editor, verify it appears in transcription prompt
- Manual test: open VS Code with a Python file, press PTT, verify context terms extracted (check DEBUG logs)
- Manual test: verify existing PTT pipeline still works with no regressions
- Manual test: verify settings persist across app restart

---

## Commit Strategy

### Commit 1: Wave 1 foundation (T1, T2, T3, T7, T9, T10, T11, T13)
"Add config save, audio device selection, hotkey update, context extraction foundations"

### Commit 2: Wave 2 features (T4, T8)
"Add tkinter settings window and content extractors"

### Commit 3: Wave 3 integration (T5, T6, T12)
"Wire settings GUI to tray and integrate context pipeline"

### Commit 4: Polish (T14)
"Integration testing fixes and polish"

---

## Success Criteria

1. User can right-click tray icon and open a settings window
2. Settings window lists available microphones and allows selection
3. Dictionary editor shows all terms and allows adding/removing custom terms
4. Hotkey can be remapped live from settings without restart
5. All settings persist to `~/.stvc/config.toml` and `~/.stvc/dictionary.json`
6. Context extraction detects VS Code and reads active file content
7. Technical terms from active file appear in transcription vocabulary
8. Entire context extraction adds <100ms to the transcription pipeline
9. Existing PTT pipeline works identically when context is disabled
10. No new heavyweight dependencies (tkinter is stdlib, comtypes/tomli-w/psutil are lightweight)

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| tkinter event loop conflicts with pystray thread | Settings window freezes | Use `root.after()` scheduling; keep tkinter on main thread |
| UI Automation fails on some terminals | No context from terminal apps | Graceful fallback to empty context; file-based extraction for editors is reliable |
| VS Code title format changes across versions | File path parsing breaks | Use regex with multiple patterns; fallback to no context |
| Hotkey capture in settings captures PTT hotkey | Conflict during remap | Temporarily disable PTT listener during hotkey capture mode |
| TOML write library compatibility | Config save fails | tomli-w is the standard complement to tomllib; well-tested |
| 224 token limit exceeded with large context | Whisper ignores excess tokens | Token counting in merger.py enforces the limit strictly |

---

## New File Structure After Implementation

```
src/stvc/
  __init__.py
  __main__.py
  app.py              # Modified: tkinter root, settings wiring, context pipeline
  config.py           # Modified: save_config(), save_dictionary(), load_dictionary_raw()
  audio.py            # Modified: device param, list_audio_devices()
  transcriber.py      # Modified: per-call initial_prompt, update_base_prompt()
  postprocess.py      # Unchanged
  injector.py         # Unchanged
  hotkey.py           # Modified: update_hotkey()
  tray.py             # Modified: Settings menu item, on_settings callback
  settings.py         # NEW: tkinter settings window
  context/
    __init__.py        # NEW: package init
    window_detect.py   # NEW: active window detection
    extractors.py      # NEW: per-app content extraction
    term_parser.py     # NEW: regex term extraction
    merger.py          # NEW: prompt merging with token budget
```
