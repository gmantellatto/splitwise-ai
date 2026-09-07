# SplitWise AI

A full-stack expense-splitting application powered by the Anthropic Claude API. Users can manage groups, track shared expenses, and calculate balances through a native UI — or delegate any action to an AI assistant through a conversational chat interface.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [AI Concepts](#ai-concepts)

---

## Overview

SplitWise AI was originally built as a study project for the CCDV-F certification and has since evolved into a production-ready application. It combines a traditional CRUD interface with an AI layer that understands natural language and can perform any operation the UI exposes — creating groups, logging expenses, renaming participants, calculating optimized settlements, and more.

---

## Features

- **Group management** — create, view, and delete expense groups
- **Participant management** — add, rename, and remove members
- **Expense tracking** — add, edit, and delete expenses with automatic split calculation
- **Balance calculation** — per-participant net balance view
- **Optimized settlements** — min-cash-flow algorithm to minimize the number of transfers
- **Undo** — revert the last mutating operation on any group (in-memory, up to 10 steps)
- **AI chat assistant** — conversational interface that can perform any operation via tool use, with full multi-turn memory per session
- **Streaming responses** — server-sent events (SSE) for real-time AI output
- **PWA-ready** — service worker and web manifest included

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 · FastAPI · Uvicorn |
| AI | Anthropic Claude API (claude-haiku / claude-sonnet) |
| Storage | JSON file (data/groups.json) |
| Frontend | Vanilla JS SPA · CSS custom properties |
| Data validation | Pydantic v2 |

---

## Project Structure

```
splitwise-ai/
├── data/
│   └── groups.json             # Persistent storage
├── public/
│   ├── index.html              # Single-page application shell
│   ├── app.js                  # SPA logic (routing, API client, UI)
│   ├── style.css               # Design system
│   ├── manifest.json           # PWA manifest
│   └── sw.js                   # Service worker
├── src/
│   ├── server.py               # FastAPI routes (HTTP + SSE)
│   ├── claude_client.py        # Claude API integration (streaming, tool-use loop)
│   ├── models.py               # Pydantic models
│   ├── storage/
│   │   ├── db.py               # JSON read/write layer
│   │   └── undo.py             # In-memory undo stack
│   └── tools/
│       ├── definitions.py      # Tool schemas (sent to Claude)
│       ├── groups.py           # Group & participant business logic
│       ├── expenses.py         # Expense business logic
│       ├── settlements.py      # Balance & min-cash-flow algorithm
│       └── undo.py             # desfazer_operacao tool
├── requirements.txt
└── .env.example
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- An Anthropic API key (or a compatible gateway)

### 1. Clone the repository

```bash
git clone <repository-url>
cd splitwise-ai
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Open `.env` and set the following variables:

```env
ANTHROPIC_AUTH_TOKEN=your_api_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-haiku-4-5
ANTHROPIC_DEFAULT_SONNET_MODEL=claude-sonnet-4-5
```

### 5. Run the application

```bash
python -m src.server
```

The server starts at `http://localhost:8000`. Open it in your browser.

> **Hot reload (development):** pass `--reload` to Uvicorn via the `__main__` block or run:
> ```bash
> uvicorn src.server:app --reload
> ```

---

## API Reference

### Chat (AI assistant)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a message; returns an SSE stream |

**Request body**

```json
{
  "message": "Create a group called Trip with Alice and Bob",
  "group_id": "optional-uuid",
  "session_id": "optional-uuid"
}
```

**SSE event format**

```
data: {"text": "chunk of text"}\n\n
data: [DONE]\n\n
```

### Groups

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/groups` | List all groups |
| `POST` | `/api/groups` | Create a group |
| `GET` | `/api/groups/{id}` | Get group details |
| `DELETE` | `/api/groups/{id}` | Delete a group |
| `GET` | `/api/groups/{id}/balances` | Per-participant net balances |
| `GET` | `/api/groups/{id}/optimized` | Minimum-transfer settlement plan |
| `POST` | `/api/groups/{id}/undo` | Revert the last operation |

### Participants

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/groups/{id}/participants` | Add a participant |
| `DELETE` | `/api/groups/{id}/participants/{name}` | Remove a participant |
| `PATCH` | `/api/groups/{id}/participants` | Rename a participant |

### Expenses

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/groups/{id}/expenses` | Add an expense |
| `PATCH` | `/api/groups/{id}/expenses/{exp_id}` | Edit an expense |
| `DELETE` | `/api/groups/{id}/expenses/{exp_id}` | Delete an expense |

---

## AI Concepts

- Streaming with `client.messages.stream` and SSE transport
- Tool use — schema design, dispatch loop, multi-turn cycles
- Multi-turn conversation history (session-scoped, in-memory)
- Model selection by intent (Haiku vs Sonnet)
- Error handling — `RateLimitError`, `APIError`, `max_tokens`
- Generator functions as SSE producers
