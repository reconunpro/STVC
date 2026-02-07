---
title: STT Engine Comparison 2026
created: 07-02-2026
tags: [research, stt, whisper, engines, comparison]
---

# STT Engine Comparison 2026

**Research Date:** 07 February 2026

## Coverage Key
<span style="color:#3498db">Global</span> | <span style="color:#2ecc71">Open Source</span> | <span style="color:#e67e22">Commercial-Friendly</span>

## Executive Summary

- **Best overall accuracy**: NVIDIA Parakeet-TDT 0.6B v2/v3 leads the Hugging Face Open ASR Leaderboard with 6.05% WER, followed by NVIDIA Canary-Qwen 2.5B at 5.63% WER.
- **Best speed-to-accuracy ratio for local GPU use**: faster-whisper with large-v3-turbo model on an RTX 4070 delivers near-real-time transcription (~200x+ RTF) with strong accuracy (~7-8% WER).
- **Best for vibe coding (recommended)**: faster-whisper (large-v3-turbo) with Silero VAD provides the ideal combination of low latency, high accuracy on natural speech, mature Python API, native CUDA support, and streaming capability.
- **Best ultra-low-latency edge option**: Moonshine Tiny (27M params) processes 10s of audio with 5x less compute than Whisper Tiny, ideal for voice commands but weaker on long-form dictation.
- **Best pure accuracy (if latency is acceptable)**: NVIDIA Canary-Qwen 2.5B achieves state-of-the-art WER but requires NeMo framework (poor native Windows support).
- **Avoid for this use case**: Vosk (outdated accuracy), vanilla whisper.cpp (CUDA issues on Windows).

---

## Engine-by-Engine Analysis

### 1. faster-whisper (CTranslate2-based) <span style="color:#2ecc71">RECOMMENDED</span>

**Overview:** A reimplementation of OpenAI's Whisper using [CTranslate2](https://github.com/OpenNLP/CTranslate2), an optimized inference engine for Transformer models. Up to 4x faster than vanilla OpenAI Whisper with the same accuracy and lower memory usage.

| Attribute | Details |
|-----------|---------|
| **Latency (RTX 4070)** | ~0.3-0.5s for 10s audio with large-v3-turbo; ~200-300x real-time factor. A 4070 Laptop GPU transcribed 4+ min audio in <1s. |
| **Accuracy / WER** | large-v3: ~6.4% WER (LibriSpeech); large-v3-turbo: ~7-8% WER; competitive with best-in-class models. |
| **GPU Support** | Native CUDA support via CTranslate2. FP16 and INT8 quantization on GPU. Excellent RTX 4070 compatibility. |
| **Python API** | `pip install faster-whisper`. Clean, well-documented API. `WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")`. |
| **Model Sizes** | tiny: 39M (75MB), base: 74M (142MB), small: 244M (466MB), medium: 769M (1.5GB), large-v3: 1.55B (3GB), large-v3-turbo: 809M (1.6GB). |
| **Streaming** | Not natively streaming, but ecosystem solutions exist: whisper-live, whisper_streaming, SimulStreaming. Integrates well with Silero VAD for real-time chunked transcription. |
| **License** | MIT License (code and model weights). |
| **Maintenance** | Actively maintained by SYSTRAN. 14k+ GitHub stars. Regular releases through 2025. |
| **Vibe Coding Fit** | <span style="color:#2ecc71;font-weight:bold">Excellent.</span> Fast GPU inference, accurate on natural speech, mature ecosystem, easy Python integration. |

**Links:** [GitHub](https://github.com/SYSTRAN/faster-whisper) | [PyPI](https://pypi.org/project/faster-whisper/) | [HuggingFace Models](https://huggingface.co/Systran/faster-whisper-large-v3)

---

### 2. Whisper.cpp (C++ Port)

**Overview:** A C/C++ port of OpenAI's Whisper using the ggml tensor library. Primarily optimized for CPU inference with experimental GPU support. Maintained by ggml-org.

| Attribute | Details |
|-----------|---------|
| **Latency (RTX 4070)** | CPU-primary: ~2-5s for 10s audio with large-v3 on modern CPU. CUDA acceleration available but inconsistent on Windows. |
| **Accuracy / WER** | Identical to OpenAI Whisper models (same weights). ~6.4% WER with large-v3. |
| **GPU Support** | CUDA via cuBLAS (`-DGGML_CUDA=1`), but **known issues on Windows** in 2025: CUBLAS=0 detection failures, resource allocation errors. GPU mode is less mature than CPU mode. |
| **Python API** | `pywhispercpp` (v1.4.1, Dec 2025). Windows wheels for Python 3.10-3.14. CUDA support requires manual build with `GGML_CUDA=1`. |
| **Model Sizes** | Same as Whisper: tiny through large-v3. GGML quantized formats available (Q4, Q5, Q8) reducing size by 2-4x. |
| **Streaming** | Native streaming support via whisper.cpp server mode. Real-time transcription built-in. |
| **License** | MIT License. |
| **Maintenance** | Very actively maintained (ggml-org). 37k+ GitHub stars. Frequent releases. |
| **Vibe Coding Fit** | <span style="color:#f1c40f;font-weight:bold">Mixed.</span> Great on CPU/Mac, but CUDA support on Windows is unreliable. If you do not need GPU, it is an option for CPU-only use. |

**Links:** [GitHub](https://github.com/ggml-org/whisper.cpp) | [pywhispercpp](https://github.com/absadiki/pywhispercpp)

---

### 3. Distil-Whisper (Distilled Models)

**Overview:** Knowledge-distilled variants of Whisper large-v3, created by Hugging Face. 6x faster inference, 50% fewer parameters, within 1% WER of the teacher model.

| Attribute | Details |
|-----------|---------|
| **Latency (RTX 4070)** | ~6x faster than Whisper large-v3. Estimated ~0.2-0.4s for 10s audio on RTX 4070 with GPU acceleration. |
| **Accuracy / WER** | distil-large-v3: within 1% WER of large-v3 (~7.2% WER). Edge benchmark: 14.93% WER (with noise). Strong noise handling at 21.26% WER (only +6.33% degradation). |
| **GPU Support** | Full CUDA support via Hugging Face Transformers or CTranslate2 (faster-whisper compatible). |
| **Python API** | `pip install transformers` or use through faster-whisper with CTranslate2-converted models. Native HF pipeline integration. |
| **Model Sizes** | distil-large-v3: 756M parameters (~1.5GB). distil-large-v2: 756M parameters. distil-medium.en: 394M (~800MB). distil-small.en: 166M (~330MB). |
| **Streaming** | Same streaming ecosystem as faster-whisper (chunked with VAD). Hugging Face Transformers supports chunked long-form decoding. |
| **License** | MIT License. |
| **Maintenance** | Maintained by Hugging Face. Active development. |
| **Vibe Coding Fit** | <span style="color:#2ecc71;font-weight:bold">Very Good.</span> Best balance of speed and accuracy when run through faster-whisper. Slightly less accurate than full large-v3 but significantly faster. |

**Links:** [GitHub](https://github.com/huggingface/distil-whisper) | [HuggingFace](https://huggingface.co/distil-whisper/distil-large-v3)

---

### 4. Moonshine (UsefulSensors / moonshine-ai)

**Overview:** A family of ultra-efficient ASR models designed for edge devices and real-time voice commands. Uses RoPE (Rotary Position Embedding) and is trained on variable-length speech segments. Currently the default engine in [claude-stt](https://github.com/jarrodwatts/claude-stt).

| Attribute | Details |
|-----------|---------|
| **Latency (RTX 4070)** | Extremely fast: 5x reduction in compute vs Whisper Tiny for 10s audio. Sub-100ms inference for short utterances on CPU. GPU acceleration available via ONNX Runtime CUDA. |
| **Accuracy / WER** | Tiny (27M): 48% lower error than Whisper Tiny; matches/outperforms Whisper Medium (28x larger). Base (62M): strong but limited to 8 languages. English-focused accuracy is good for short utterances but less proven on long-form dictation. |
| **GPU Support** | Via ONNX Runtime with CUDA EP. Not as deeply optimized for GPU as faster-whisper's CTranslate2. |
| **Python API** | `pip install moonshine-onnx` for ONNX inference. Also available via Hugging Face Transformers. Simple API: `moonshine_onnx.transcribe(audio, 'moonshine/tiny')`. |
| **Model Sizes** | Tiny: 27M params (~190MB). Base: 62M params (~400MB). Extremely compact. |
| **Streaming** | Designed for streaming/live transcription. Real-time voice command support is a core design goal. |
| **License** | MIT License. |
| **Maintenance** | Active development by moonshine-ai. Multilingual expansion in 2025 (Arabic, Chinese, Japanese, Korean, Ukrainian, Vietnamese). |
| **Vibe Coding Fit** | <span style="color:#f1c40f;font-weight:bold">Good for voice commands, weaker for dictation.</span> Excellent latency but limited vocabulary depth for long-form natural language dictation compared to larger models. Best for short commands rather than extended prose. |

**Links:** [GitHub](https://github.com/moonshine-ai/moonshine) | [Paper](https://arxiv.org/abs/2410.15608) | [HuggingFace](https://huggingface.co/UsefulSensors/moonshine)

---

### 5. Vosk (alphacep)

**Overview:** Lightweight offline speech recognition toolkit based on Kaldi. Designed for embedded and edge deployment with minimal resource requirements.

| Attribute | Details |
|-----------|---------|
| **Latency (RTX 4070)** | CPU-only inference. Fast on CPU but cannot leverage GPU. Typical latency ~1-3s for 10s audio depending on model size. |
| **Accuracy / WER** | 10-15% WER on English. Significantly worse than Whisper-family models. Performs poorly with background noise. Custom models can improve domain-specific accuracy. |
| **GPU Support** | <span style="color:#ff6b6b;font-weight:bold">None.</span> CPU-only for inference. GPU only needed for training custom models. |
| **Python API** | `pip install vosk`. Mature API supporting Python, Java, C#, Node.js. Streaming API with real-time recognition. |
| **Model Sizes** | Portable: ~50MB per language. High-accuracy English: ~1.4GB (vosk-model-en-us-0.22). Very compact for resource-constrained environments. |
| **Streaming** | Native streaming API with zero-latency response. One of its strongest features. |
| **License** | Apache 2.0 License. |
| **Maintenance** | Stable but lower development velocity compared to Whisper ecosystem. Community-driven. |
| **Vibe Coding Fit** | <span style="color:#ff6b6b;font-weight:bold">Poor.</span> WER of 10-15% is unacceptable for vibe coding where transcription accuracy directly impacts code quality. No GPU acceleration wastes the RTX 4070. |

**Links:** [Website](https://alphacephei.com/vosk/) | [GitHub](https://github.com/alphacep/vosk-api) | [Models](https://alphacephei.com/vosk/models)

---

### 6. SenseVoice (Alibaba / FunAudioLLM)

**Overview:** A speech foundation model from Alibaba's Tongyi Speech team supporting ASR, language identification, emotion recognition, and audio event detection. Trained on 400k+ hours of data across 50+ languages.

| Attribute | Details |
|-----------|---------|
| **Latency (RTX 4070)** | Exceptional: ~70ms for 10s audio (non-autoregressive). 5x faster than Whisper-Small, 15x faster than Whisper-Large. |
| **Accuracy / WER** | Consistently outperforms Whisper on multilingual benchmarks (AISHELL-1, AISHELL-2, WenetSpeech, LibriSpeech). Especially strong on under-resourced languages. English performance comparable to Whisper large-v3. |
| **GPU Support** | Full CUDA support via FunASR (`device="cuda:0"`). PyTorch-based inference. |
| **Python API** | Via FunASR: `pip install funasr`. `AutoModel(model="iic/SenseVoiceSmall", device="cuda:0")`. Also available via sherpa-onnx for lightweight deployment. |
| **Model Sizes** | SenseVoice-Small: ~234M params (comparable to Whisper-Small, ~470MB). SenseVoice-Large: larger encoder-decoder model (not publicly released as of early 2026). |
| **Streaming** | Pseudo-streaming via chunked inference with truncated attention. Not true native streaming. Accuracy degrades in streaming mode. |
| **License** | FunASR code: MIT License. Model weights: custom model license (check [MODEL_LICENSE](https://github.com/modelscope/FunASR/blob/main/MODEL_LICENSE)). Commercial use may require review. |
| **Maintenance** | Actively developed by Alibaba. FunASR-Nano released in late 2025 with 31-language support. |
| **Vibe Coding Fit** | <span style="color:#f1c40f;font-weight:bold">Promising but caveats.</span> Extremely fast inference and good accuracy. However, streaming is pseudo-streaming, the licensing is less clear than MIT, and the ecosystem is more oriented toward Chinese/multilingual use cases. English-only vibe coding has better options. |

**Links:** [GitHub](https://github.com/FunAudioLLM/SenseVoice) | [HuggingFace](https://huggingface.co/FunAudioLLM/SenseVoiceSmall) | [FunASR](https://github.com/modelscope/FunASR)

---

### 7. NVIDIA Parakeet / Canary (NeMo)

**Overview:** NVIDIA's state-of-the-art ASR models built on the NeMo framework. Parakeet uses FastConformer + TDT decoder for English; Canary adds multilingual + translation via LLM decoder.

| Attribute | Details |
|-----------|---------|
| **Latency (RTX 4070)** | Parakeet-TDT 0.6B: RTFx ~3380 (batch), meaning it can transcribe 1 hour of audio in ~1 second on high-end GPU. On RTX 4070, expect ~50-100x real-time. Canary-Qwen 2.5B: RTFx ~418 (slower due to LLM decoder). |
| **Accuracy / WER** | Parakeet-TDT 0.6B v2: **6.05% WER** (#1 on HF Open ASR Leaderboard). Canary-Qwen 2.5B: **5.63% WER** (best overall). Canary-1B v2: strong multilingual. |
| **GPU Support** | Native CUDA via NeMo/PyTorch. Optimized for NVIDIA GPUs. Also available via ONNX for broader deployment (onnx-asr package). |
| **Python API** | Via NeMo: `pip install nemo_toolkit[asr]`. Also available via `onnx-asr` package for simpler deployment. HuggingFace integration available. |
| **Model Sizes** | Parakeet-TDT 0.6B: 600M params (~1.2GB). Parakeet-CTC 1.1B: 1.1B params (~2.2GB). Canary-1B: 1B params (~2GB). Canary-Qwen 2.5B: 2.5B params (~5GB). |
| **Streaming** | Parakeet supports streaming via NeMo streaming inference scripts (`speech_to_text_streaming_infer_rnnt.py`). Canary-Qwen does NOT support streaming (LLM decoder). |
| **License** | Parakeet: CC-BY-4.0 (commercial-friendly). Canary models: check specific model cards. NeMo framework: Apache 2.0. |
| **Maintenance** | Very actively developed by NVIDIA. Regular model releases. Strong corporate backing. |
| **Vibe Coding Fit** | <span style="color:#f1c40f;font-weight:bold">Best accuracy, but friction on Windows.</span> NeMo does NOT natively support Windows (requires WSL2 or Docker). The onnx-asr package is a lighter alternative that works on Windows. If you can tolerate WSL2, Parakeet is the accuracy king. |

**Windows Workaround:** Use `pip install onnx-asr` which wraps Parakeet/Canary models in ONNX format and works on Windows, Linux, and macOS.

**Links:** [Parakeet v2](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2) | [Parakeet v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) | [Canary-Qwen](https://huggingface.co/nvidia/canary-1b-v2) | [NeMo](https://github.com/NVIDIA-NeMo/NeMo) | [NVIDIA Blog](https://developer.nvidia.com/blog/nvidia-speech-ai-models-deliver-industry-leading-accuracy-and-performance/)

---

### 8. Other Notable Engines (2025-2026)

#### WhisperX
Whisper with word-level timestamps, forced alignment, and speaker diarization. Uses faster-whisper as backend. Good for meeting transcription but adds overhead not needed for vibe coding.
**Link:** [GitHub](https://github.com/m-bain/whisperX)

#### Granite-Speech-3.3 (IBM)
Strong contender on Open ASR Leaderboard. Low insertion errors. Enterprise-focused.
**Link:** [HuggingFace](https://huggingface.co/ibm-granite)

#### Groq Whisper API (Cloud)
Cloud-based Whisper running on Groq LPU hardware: 164-299x real-time. If you are open to cloud APIs, Groq offers the fastest Whisper inference available (~3.7s for 10 min audio). Not local, but worth noting.
**Link:** [Groq Docs](https://console.groq.com/docs/speech-to-text)

#### ElevenLabs Scribe v1 (Cloud)
Tops the long-form leaderboard at 4.33% WER. Cloud-only, commercial API.
**Link:** [ElevenLabs](https://elevenlabs.io)

#### SimulStreaming (2025)
Successor to whisper_streaming. Much faster and higher quality real-time streaming, with optional LLM translation cascade. Emerging project.
**Link:** Referenced in [whisper_streaming](https://github.com/ufal/whisper_streaming)

---

## Master Comparison Table

| Engine | WER (English) | Latency (10s audio, RTX 4070) | GPU (CUDA) | Streaming | Python API | Model Size (Best) | License | Windows | Maintenance |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **faster-whisper (large-v3-turbo)** | ~7-8% | ~0.3-0.5s | Native | Via ecosystem | Excellent | 809M / 1.6GB | MIT | Native | Active (14k stars) |
| **faster-whisper (large-v3)** | ~6.4% | ~0.5-1.0s | Native | Via ecosystem | Excellent | 1.55B / 3GB | MIT | Native | Active |
| **whisper.cpp** | ~6.4% | ~2-5s (CPU) | Experimental | Native | pywhispercpp | 1.55B / 3GB (GGML) | MIT | Problematic CUDA | Active (37k stars) |
| **Distil-Whisper (large-v3)** | ~7.2% | ~0.2-0.4s | Via HF/CT2 | Via ecosystem | Good | 756M / 1.5GB | MIT | Native | Active |
| **Moonshine Tiny** | ~12-15% | <100ms | ONNX CUDA | Native | Simple | 27M / 190MB | MIT | Native | Active |
| **Moonshine Base** | ~10-12% | ~100-200ms | ONNX CUDA | Native | Simple | 62M / 400MB | MIT | Native | Active |
| **Vosk (large)** | 10-15% | ~1-3s (CPU) | None | Native | Mature | 50MB-1.4GB | Apache 2.0 | Native | Stable |
| **SenseVoice-Small** | ~7-8% | ~70ms | Native | Pseudo | FunASR | ~234M / 470MB | Custom+MIT | Native | Active |
| **Parakeet-TDT 0.6B v2** | **6.05%** | ~0.1-0.2s | Native | Via NeMo | NeMo/ONNX | 600M / 1.2GB | CC-BY-4.0 | WSL2/ONNX | Very Active |
| **Canary-Qwen 2.5B** | **5.63%** | ~0.5-1.0s | Native | No | NeMo | 2.5B / 5GB | Check card | WSL2/ONNX | Very Active |

### Scoring Matrix (1-5 scale, 5 = best) for Vibe Coding Use Case

| Engine | Accuracy | Latency | GPU Util. | Streaming | Python API | Win Support | Overall |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **faster-whisper (turbo)** | 4 | 5 | 5 | 4 | 5 | 5 | **4.7** |
| **Distil-Whisper** | 4 | 5 | 5 | 4 | 4 | 5 | **4.5** |
| **Parakeet-TDT (ONNX)** | 5 | 5 | 5 | 3 | 3 | 3 | **4.0** |
| **SenseVoice-Small** | 4 | 5 | 5 | 2 | 3 | 4 | **3.8** |
| **Moonshine Base** | 3 | 5 | 3 | 5 | 4 | 5 | **3.7** |
| **whisper.cpp** | 4 | 3 | 2 | 5 | 3 | 2 | **3.2** |
| **Canary-Qwen** | 5 | 4 | 5 | 1 | 3 | 2 | **3.3** |
| **Vosk** | 2 | 3 | 1 | 5 | 4 | 5 | **2.8** |

---

## Recommendation for Vibe Coding with RTX 4070

### Primary Recommendation: faster-whisper with large-v3-turbo

**Why:**
1. **Accuracy**: ~7-8% WER is more than sufficient for natural language dictation. Misrecognitions are rare enough that correction is fast.
2. **Latency**: Sub-500ms transcription for typical dictation segments on RTX 4070. This feels instantaneous.
3. **GPU utilization**: Native CTranslate2 CUDA with FP16/INT8 quantization fully leverages the RTX 4070's 12GB VRAM and Tensor Cores.
4. **Python ecosystem**: `pip install faster-whisper` just works. Clean API, well-documented, widely used.
5. **Streaming**: Combine with Silero VAD for real-time chunked transcription. Projects like whisper-live and SimulStreaming provide turnkey solutions.
6. **Windows native**: No WSL2 or Docker required. Pure Python + CUDA.
7. **License**: MIT - no restrictions.
8. **Community**: 14k+ stars, active development, large ecosystem of tools built on top.

**Setup for vibe coding:**
```python
from faster_whisper import WhisperModel

model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
segments, info = model.transcribe("audio.wav", beam_size=5, vad_filter=True)
for segment in segments:
    print(segment.text)
```

### Secondary Recommendation: Distil-Whisper large-v3 (via faster-whisper)

If you want slightly faster inference at the cost of ~1% WER, use the distilled model through the faster-whisper pipeline. Same ecosystem, same API, just a different model checkpoint.

### Future Watch: NVIDIA Parakeet via onnx-asr

If the `onnx-asr` package matures on Windows, Parakeet-TDT 0.6B v2/v3 could become the best option due to its industry-leading 6.05% WER and extreme speed. Monitor this for potential upgrade.

### Why Not Moonshine (current claude-stt default)?

Moonshine is optimized for edge/embedded devices where compute is limited. On a desktop with an RTX 4070, you have abundant GPU compute that Moonshine cannot fully exploit. Its ONNX-based GPU path is less optimized than CTranslate2's CUDA path. More importantly, Moonshine's 27-62M parameter models have a narrower vocabulary and less robustness on long-form natural language dictation compared to the 800M+ parameter Whisper models. For short voice commands, Moonshine is excellent. For dictating paragraphs of natural language to Claude Code, faster-whisper with a larger model produces meaningfully better results.

---

## Architecture Recommendation for the STVC Tool

For a Windows desktop STT tool targeting vibe coding with Claude Code:

```
[Microphone] -> [Silero VAD] -> [Audio Chunks] -> [faster-whisper large-v3-turbo (CUDA FP16)] -> [Text Output]
```

**Key design decisions:**
1. **VAD-first**: Use Silero VAD to detect speech boundaries. Only send speech segments to the model. This eliminates wasted GPU cycles on silence and provides natural sentence boundaries.
2. **Chunked processing**: Process in ~5-10 second chunks for low perceived latency. VAD handles the segmentation.
3. **GPU inference**: Pin the model to GPU with FP16 for fastest inference. The RTX 4070's 12GB VRAM easily holds the large-v3-turbo model (~1.6GB).
4. **Warm model**: Keep the model loaded in GPU memory between transcriptions. Cold-start adds ~2-3s; warm inference is sub-500ms.
5. **Fallback**: Consider Moonshine Tiny as a fallback for ultra-fast voice commands (e.g., "stop", "cancel", "undo") where latency matters more than vocabulary.

---

## Sources

- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper) - CTranslate2-based Whisper reimplementation
- [whisper.cpp GitHub](https://github.com/ggml-org/whisper.cpp) - C++ port of Whisper
- [Distil-Whisper GitHub](https://github.com/huggingface/distil-whisper) - Distilled Whisper models by Hugging Face
- [Moonshine GitHub](https://github.com/moonshine-ai/moonshine) - Edge-optimized ASR models
- [Moonshine Paper](https://arxiv.org/abs/2410.15608) - Moonshine: Speech Recognition for Live Transcription
- [Vosk Website](https://alphacephei.com/vosk/) - Offline speech recognition toolkit
- [SenseVoice GitHub](https://github.com/FunAudioLLM/SenseVoice) - Alibaba's multilingual voice understanding
- [NVIDIA Parakeet v2](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2) - #1 on HF Open ASR Leaderboard
- [NVIDIA Parakeet v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) - Multilingual extension
- [NVIDIA Canary-Qwen](https://huggingface.co/nvidia/canary-1b-v2) - Best overall WER
- [NVIDIA Speech AI Blog](https://developer.nvidia.com/blog/nvidia-speech-ai-models-deliver-industry-leading-accuracy-and-performance/) - Benchmark details
- [NeMo Framework](https://github.com/NVIDIA-NeMo/NeMo) - NVIDIA's speech AI framework
- [Northflank 2026 STT Benchmark](https://northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2026-benchmarks) - Comprehensive model comparison
- [ionio.ai 2025 Edge Benchmark](https://www.ionio.ai/blog/2025-edge-speech-to-text-model-benchmark-whisper-vs-competitors) - Edge model comparison
- [Modal Open Source STT 2025](https://modal.com/blog/open-source-stt) - Top open source STT models
- [HF Open ASR Leaderboard](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard) - Live model rankings
- [Tom's Hardware GPU Benchmark](https://www.tomshardware.com/news/whisper-audio-transcription-gpus-benchmarked) - GPU transcription performance
- [claude-stt GitHub](https://github.com/jarrodwatts/claude-stt) - Speech-to-text for Claude Code (uses Moonshine)
- [Groq Whisper Docs](https://console.groq.com/docs/speech-to-text) - Cloud Whisper API
- [Whisper Large v3 Turbo](https://huggingface.co/openai/whisper-large-v3-turbo) - OpenAI's pruned fast model
- [onnx-asr PyPI](https://pypi.org/project/onnx-asr/) - ONNX-based ASR wrapper (Parakeet/Canary on Windows)
- [pywhispercpp PyPI](https://pypi.org/project/pywhispercpp/) - Python bindings for whisper.cpp
