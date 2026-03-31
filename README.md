# AI Project Tracker (Self-Hosted LLM) 🧠

Task management system powered by a self-hosted LLM.

This project combines a Telegram bot, web dashboard, and FastAPI backend to generate project roadmaps and track progress.  
Runs entirely offline using a local LLM (Qwen 2.5 via llama.cpp) — no external APIs required.

---

## 🚀 Overview

- Generates structured project roadmaps from user input using LLM  
- Supports both Telegram bot and web interface  
- Runs fully offline (self-hosted AI, no OpenAI dependency)  
- Built with async backend and containerized architecture  
- Designed for privacy, control, and low-latency inference  

---

## 🏗 Architecture

```mermaid
graph TD
    User((User))
    TG[Telegram Bot]
    Web[Web Dashboard]
    API[FastAPI Backend]
    DB[(PostgreSQL)]
    Redis[(Redis Cache)]
    LLM[Local LLM Service]

    User --> TG
    User --> Web
    TG --> API
    Web --> API
    API --> DB
    API --> Redis
    API -->|Prompt| LLM
    LLM -->|Stream| API
````

---

## 🚀 Key Features

### Self-Hosted AI

Runs quantized LLM models (GGUF) locally via llama.cpp
No OpenAI API keys required

### Task Generation

Transforms user ideas into 5–7 structured technical tasks

### Multi-Platform Access

* Telegram Bot (Aiogram 3)
* Web Dashboard (Next.js)

### Real-Time Feedback

Streaming responses and progress updates

---

## 🛠 Tech Stack

**Backend**

* FastAPI
* SQLAlchemy (async)
* Pydantic

**Frontend**

* Next.js 14
* TypeScript
* Tailwind CSS

**AI**

* llama.cpp (OpenAI-compatible API)
* Qwen 2.5 (GGUF models)

**Infrastructure**

* Docker / Docker Compose
* Redis
* PostgreSQL
* Caddy

---

## ⚡ Quick Start

### Clone and configure

```bash
git clone https://github.com/vlimkv/ai-project-tracker.git
cp .env.example .env
```

### Run system

```bash
# Downloads model (~2GB on first run)
docker compose up -d --build
```

---

## 🌐 Access

* Web UI: [http://localhost:3000](http://localhost:3000)
* API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
* LLM Endpoint: [http://localhost:8080/v1](http://localhost:8080/v1)

---

## ⚙️ Environment

* AI_PROVIDER — oss (local) or openai
* OSS_MODEL — qwen2.5-3b-instruct
* REDIS_URL — caching and state

---

## ⚠️ Requirements

* Docker
* 4GB RAM minimum (8GB recommended)
* GPU optional

---

## 💡 Why this project

Built to explore real-world LLM integration without external APIs.

Focus:

* self-hosted AI
* async backend
* full-stack system design

---

## 📌 Notes

This project demonstrates:

* local LLM deployment
* AI + backend integration
* full-stack architecture (bot + web + backend)
* containerized development workflow
