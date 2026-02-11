---
title: Windows Text Injection Methods Research
created: 07-02-2026
tags: [research, windows, text-injection, sendinput, ui-automation]
---

# Windows Text Injection Methods Research

**Research Date:** 07 February 2026

## Coverage Key

<span style="color:#3498db">?åç</span> Global/Cross-platform | <span style="color:#2ecc71">??∫??∏</span> Windows-specific

## Executive Summary

- **Clipboard + Ctrl+V** is the most reliable and fastest method for injecting text into arbitrary Windows applications, including Electron apps (Obsidian, VS Code) and terminals (Windows Terminal, PowerShell). It works universally because every text-accepting control supports paste.
- **SendInput (character-by-character)** is the most natural-feeling approach and works broadly, but is slower for large text blocks and subject to UIPI integrity level restrictions.
- **UI Automation (IValueProvider.SetValue)** is the cleanest API-level approach but has limited support in Electron/Chromium apps and terminals, making it unsuitable as a primary method.
- **PostMessage/SendMessage with WM_CHAR** is fundamentally unreliable per Microsoft's own guidance and should be avoided entirely.
- **For a speech-to-text tool targeting Claude Code (terminal) and Obsidian (Electron):** Use **Clipboard + Ctrl+V as primary** with **SendInput as fallback** for edge cases where clipboard disruption is unacceptable.

---

## Method 1: AttachThreadInput + SendInput <span style="color:#2ecc71">??∫??∏</span>

### How It Works

[SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput) synthesizes keyboard (and mouse) input events by inserting `INPUT` structures into the system input stream. [AttachThreadInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-attachthreadinput) allows one thread to share input state (focus, keyboard state) with another thread, enabling `SetFocus` calls across thread boundaries.

**Typical pattern:**

1. `AttachThreadInput(myThread, targetThread, TRUE)` -- share input queues
2. `SetForegroundWindow(targetHwnd)` / `SetFocus(targetHwnd)` -- ensure target has focus
3. `SendInput(...)` -- inject keystroke events
4. `AttachThreadInput(myThread, targetThread, FALSE)` -- detach

### Reliability

| Aspect                                       | Rating                                         | Notes                                                                                             |
| -------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Snapped/maximized windows**                | Good                                           | Works regardless of window arrangement; focus is the key factor                                   |
| **Electron apps (Obsidian, VS Code)**        | Good                                           | SendInput feeds the OS input queue; Electron receives standard keyboard events                    |
| **Terminals (Windows Terminal, PowerShell)** | Good                                           | Windows Terminal accepts SendInput keystrokes; ConPTY translates them to VT sequences             |
| **Speed**                                    | Moderate                                       | Character-by-character; no inter-key delay with SendInput mode, but still sequential              |
| **Focus-stealing**                           | <span style="color:#ff6b6b">Yes</span>         | Must bring target to foreground; steals focus from calling application                            |
| **Admin required**                           | <span style="color:#ff6b6b">Conditional</span> | UIPI blocks injection into higher-integrity processes. Non-admin cannot inject into admin windows |
| **Python availability**                      | Excellent                                      | `ctypes.windll.user32.SendInput`, `pyautogui`, `pynput`, `keyboard` all use SendInput             |

### Pros

- Simulates real keyboard input; applications cannot easily distinguish from physical typing
- Maintains proper keyboard state (GetKeyState returns correct values)
- No clipboard disruption
- Events are serialized atomically (no interleaving with other input)

### Cons

- Requires foreground focus -- cannot inject into background windows
- Subject to UIPI: non-elevated process cannot send to elevated process, and **the failure is silent** (no error code returned)
- AttachThreadInput can cause deadlocks if not carefully managed
- Slower than clipboard paste for large text blocks
- Character-by-character means intermediate states are visible (e.g., autocomplete triggers)

### UIPI Integrity Level Detail

Per [Microsoft documentation](https://learn.microsoft.com/en-us/archive/msdn-technet-forums/b68a77e7-cd00-48d0-90a6-d6a4a46a95aa), applications can only inject input into processes at equal or lesser integrity level. A standard (medium IL) process cannot SendInput to an admin (high IL) process. The `uiAccess="true"` manifest flag can bypass UIPI but requires the application to be signed and installed in a secure location (Program Files).

---

## Method 2: UI Automation (Microsoft UIA) <span style="color:#2ecc71">??∫??∏</span>

### How It Works

[Microsoft UI Automation](https://learn.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32) provides structured access to UI elements through control patterns. For text injection, the relevant pattern is `IValueProvider.SetValue()`, which directly sets the value of a control without simulating keystrokes.

**Python libraries:** [uiautomation](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows) (wraps COM via comtypes), [pywinauto](https://github.com/pywinauto/pywinauto)

**Typical pattern:**

```python
import uiautomation as auto
edit = auto.EditControl(Name="...")
edit.GetValuePattern().SetValue("injected text")
```

### Reliability

| Aspect                                       | Rating                                  | Notes                                                                                                                                                                      |
| -------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Snapped/maximized windows**                | Excellent                               | UIA works regardless of window position or state                                                                                                                           |
| **Electron apps (Obsidian, VS Code)**        | <span style="color:#ff6b6b">Poor</span> | Chromium exposes accessibility tree but `ValuePattern` is often not implemented on content-editable regions. Obsidian's editor (CodeMirror) does not expose IValueProvider |
| **Terminals (Windows Terminal, PowerShell)** | <span style="color:#ff6b6b">Poor</span> | Terminal controls do not implement ValuePattern; they are essentially canvas-style renders                                                                                 |
| **Speed**                                    | Excellent                               | Direct property set; instantaneous regardless of text length                                                                                                               |
| **Focus-stealing**                           | <span style="color:#2ecc71">No</span>   | Can set values without bringing window to foreground                                                                                                                       |
| **Admin required**                           | No                                      | UIA uses cross-process COM; works within same integrity level                                                                                                              |
| **Python availability**                      | Good                                    | `uiautomation` package (comtypes-based); `pywinauto` with UIA backend                                                                                                      |

### Pros

- No focus stealing -- can inject text into background windows
- No clipboard disruption
- Instantaneous for any text length
- Proper API-level integration; triggers change events correctly
- Works beautifully with WPF, WinForms, UWP, and traditional Win32 edit controls

### Cons

- <span style="color:#ff6b6b;font-weight:bold">Critical limitation:</span> Electron/Chromium apps often do not implement `IValueProvider` on their text areas. Chromium's native UIA support [was improved in 2024](https://developer.chrome.com/blog/windows-uia-support-update) but primarily for accessibility reading, not writing
- Terminal emulators generally do not expose editable text patterns
- Multi-line edit controls use `ITextProvider` (read-only access) rather than `IValueProvider`
- Requires comtypes; Python 3.7.6 and 3.8.1 have known comtypes bugs
- Slower to set up (COM initialization, tree walking to find elements)

### Electron/Chromium UIA Status

As of 2024-2025, [Chromium has native UIA support](https://developer.chrome.com/blog/windows-uia-support) replacing the old MSAA-to-UIA proxy layer. However, UIA's `TextPattern` in Chromium is designed as a **read-only** solution for screen readers and Braille devices, not for text injection. The `ValuePattern.SetValue` method is generally not available on Chromium content-editable elements.

---

## Method 3: PostMessage / SendMessage WM_CHAR <span style="color:#2ecc71">??∫??∏</span>

### How It Works

`PostMessage` and `SendMessage` can deliver `WM_CHAR`, `WM_KEYDOWN`, and `WM_KEYUP` messages directly to a window's message queue, bypassing the input system entirely.

### Reliability

| Aspect                        | Rating                                    | Notes                                                                     |
| ----------------------------- | ----------------------------------------- | ------------------------------------------------------------------------- |
| **Snapped/maximized windows** | N/A                                       | <span style="color:#ff6b6b">Fundamentally unreliable</span>               |
| **Electron apps**             | <span style="color:#ff6b6b">Broken</span> | Chromium ignores posted keyboard messages                                 |
| **Terminals**                 | <span style="color:#ff6b6b">Broken</span> | Does not go through ConPTY input path                                     |
| **Speed**                     | Fast                                      | Direct message delivery                                                   |
| **Focus-stealing**            | No                                        | Can target any window handle                                              |
| **Admin required**            | No                                        | Messages can cross process boundaries (with UIPI caveats for WM_COPYDATA) |
| **Python availability**       | Good                                      | `ctypes.windll.user32.PostMessageW`, `win32gui.PostMessage`               |

### Why This Method Should Be Avoided

Raymond Chen's authoritative articles on "The Old New Thing" blog explain this definitively:

- [You can't simulate keyboard input with PostMessage](https://devblogs.microsoft.com/oldnewthing/20050530-11/?p=35513) (2005)
- [You can't simulate keyboard input with PostMessage, revisited](https://devblogs.microsoft.com/oldnewthing/20250319-00/?p=110979) (2025)

**Core problem:** PostMessage goes directly to the window procedure without updating the kernel-side keyboard state. When the application calls `GetKeyState()`, `GetAsyncKeyState()`, or `GetKeyboardState()`, the actual key state does not match what the messages claim. The application discovers "it's all a ruse."

**Specific failures:**

- `WM_KEYDOWN` for character keys is ignored in WinUI3/Chromium because `TranslateMessage` never ran
- Keyboard accelerators and shortcuts fail because the accelerator table lookup checks real key state
- `WM_CHAR` may work for simple edit controls but fails in modern frameworks that validate input state
- Input method editors (IME) state is not updated
- Low-level keyboard hooks never fire (they are input-system hooks, not message hooks)

### Verdict

<span style="color:#ff6b6b;font-weight:bold">Do not use.</span> This method is fundamentally broken by design and will fail unpredictably across applications.

---

## Method 4: Clipboard + Ctrl+V (Save/Restore) <span style="color:#2ecc71">??∫??∏</span>

### How It Works

1. Save current clipboard contents (all formats)
2. Set clipboard to desired text (`CF_UNICODETEXT`)
3. Simulate Ctrl+V keystroke via SendInput
4. Wait brief period for paste to complete
5. Restore original clipboard contents

**Python implementation:**

```python
import win32clipboard
import ctypes

# Save clipboard
win32clipboard.OpenClipboard()
saved_formats = {}
fmt = win32clipboard.EnumClipboardFormats(0)
while fmt:
    try:
        saved_formats[fmt] = win32clipboard.GetClipboardData(fmt)
    except Exception:
        pass
    fmt = win32clipboard.EnumClipboardFormats(fmt)
win32clipboard.CloseClipboard()

# Set new text
win32clipboard.OpenClipboard()
win32clipboard.EmptyClipboard()
win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
win32clipboard.CloseClipboard()

# Send Ctrl+V via SendInput
# ... (SendInput with VK_CONTROL down, 'V' down, 'V' up, VK_CONTROL up)

# Brief delay for paste to process
import time
time.sleep(0.05)

# Restore clipboard
win32clipboard.OpenClipboard()
win32clipboard.EmptyClipboard()
for fmt, data in saved_formats.items():
    try:
        win32clipboard.SetClipboardData(fmt, data)
    except Exception:
        pass
win32clipboard.CloseClipboard()
```

### Reliability

| Aspect                                       | Rating                                                        | Notes                                                                                      |
| -------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **Snapped/maximized windows**                | Excellent                                                     | Paste works in any window arrangement                                                      |
| **Electron apps (Obsidian, VS Code)**        | <span style="color:#2ecc71;font-weight:bold">Excellent</span> | Every Electron app supports Ctrl+V; Chromium clipboard handling is robust                  |
| **Terminals (Windows Terminal, PowerShell)** | <span style="color:#2ecc71;font-weight:bold">Excellent</span> | Windows Terminal supports Ctrl+V natively; legacy consoles use Ctrl+Shift+V or right-click |
| **Speed**                                    | <span style="color:#2ecc71;font-weight:bold">Excellent</span> | Instantaneous regardless of text length; entire text inserted in single operation          |
| **Focus-stealing**                           | <span style="color:#ff6b6b">Yes</span>                        | Still requires SendInput for the Ctrl+V, so target must have focus                         |
| **Admin required**                           | Conditional                                                   | Same UIPI constraints as SendInput for the Ctrl+V keystroke                                |
| **Python availability**                      | Excellent                                                     | `win32clipboard` (pywin32), `pyperclip`, or `ctypes` with Win32 API                        |

### Pros

- **Universally compatible** -- every text-accepting application supports paste
- **Instant** -- 100KB of text pastes as fast as 5 characters
- **No character encoding issues** -- CF_UNICODETEXT handles full Unicode
- **No autocomplete triggers** -- text appears atomically, not character-by-character
- **Battle-tested** -- AutoHotkey, Dragon NaturallySpeaking, and many speech-to-text tools use this approach
- Works with CodeMirror (Obsidian), Monaco (VS Code), xterm.js (terminals)

### Cons

- **Clipboard disruption** -- even with save/restore, there is a brief window where clipboard contents change
- **Race conditions** -- another application may read the clipboard during the injection window
- **Clipboard listeners** -- clipboard manager applications (Ditto, ClipboardFusion) will log the injected text
- **Save/restore complexity** -- some clipboard formats (CF_BITMAP, CF_HDROP for files, OLE objects) are difficult to save and restore perfectly
- **Terminal paste mode** -- some terminals use Ctrl+Shift+V instead of Ctrl+V; requires detection
- **Timing sensitivity** -- need a small delay between setting clipboard and sending Ctrl+V, and between paste and restore

### Save/Restore Limitations

Not all clipboard formats can be reliably saved and restored:

- **CF_UNICODETEXT / CF_TEXT**: Easy to save/restore
- **CF_BITMAP / CF_DIB**: Requires careful memory handling
- **CF_HDROP (file paths)**: Requires GlobalAlloc/DROPFILES structure reconstruction
- **Delayed rendering formats**: Cannot be captured; the source application provides data on demand
- **OLE/COM objects**: Extremely complex to preserve

**Practical mitigation:** For a speech-to-text tool, saving only CF_UNICODETEXT and CF_TEXT is usually sufficient. Most users will have text on their clipboard, not complex objects. If complex clipboard contents are detected, warn the user or fall back to SendInput character-by-character.

---

## Method 5: Virtual Keyboard Drivers (Interception) <span style="color:#2ecc71">??∫??∏</span>

### How It Works

The [Interception driver](https://github.com/oblitum/Interception) installs a kernel-mode filter driver that sits below the input stack. It can intercept real device input and inject synthetic input that is indistinguishable from hardware input (no `LLMHF_INJECTED` flag).

### Reliability

| Aspect                        | Rating                                                                                        | Notes                                                                           |
| ----------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Snapped/maximized windows** | Excellent                                                                                     | Kernel-level injection; window state irrelevant                                 |
| **Electron apps**             | Excellent                                                                                     | Indistinguishable from real hardware input                                      |
| **Terminals**                 | Excellent                                                                                     | Goes through full input stack including ConPTY                                  |
| **Speed**                     | Good                                                                                          | Character-by-character but very low-level                                       |
| **Focus-stealing**            | Yes                                                                                           | Still requires target to have focus to receive input                            |
| **Admin required**            | <span style="color:#ff6b6b;font-weight:bold">Yes -- driver installation requires admin</span> |                                                                                 |
| **Python availability**       | Limited                                                                                       | No official Python bindings; requires C wrapper or ctypes to `interception.dll` |

### Pros

- Input is **truly indistinguishable** from hardware keyboard -- no LLMHF_INJECTED flag
- Bypasses UIPI entirely (kernel-level)
- Can inject into elevated/admin windows from non-admin context (after driver install)
- Used in aviation training, accessibility, SCADA systems

### Cons

- **Requires kernel driver installation** -- admin rights, reboot required
- **Security risk** -- kernel driver has full system access; anti-virus may flag it
- **Licensing** -- LGPL for non-commercial; commercial license required for products
- **Maintenance burden** -- driver must be compatible with each Windows version/update
- **Overkill** for speech-to-text -- same focus requirement as SendInput
- **No official Python bindings** -- must build a ctypes wrapper or use C#/Node.js wrappers
- Can brick keyboard/mouse if driver malfunctions (documented [Issue #117](https://github.com/oblitum/Interception/issues/117))

### Verdict

<span style="color:#f1c40f">Not recommended for speech-to-text.</span> The admin requirement, driver installation, and maintenance burden far outweigh the benefits over SendInput. Only justified for anti-cheat bypass or when LLMHF_INJECTED flag detection is a problem (not the case for STT tools).

---

## Method 6: Python Libraries (pyautogui, pynput, keyboard) <span style="color:#3498db">?åç</span>

### How They Work

These are Python wrappers around the Win32 SendInput API. On Windows, they all ultimately call `ctypes.windll.user32.SendInput`.

| Library                                                             | Backend on Windows                        | Key Feature                                  | Install                     |
| ------------------------------------------------------------------- | ----------------------------------------- | -------------------------------------------- | --------------------------- |
| [pyautogui](https://pypi.org/project/PyAutoGUI/)                    | SendInput (keyboard), mouse_event (mouse) | Cross-platform, screenshot, locate on screen | `pip install pyautogui`     |
| [pynput](https://pypi.org/project/pynput/)                          | SendInput with scan codes                 | Keyboard/mouse listener + controller         | `pip install pynput`        |
| [keyboard](https://pypi.org/project/keyboard/)                      | SendInput                                 | Global hotkeys, recording, playback          | `pip install keyboard`      |
| [pydirectinput](https://github.com/learncodebygaming/pydirectinput) | SendInput with DirectInput scan codes     | Game input (DirectInput vs WM_INPUT)         | `pip install pydirectinput` |

### Reliability

Since all libraries use SendInput under the hood, their reliability profile matches Method 1 exactly:

| Aspect                        | Rating                                                     | Notes                                                                                 |
| ----------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **Snapped/maximized windows** | Good                                                       | Same as SendInput                                                                     |
| **Electron apps**             | Good                                                       | Same as SendInput                                                                     |
| **Terminals**                 | Good                                                       | Same as SendInput                                                                     |
| **Speed**                     | Moderate                                                   | Character-by-character; pyautogui adds 0.1s default pause between keys (configurable) |
| **Focus-stealing**            | Yes                                                        | All require target to have focus                                                      |
| **Admin required**            | Conditional                                                | Same UIPI constraints; `keyboard` library **requires root/admin for listener**        |
| **Python availability**       | <span style="color:#2ecc71;font-weight:bold">Native</span> | All are pip-installable                                                               |

### Library-Specific Notes

**pyautogui:**

- `pyautogui.write("text")` types character-by-character using SendInput
- Default `PAUSE = 0.1` seconds between actions (set `pyautogui.PAUSE = 0` for speed)
- `write()` only works with single-character keys; cannot type Unicode characters outside ASCII
- Cross-platform: same API on Windows, macOS, Linux

**pynput:**

- `keyboard.Controller().type("text")` sends via SendInput with proper scan codes
- Better Unicode support than pyautogui
- Can both listen and inject (useful for hotkey-triggered dictation)
- DPI awareness issues noted on Windows

**keyboard:**

- `keyboard.write("text")` sends via SendInput
- **Requires admin/root to install keyboard hooks** (listener functionality)
- Supports hotkey registration: `keyboard.add_hotkey('ctrl+shift+d', callback)`
- Records and replays key sequences

### Verdict

<span style="color:#3498db">Good convenience wrappers</span> but provide no advantage over direct SendInput via ctypes for text injection. Choose based on additional features needed:

- Need hotkey listener without admin? Use **pynput**
- Need cross-platform + screenshots? Use **pyautogui**
- Need recording/replay? Use **keyboard** (but note admin requirement)
- For pure text injection, **direct ctypes SendInput** avoids the dependency

---

## Method 7: Direct stdin Piping for CLI Apps <span style="color:#3498db">?åç</span>

### How It Works

For command-line applications, text can be piped directly to the process's standard input (stdin) handle, bypassing the display/input stack entirely.

**Python:**

```python
import subprocess
proc = subprocess.Popen(['cmd.exe'], stdin=subprocess.PIPE)
proc.stdin.write(b"echo hello\r\n")
proc.stdin.flush()
```

**ConPTY approach:**
Write directly to the ConPTY input pipe handle that feeds the pseudo-console.

### Reliability

| Aspect                           | Rating                                            | Notes                                                         |
| -------------------------------- | ------------------------------------------------- | ------------------------------------------------------------- |
| **Snapped/maximized windows**    | N/A                                               | No window interaction; pipe-based                             |
| **Electron apps**                | <span style="color:#ff6b6b">Not applicable</span> | Electron apps are GUI; no stdin                               |
| **Terminals (Windows Terminal)** | <span style="color:#ff6b6b">Very Limited</span>   | Cannot access an existing terminal's ConPTY pipe from outside |
| **Speed**                        | Excellent                                         | Direct pipe write; no input simulation overhead               |
| **Focus-stealing**               | No                                                | No window interaction at all                                  |
| **Admin required**               | No                                                | Standard process I/O                                          |
| **Python availability**          | Native                                            | `subprocess.PIPE`, `os.write()`                               |

### Pros

- Zero overhead; fastest possible text delivery
- No focus requirements
- No clipboard disruption
- Works perfectly when you own/spawn the target process

### Cons

- <span style="color:#ff6b6b;font-weight:bold">Cannot inject into an existing terminal session you did not spawn</span>
- Does not work for GUI applications at all
- Cannot target a specific Windows Terminal tab/pane from outside
- ConPTY pipe handles are private to the terminal host process
- The user's Claude Code session is an existing process; you cannot get its stdin pipe handle

### Verdict

<span style="color:#ff6b6b">Not viable for the speech-to-text use case.</span> The tool needs to inject text into whatever application currently has focus. Stdin piping only works when you control the process lifecycle, which is not the case for dictating into Claude Code or Obsidian.

---

## Comprehensive Comparison Table

| Criterion                     | SendInput | UI Automation | PostMessage | Clipboard+Paste | Interception | Python Libs   | stdin Pipe    |
| ----------------------------- |:---------:|:-------------:|:-----------:|:---------------:|:------------:|:-------------:|:-------------:|
| **Electron (Obsidian)**       | Good      | Poor          | Broken      | **Excellent**   | Excellent    | Good          | N/A           |
| **Electron (VS Code)**        | Good      | Poor          | Broken      | **Excellent**   | Excellent    | Good          | N/A           |
| **Windows Terminal**          | Good      | Poor          | Broken      | **Excellent**   | Excellent    | Good          | N/A*          |
| **PowerShell console**        | Good      | Poor          | Broken      | **Excellent**   | Excellent    | Good          | N/A*          |
| **Win32 edit controls**       | Good      | **Excellent** | Partial     | **Excellent**   | Excellent    | Good          | N/A           |
| **WPF/UWP apps**              | Good      | **Excellent** | Partial     | **Excellent**   | Excellent    | Good          | N/A           |
| **Speed (large text)**        | Slow      | **Instant**   | Fast        | **Instant**     | Slow         | Slow          | **Instant**   |
| **Speed (short text)**        | Good      | Good          | Fast        | Good            | Good         | Good          | **Instant**   |
| **No focus needed**           | No        | **Yes**       | **Yes**     | No              | No           | No            | **Yes**       |
| **No clipboard disruption**   | **Yes**   | **Yes**       | **Yes**     | No              | **Yes**      | **Yes**       | **Yes**       |
| **No admin required**         | Mostly    | **Yes**       | **Yes**     | Mostly          | No           | Mostly        | **Yes**       |
| **Unicode support**           | Good      | **Excellent** | Poor        | **Excellent**   | Good         | Varies        | **Excellent** |
| **UIPI bypass**               | No        | No            | No          | No              | **Yes**      | No            | N/A           |
| **Python ecosystem**          | Good      | Good          | Good        | **Excellent**   | Poor         | **Excellent** | **Excellent** |
| **Implementation complexity** | Low       | Medium        | Low         | Medium          | High         | **Very Low**  | Low           |
| **Reliability score**         | 7/10      | 5/10          | 1/10        | **9/10**        | 8/10         | 7/10          | 3/10          |

*N/A for stdin means: cannot access an existing terminal session's stdin from outside.

---

## Recommendation for STVC Speech-to-Text Tool

### Primary Method: Clipboard + Ctrl+V (with Save/Restore)

**Why:** It is the only method that scores "Excellent" across all target applications (Obsidian, VS Code, Windows Terminal, PowerShell). It handles any text length instantly and works with the complex input handling of CodeMirror (Obsidian), Monaco (VS Code), and xterm.js (Windows Terminal).

**Implementation strategy:**

1. Save clipboard text format only (`CF_UNICODETEXT`) for fast save/restore
2. Set clipboard to dictated text
3. SendInput Ctrl+V (4 INPUT events: Ctrl down, V down, V up, Ctrl up)
4. Sleep 30-50ms for paste processing
5. Restore original clipboard content
6. Total overhead: ~50-80ms regardless of text length

**Edge case handling:**

- If clipboard contains non-text data (images, files), save the format type and warn user that restore is best-effort
- If clipboard is empty, skip save/restore
- If target is legacy console (not Windows Terminal), try Ctrl+Shift+V or right-click paste

### Fallback Method: SendInput (Character-by-Character)

**When to use fallback:**

- User explicitly opts out of clipboard disruption (e.g., they are actively using clipboard for other work)
- Clipboard access fails (another application has clipboard locked)
- Very short text (1-3 characters) where clipboard overhead exceeds character-by-character cost

**Implementation strategy:**

1. Use `SendInput` with `KEYEVENTF_UNICODE` flag for each character
2. This sends `wScan` field as the Unicode character, avoiding VK code mapping issues
3. Works for full Unicode range including emoji

### Architecture Decision

```
                     +-------------------+
                     | Speech-to-Text    |
                     | Engine Output     |
                     +--------+----------+
                              |
                              v
                     +--------+----------+
                     | Text Injection    |
                     | Router            |
                     +---+----------+----+
                         |          |
              (default)  |          |  (fallback)
                         v          v
              +----------+--+  +---+-----------+
              | Clipboard   |  | SendInput     |
              | + Ctrl+V    |  | Unicode Chars |
              +-------------+  +---------------+
              | 1. Save CB  |  | For each char:|
              | 2. Set text |  |   SendInput   |
              | 3. Ctrl+V   |  |   KEYEVENTF_  |
              | 4. Restore  |  |   UNICODE     |
              +-------------+  +---------------+
```

### Why Not Other Methods

| Method              | Rejection Reason                                                           |
| ------------------- | -------------------------------------------------------------------------- |
| UI Automation       | Does not work with Obsidian or terminal editors -- the two primary targets |
| PostMessage/WM_CHAR | Fundamentally broken per Microsoft's own documentation                     |
| Interception driver | Requires admin + driver install; unacceptable for a user-facing STT tool   |
| stdin piping        | Cannot inject into existing terminal sessions                              |

### Performance Estimates

| Scenario        | Clipboard+Paste | SendInput | Difference                                 |
| --------------- | --------------- | --------- | ------------------------------------------ |
| 5 characters    | ~60ms           | ~10ms     | SendInput faster (skip clipboard overhead) |
| 50 characters   | ~60ms           | ~50ms     | Roughly equal                              |
| 500 characters  | ~60ms           | ~500ms    | Clipboard 8x faster                        |
| 5000 characters | ~60ms           | ~5000ms   | Clipboard 80x faster                       |

**Crossover point:** ~30 characters. Below this, SendInput is competitive. Above this, clipboard paste is dramatically faster.

**Recommendation:** Use clipboard for all injections >= 5 characters (covers virtually all dictation output). Use SendInput only for single-character corrections or when clipboard is unavailable.

---

## Implementation Notes

### Python Dependencies

```
pywin32        # win32clipboard, win32gui, win32con
# OR
ctypes         # Built-in; direct Win32 API access without pywin32
pynput         # Optional: for global hotkey listener (no admin needed)
```

### Key Win32 API Functions

| Function               | Purpose                      | Header    |
| ---------------------- | ---------------------------- | --------- |
| `OpenClipboard`        | Lock clipboard for access    | winuser.h |
| `EmptyClipboard`       | Clear clipboard contents     | winuser.h |
| `SetClipboardData`     | Set clipboard content        | winuser.h |
| `GetClipboardData`     | Read clipboard content       | winuser.h |
| `EnumClipboardFormats` | List available formats       | winuser.h |
| `CloseClipboard`       | Release clipboard lock       | winuser.h |
| `SendInput`            | Inject keyboard/mouse events | winuser.h |
| `GetForegroundWindow`  | Get currently focused window | winuser.h |
| `AttachThreadInput`    | Share thread input state     | winuser.h |

### Terminal Paste Detection

Different terminals accept paste differently:

| Terminal          | Paste Shortcut                 | Detection Method                              |
| ----------------- | ------------------------------ | --------------------------------------------- |
| Windows Terminal  | Ctrl+V                         | Window class: `CASCADIA_HOSTING_WINDOW_CLASS` |
| Legacy cmd.exe    | Right-click or Ctrl+V (Win10+) | Window class: `ConsoleWindowClass`            |
| PowerShell ISE    | Ctrl+V                         | Window class contains `PowerShell`            |
| Git Bash / mintty | Shift+Insert                   | Window class: `mintty`                        |
| WSL terminal      | Ctrl+Shift+V                   | Varies by host terminal                       |

---

## Sources

- [SendInput function - Win32 API (Microsoft Learn)](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
- [AttachThreadInput function - Win32 API (Microsoft Learn)](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-attachthreadinput)
- [UI Automation Overview - Win32 (Microsoft Learn)](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-uiautomationoverview)
- [IValueProvider.SetValue - Win32 API (Microsoft Learn)](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationcore/nf-uiautomationcore-ivalueprovider-setvalue)
- [Add Content to a Text Box Using UI Automation (.NET)](https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/add-content-to-a-text-box-using-ui-automation)
- [You can't simulate keyboard input with PostMessage - Raymond Chen (2005)](https://devblogs.microsoft.com/oldnewthing/20050530-11/?p=35513)
- [You can't simulate keyboard input with PostMessage, revisited - Raymond Chen (2025)](https://devblogs.microsoft.com/oldnewthing/20250319-00/?p=110979)
- [Native UI Automation for Windows in Chromium (Chrome Developers)](https://developer.chrome.com/blog/windows-uia-support-update)
- [Introducing UIA support on Windows (Chrome Developers)](https://developer.chrome.com/blog/windows-uia-support)
- [Electron Accessibility Documentation](https://github.com/electron/electron/blob/main/docs/tutorial/accessibility.md)
- [Chromium Accessibility Overview](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/accessibility/overview.md)
- [Windows Pseudo Console (ConPTY) Introduction](https://devblogs.microsoft.com/commandline/windows-command-line-introducing-the-windows-pseudo-console-conpty/)
- [Interception Driver (GitHub)](https://github.com/oblitum/Interception)
- [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/en/latest/)
- [PyAutoGUI Windows Implementation Source](https://github.com/asweigart/pyautogui/blob/master/pyautogui/_pyautogui_win.py)
- [pynput Documentation](https://pynput.readthedocs.io/en/latest/keyboard.html)
- [pynput Windows Keyboard Source](https://github.com/moses-palmer/pynput/blob/master/lib/pynput/keyboard/_win32.py)
- [keyboard Library (PyPI)](https://pypi.org/project/keyboard/)
- [Python-UIAutomation-for-Windows (GitHub)](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows)
- [UIPI and SendInput - Microsoft Forum](https://learn.microsoft.com/en-us/archive/msdn-technet-forums/b68a77e7-cd00-48d0-90a6-d6a4a46a95aa)
- [UIPI Security Documentation (GitHub)](https://github.com/Chaoses-Ib/Windows/blob/main/Kernel/Security/UIPI.md)
- [Standard Clipboard Formats (Microsoft Learn)](https://learn.microsoft.com/en-us/windows/win32/dataxchg/standard-clipboard-formats)
- [Win32clipboard Python Examples (GitHub Gist)](https://gist.github.com/Erriez/8d0f9d0855708da7fd85c45e6e9a62f6)
- [Clipboard + Paste Speed Discussion (AutoHotkey Community)](https://www.autohotkey.com/boards/viewtopic.php?t=33752)
- [SendInput Instant Typing Discussion (AutoHotkey Community)](https://www.autohotkey.com/boards/viewtopic.php?t=108704)
- [Windows Terminal Keyboard Handling (GitHub Issue #4999)](https://github.com/microsoft/terminal/issues/4999)
- [WinUI3 PostMessage WM_KEYDOWN Failure (Microsoft Learn Q&A)](https://learn.microsoft.com/en-us/answers/questions/5559327/in-winui3-desktop-application-postmessage-of-wm-ke)
