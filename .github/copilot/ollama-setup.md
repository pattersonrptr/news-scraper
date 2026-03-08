# Ollama Setup Guide — Local AI Provider

This guide helps you install and configure Ollama as the local AI provider fallback.

---

## 1. Install Ollama

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### macOS

```bash
brew install ollama
```

### Windows

Download the installer from [https://ollama.com/download](https://ollama.com/download).

---

## 2. Start the Ollama Service

```bash
ollama serve
# Ollama will listen on http://localhost:11434
```

---

## 3. Pull a Model

Recommended models for this project (choose one based on your hardware):

```bash
# Recommended: fast, good quality (requires ~5GB RAM)
ollama pull llama3.1:8b

# Lighter option (~4GB RAM)
ollama pull mistral:7b

# Smallest option (~2GB RAM, lower quality)
ollama pull phi3:mini
```

---

## 4. Verify

```bash
ollama list
# Should show your downloaded model

curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Summarize: Python is a programming language.",
  "stream": false
}'
```

---

## 5. Configure in This Project

In your `.env` file:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

Or to use Gemini as primary with Ollama as fallback:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
OLLAMA_FALLBACK=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

---

## 6. Ollama in Docker

If running the full stack via docker-compose, Ollama runs on the **host machine** (not in Docker), and the backend container accesses it via `host.docker.internal`:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

This is already the default in `docker-compose.yml` for local development.

---

## Hardware Requirements

| Model | RAM | VRAM (GPU) | Speed |
|---|---|---|---|
| phi3:mini | 2GB | 2GB | Fast |
| mistral:7b | 4GB | 4GB | Medium |
| llama3.1:8b | 5GB | 5GB | Medium |
| llama3.1:70b | 40GB | 40GB | Slow (CPU) |

GPU acceleration (NVIDIA CUDA or Apple Metal) significantly improves speed but is optional.
