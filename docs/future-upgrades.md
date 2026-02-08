---
title: STVC Future Upgrades
created: 08-02-2026
tags: [implementation, tooling, stt, future, upgrades]
status: backlog
---

# STVC Future Upgrades

Features researched and validated but not needed for the current implementation. These can be added later as standalone enhancements.

## Silero VAD (Hands-Free Activation)

Automatic speech detection — no hotkey needed. VAD continuously monitors the microphone and triggers transcription when speech is detected.

| Attribute      | Value                             |
| -------------- | --------------------------------- |
| **Model**      | Silero VAD                        |
| **Accuracy**   | 87.7% TPR @ 5% FPR               |
| **vs. WebRTC** | 4x fewer errors (WebRTC: 50% TPR) |
| **Latency**    | <1ms per 30ms audio chunk         |
| **Languages**  | 6000+                             |
| **License**    | MIT                               |
| **VRAM**       | ~50 MB                            |

**Configuration:**

```python
vad_config = {
    'threshold': 0.5,            # Medium sensitivity (0.3-0.4 for quiet rooms, 0.6-0.7 for noisy)
    'min_speech_duration': 0.3,  # Ignore clicks/sounds < 300ms
    'min_silence_duration': 1.0, # 1s pause = user finished speaking
    'speech_pad_ms': 300,        # 300ms padding before/after speech
}
```

**Dependencies:** `torch`, `silero-vad`

**Implementation effort:** ~80-100 lines (VAD loop, buffer management, silence threshold tuning)

**Added latency:** 1.0-1.5s (silence detection wait before transcription triggers)

> Research basis: [STT Approach Analysis](research/STT-Approach-Analysis-2026-02-07.md) §VAD Deep Dive

---

## LLM Polish

On-demand text cleanup via Claude API. User can optionally send transcription through an LLM to fix grammar, remove disfluencies, and improve clarity before injection.

**Use case:** Critical text (emails, documentation) where transcription accuracy matters more than speed.

**Trade-off:** Adds network latency (~1-2s) and API cost. Not needed for dictating to Claude Code (Claude already interprets natural language).

---

## Wake Word (Porcupine)

Trigger voice input with a spoken phrase (e.g., "Hey Claude") instead of a hotkey.

| Attribute | Value |
|-----------|-------|
| **Engine** | Porcupine (Picovoice) |
| **Accuracy** | >95% TPR, <1 false alarm/hour |
| **Custom words** | Trainable in seconds via Picovoice Console |
| **License** | Free tier + paid |

**Depends on:** VAD (wake word activates VAD pipeline)

> Research basis: [STT Approach Analysis](research/STT-Approach-Analysis-2026-02-07.md) §Wake Word Detection

---

## Multi-Microphone (Beam Forming)

Use multiple microphones for better noise rejection via beam forming. Useful in noisy environments.

**Depends on:** VAD (beam forming improves VAD accuracy in noise)

---

## Adaptive Silence Threshold

ML-based automatic adjustment of silence detection threshold based on user speech patterns. Learns when user is pausing vs. finished speaking.

**Depends on:** VAD

---

## Audio Feedback

Subtle sound effect on transcription complete to confirm text was injected.

---

## Research References

All features above are backed by research conducted on 07 February 2026:

- [STT Approach Analysis](research/STT-Approach-Analysis-2026-02-07.md) — VAD, wake word, streaming analysis
- [STT Engine Comparison](research/STT-Engine-Comparison-2026-02-07.md) — Model benchmarks
- [Existing STT Tools Survey](research/Existing-STT-Tools-Survey-2026-02-07.md) — Feature landscape
