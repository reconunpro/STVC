# STVC Phases 3 & 4 Integration Testing

## Overview
Manual testing checklist for verifying all Phase 3 (Settings GUI) and Phase 4 (Context-Aware Transcription) features.

**Status:** Ready for Manual Testing
**Date:** 2026-02-14
**Swarm:** stvc-phases-3-4 (8 agents)

---

## Prerequisites

1. **Dependencies Installed**
   ```bash
   pip install -r requirements.txt
   # Verify: tomli-w, comtypes, psutil are present
   ```

2. **Configuration Files**
   - Default config created at: `~/.config/stvc/config.toml`
   - Default dictionary at: `~/.config/stvc/dictionary.toml`

3. **Hardware Requirements**
   - CUDA-capable GPU (or CPU fallback)
   - Working microphone
   - Windows OS (for win32gui, UI Automation)

---

## Phase 3: Settings GUI Testing

### Test 1: Settings Window Access
**Goal:** Verify settings window opens from tray icon

- [ ] Start STVC: `python -m stvc`
- [ ] Locate tray icon (gray circle when idle)
- [ ] Right-click tray icon
- [ ] Verify menu shows: "STVC — idle", "Settings...", "Quit"
- [ ] Click "Settings..."
- [ ] Verify settings window opens (600x500 modal window)
- [ ] Verify window is centered on screen
- [ ] Verify window title: "STVC Settings"

**Expected:** Settings window opens successfully with 4 tabs: General, Hotkey, Dictionary, About

---

### Test 2: General Tab - Microphone Selection
**Goal:** Verify audio device selection and live updates

- [ ] Open Settings → General tab
- [ ] Verify "Microphone Device:" label visible
- [ ] Verify dropdown shows audio devices in format: "index: Device Name"
- [ ] Note current device selection
- [ ] Click "Refresh" button
- [ ] Verify device list refreshes
- [ ] Select a different audio device
- [ ] Click "Save"
- [ ] Verify success message: "All settings have been saved successfully."
- [ ] Open config file: `~/.config/stvc/config.toml`
- [ ] Verify `[audio]` section shows: `device = "X"` (selected device index)
- [ ] Perform a test recording (press PTT hotkey)
- [ ] Verify audio is captured from new device

**Expected:** Device changes persist and apply immediately without restart

---

### Test 3: Hotkey Tab - Hotkey Remapping
**Goal:** Verify hotkey capture and live updates

- [ ] Open Settings → Hotkey tab
- [ ] Verify current hotkey displayed (default: "ctrl+f13")
- [ ] Click "Record New Hotkey" button
- [ ] Verify button text changes to "Press key combination..."
- [ ] Verify instructions change to blue: "Press your desired key combination now..."
- [ ] Press: Ctrl+F10
- [ ] Verify label updates to: "ctrl+f10"
- [ ] Verify instructions show: "New hotkey set: ctrl+f10" (green text)
- [ ] Click "Save"
- [ ] Verify success message
- [ ] Close settings window
- [ ] Test new hotkey: Press Ctrl+F10
- [ ] Verify tray icon changes to green (listening)
- [ ] Release Ctrl+F10
- [ ] Verify transcription occurs (icon → yellow → gray)

**Expected:** Hotkey updates immediately without app restart

---

### Test 4: Dictionary Tab - Custom Terms
**Goal:** Verify dictionary editing and persistence

- [ ] Open Settings → Dictionary tab
- [ ] Verify listbox shows existing categories (e.g., [PROGRAMMING], [CUSTOM])
- [ ] Verify "Total terms: X" label at bottom
- [ ] Type "STVC" in text entry field
- [ ] Click "Add Term"
- [ ] Verify "STVC" appears under [CUSTOM] category
- [ ] Verify term count increments
- [ ] Select "STVC" from listbox
- [ ] Click "Remove" button
- [ ] Verify "STVC" is removed from listbox
- [ ] Verify term count decrements
- [ ] Add 3 new terms: "PyTorch", "FastAPI", "SQLAlchemy"
- [ ] Click "Save"
- [ ] Verify success message
- [ ] Close settings window
- [ ] Speak one of the new terms during dictation
- [ ] Verify term is transcribed correctly (case-sensitive)
- [ ] Open `~/.config/stvc/dictionary.toml`
- [ ] Verify `[categories.custom]` contains new terms

**Expected:** Dictionary changes persist and improve transcription accuracy immediately

---

### Test 5: About Tab
**Goal:** Verify version information displayed

- [ ] Open Settings → About tab
- [ ] Verify displays: "STVC"
- [ ] Verify version string: "Version X.X.X"
- [ ] Verify subtitle: "Speech-to-Text for Vibe Coding"
- [ ] Verify description: "A Windows PTT tool with context-aware transcription"

**Expected:** About tab shows correct version and project info

---

### Test 6: Settings Persistence
**Goal:** Verify all settings persist across restarts

- [ ] Change hotkey to: Ctrl+F11
- [ ] Change audio device to device index 1
- [ ] Add custom term: "TestTerm123"
- [ ] Save all settings
- [ ] Close STVC completely (Quit from tray)
- [ ] Restart STVC: `python -m stvc`
- [ ] Open Settings
- [ ] Verify hotkey shows: "ctrl+f11"
- [ ] Verify audio device shows: "1: ..."
- [ ] Verify dictionary contains: "TestTerm123"
- [ ] Test hotkey: Press Ctrl+F11
- [ ] Verify recording starts

**Expected:** All settings persist correctly after restart

---

## Phase 4: Context-Aware Transcription Testing

### Test 7: VS Code Context Extraction
**Goal:** Verify context terms extracted from VS Code

- [ ] Open VS Code with a Python file containing terms: "AudioRecorder", "transcriber", "hotkey_listener"
- [ ] Click into the editor (make VS Code active window)
- [ ] Press PTT hotkey
- [ ] Speak: "add audio recorder instance"
- [ ] Release PTT
- [ ] Check STVC console logs for: "Extracted X context terms: ['AudioRecorder', ...]"
- [ ] Verify transcription includes correct capitalization: "add AudioRecorder instance"
- [ ] Verify "AudioRecorder" is properly cased (not "audio recorder")

**Expected:** Terms from active file improve transcription accuracy

---

### Test 8: Notepad++ Context Extraction
**Goal:** Verify context extraction from Notepad++

- [ ] Open Notepad++ with a file containing: "FastAPI", "Pydantic", "uvicorn"
- [ ] Make Notepad++ the active window
- [ ] Press PTT hotkey
- [ ] Speak: "import fast api"
- [ ] Check logs for: "Active window: notepadpp - ..."
- [ ] Verify transcription: "import FastAPI" (correct casing)

**Expected:** Notepad++ context terms extracted and used

---

### Test 9: Terminal Context Extraction
**Goal:** Verify UI Automation extracts terminal content

- [ ] Open Windows Terminal or PowerShell
- [ ] Type commands: "git status", "pip install torch"
- [ ] Make terminal active window
- [ ] Press PTT hotkey
- [ ] Speak: "run pie torch"
- [ ] Check logs for: "Active window: terminal - ..."
- [ ] Verify transcription: "run PyTorch" or "run torch"

**Expected:** Terminal content extracted via UI Automation

---

### Test 10: Context Disable/Enable
**Goal:** Verify context feature can be toggled

- [ ] Open `~/.config/stvc/config.toml`
- [ ] Add section:
   ```toml
   [context]
   enabled = false
   ```
- [ ] Restart STVC
- [ ] Open VS Code with code terms
- [ ] Press PTT and speak a technical term
- [ ] Check logs: Should NOT show "Extracted X context terms"
- [ ] Verify transcription uses only base dictionary
- [ ] Set `enabled = true`
- [ ] Restart STVC
- [ ] Repeat test
- [ ] Verify context extraction resumes

**Expected:** Context feature respects enabled flag

---

### Test 11: Context Fallback
**Goal:** Verify graceful fallback when context unavailable

- [ ] Open a generic app (e.g., Calculator, Notepad without content)
- [ ] Make it active window
- [ ] Press PTT and speak
- [ ] Check logs for: "No content extracted from active window" or "Context extraction failed, using base dictionary"
- [ ] Verify transcription still works (uses base dictionary only)

**Expected:** No crashes, graceful fallback to base dictionary

---

### Test 12: Prompt Token Budget
**Goal:** Verify merged prompt stays within 224 token limit

- [ ] Open VS Code with a file containing 100+ unique terms
- [ ] Press PTT and speak
- [ ] Check logs for: "Extracted X context terms: ..."
- [ ] Verify log shows prompt building (terms merged)
- [ ] Estimate token count: Each term ≈ 1-2 tokens, max ~50 terms used
- [ ] Verify transcription works (not truncated by API)

**Expected:** Context terms are trimmed to fit token budget, transcription succeeds

---

## Error Handling Tests

### Test 13: Invalid Hotkey
**Goal:** Verify invalid hotkey handling

- [ ] Open Settings → Hotkey tab
- [ ] Click "Record New Hotkey"
- [ ] Press only a modifier (Ctrl alone, no main key)
- [ ] Verify error message: "No valid key captured. Click 'Record New Hotkey' to try again."
- [ ] Record valid hotkey: Ctrl+F9
- [ ] Verify success

**Expected:** Invalid hotkeys rejected with clear error message

---

### Test 14: No Audio Devices
**Goal:** Verify behavior when no microphones found

- [ ] Disable all audio input devices in Windows
- [ ] Open Settings → General tab
- [ ] Click "Refresh"
- [ ] Verify dropdown shows: "No input devices found"
- [ ] Verify console log: "No audio input devices found"
- [ ] Re-enable audio device
- [ ] Click "Refresh"
- [ ] Verify devices appear

**Expected:** Graceful handling of missing devices with clear message

---

### Test 15: Config File Corruption
**Goal:** Verify recovery from corrupt config

- [ ] Stop STVC
- [ ] Edit `~/.config/stvc/config.toml` with invalid TOML syntax (missing quote)
- [ ] Start STVC
- [ ] Verify STVC starts with defaults (logs error but continues)
- [ ] Open Settings
- [ ] Verify defaults loaded (e.g., default hotkey: "ctrl+f13")

**Expected:** Graceful recovery, uses defaults, logs error

---

## Integration Tests

### Test 16: End-to-End Workflow
**Goal:** Full workflow from startup to dictation with context

- [ ] Start STVC fresh: `python -m stvc`
- [ ] Verify tray icon appears (gray)
- [ ] Open Settings
- [ ] Set hotkey: Ctrl+F12
- [ ] Select microphone device
- [ ] Add custom term: "MyCustomTerm"
- [ ] Save and close settings
- [ ] Open VS Code with Python code
- [ ] Focus a code editor line
- [ ] Press Ctrl+F12 (tray → green)
- [ ] Speak: "add my custom term here"
- [ ] Release Ctrl+F12 (tray → yellow → gray)
- [ ] Verify text injected at cursor: "add MyCustomTerm here"
- [ ] Verify context terms from code used (check logs)

**Expected:** Complete workflow succeeds with context-aware transcription

---

### Test 17: Concurrent Settings Changes
**Goal:** Verify multiple settings changes in one session

- [ ] Open Settings
- [ ] Change hotkey to Ctrl+F11
- [ ] Change audio device to different index
- [ ] Add dictionary term: "ConcurrentTest"
- [ ] Save all at once
- [ ] Verify success message
- [ ] Test PTT with new hotkey
- [ ] Speak "concurrent test"
- [ ] Verify transcription: "ConcurrentTest"
- [ ] Verify audio from new device

**Expected:** All changes apply simultaneously without conflicts

---

### Test 18: Rapid PTT Presses
**Goal:** Verify locking prevents race conditions

- [ ] Press PTT hotkey rapidly 5 times in 1 second
- [ ] Verify tray icon state (should ignore extra presses)
- [ ] Check logs for: "Already processing, ignoring press."
- [ ] Perform normal PTT press
- [ ] Verify works correctly

**Expected:** Processing lock prevents race conditions

---

## Performance Tests

### Test 19: Settings Window Performance
**Goal:** Verify GUI remains responsive

- [ ] Open Settings with 100+ dictionary terms
- [ ] Scroll dictionary listbox
- [ ] Switch between tabs rapidly
- [ ] Verify no lag or freezing
- [ ] Add/remove multiple terms
- [ ] Verify instant updates

**Expected:** GUI remains responsive with large datasets

---

### Test 20: Context Extraction Speed
**Goal:** Verify context extraction doesn't delay transcription

- [ ] Open large file (1000+ lines) in VS Code
- [ ] Press PTT and speak
- [ ] Time from hotkey release to text injection
- [ ] Verify context extraction adds <500ms overhead
- [ ] Check logs for timing info

**Expected:** Context extraction is fast, minimal delay

---

## Regression Tests

### Test 21: Phase 1-2 Features Still Work
**Goal:** Verify previous functionality intact

- [ ] Press PTT hotkey
- [ ] Speak a sentence with filler words: "um, this is, uh, a test"
- [ ] Verify output: "This is a test" (fillers removed)
- [ ] Speak question: "what is the time"
- [ ] Verify output: "what is the time?" (question mark added)
- [ ] Verify dictionary terms from Phase 1 still apply
- [ ] Verify post-processing still works

**Expected:** All Phase 1-2 features remain functional

---

## Checklist Summary

**Phase 3 Tests (Settings GUI):**
- [ ] Test 1: Settings Window Access
- [ ] Test 2: Microphone Selection
- [ ] Test 3: Hotkey Remapping
- [ ] Test 4: Dictionary Editor
- [ ] Test 5: About Tab
- [ ] Test 6: Settings Persistence

**Phase 4 Tests (Context-Aware):**
- [ ] Test 7: VS Code Context
- [ ] Test 8: Notepad++ Context
- [ ] Test 9: Terminal Context
- [ ] Test 10: Context Toggle
- [ ] Test 11: Context Fallback
- [ ] Test 12: Token Budget

**Error Handling:**
- [ ] Test 13: Invalid Hotkey
- [ ] Test 14: No Audio Devices
- [ ] Test 15: Config Corruption

**Integration:**
- [ ] Test 16: End-to-End Workflow
- [ ] Test 17: Concurrent Changes
- [ ] Test 18: Rapid PTT Presses

**Performance:**
- [ ] Test 19: GUI Performance
- [ ] Test 20: Context Speed

**Regression:**
- [ ] Test 21: Phase 1-2 Features

---

## Test Results

**Date Tested:** _____________
**Tester:** _____________
**Tests Passed:** ____ / 21
**Tests Failed:** ____ / 21

**Issues Found:**
1.
2.
3.

**Notes:**


---

## Sign-Off

- [ ] All critical tests passed
- [ ] No blocking issues found
- [ ] Phase 3 & 4 implementation verified complete

**Approved By:** _____________
**Date:** _____________
