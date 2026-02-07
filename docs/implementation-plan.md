---
title: System-Wide STT with Local Whisper
created: 04-02-2026
tags: [idea, tooling, stt, whisper, windows]
status: backlog
priority: low
---

# System-Wide STT with Local Whisper

**Created:** 04 February 2026

## Overview

Build a unified speech-to-text service that works across all applications (Claude Code, Obsidian, any app) using locally-run Whisper AI with GPU acceleration.

## Current State

- Using `claude-stt` plugin with Moonshine engine
- Latency feels like 2-3 seconds in practice
- Injection breaks when windows are snapped/maximized
- Only works reliably with Claude Code

## Goals

1. **Faster transcription** - Sub-1 second using faster-whisper + RTX 4070
2. **Universal injection** - Works in any app (Claude Code, Obsidian, etc.)
3. **Reliable with snapped windows** - Fix the window focus issue
4. **True injection** - Not clipboard paste

## Technical Approach

### Speech Engine

Use **faster-whisper** with GPU acceleration:

| Setting | Value |
|---------|-------|
| Engine | faster-whisper |
| Model | small or medium |
| Device | CUDA (RTX 4070) |
| Compute Type | float16 |
| Expected Latency | 0.5-1 second |

### The Window Focus Problem

Windows has "foreground lock" - apps can't steal focus. `SetForegroundWindow()` is often ignored, breaking injection for snapped/maximized windows.

### The Fix: AttachThreadInput

```python
import ctypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def attach_and_focus(hwnd):
    # Get thread IDs
    my_thread = kernel32.GetCurrentThreadId()
    target_thread = user32.GetWindowThreadProcessId(hwnd, None)

    # Attach threads (share input state)
    user32.AttachThreadInput(my_thread, target_thread, True)

    # NOW SetForegroundWindow works reliably
    user32.SetForegroundWindow(hwnd)

    # Detach threads (cleanup)
    user32.AttachThreadInput(my_thread, target_thread, False)
```

**Why it works:** When threads are attached, Windows thinks you're part of the same input context, bypassing the foreground lock.

### Complete Flow

```
Step 1: Capture target HWND before recording
           ↓
Step 2: User speaks, audio recorded
           ↓
Step 3: faster-whisper transcribes → text (~0.5-1s)
           ↓
Step 4: AttachThreadInput(my_thread, target_thread)
           ↓
Step 5: SetForegroundWindow(hwnd)  ← Now works reliably
           ↓
Step 6: AttachThreadInput(..., False)  ← Detach
           ↓
Step 7: SendInput(keystrokes)  ← Types into focused window
           ↓
Step 8: Text appears in target app
```

## Alternative Injection Methods

| Method | Pros | Cons |
|--------|------|------|
| SendInput + AttachThreadInput | True injection, works with snapped | Slight focus flicker |
| PostMessage WM_CHAR | No focus needed | Doesn't work with Electron apps |
| UI Automation | Modern API | Slow, complex |
| Clipboard + Ctrl+V | Most reliable | Not true injection |

## Implementation Options

### Option A: Modify claude-stt

- Fix window.py with AttachThreadInput
- Switch engine to faster-whisper
- Keep existing hotkey system

### Option B: Standalone Python Tool

- ~200 lines of Python
- faster-whisper + Win32 APIs
- Independent of Claude Code ecosystem
- Works anywhere

## Hardware

- GPU: RTX 4070 (more than sufficient)
- Expected VRAM usage: ~2-4GB for medium model

## References

- faster-whisper: https://github.com/guillaumekln/faster-whisper
- claude-stt plugin: `~/.claude/plugins/marketplaces/jarrodwatts-claude-stt/`
- Windows SendInput: https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput
- AttachThreadInput: https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-attachthreadinput

## Next Steps (When Prioritized)

1. Test AttachThreadInput fix on current claude-stt
2. Benchmark faster-whisper latency on RTX 4070
3. Decide: modify claude-stt vs build standalone
4. Implement and test across Claude Code + Obsidian
