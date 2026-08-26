# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

六爻解卦 — A Vue 3 + Flask web application for Chinese I-Ching (六爻) divination with AI-powered interpretations via DeepSeek LLM. Ported from an iOS native app.

## Development Commands

### Frontend (in `frontend/` directory)
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Dev server on http://localhost:3000 (proxies /api to :9001)
npm run build        # Production build → outputs to ../static/
npm run preview      # Preview production build
```

### Backend (in project root)
```bash
pip install -r requirements.txt   # Install Python dependencies
python gua_app.py                 # Flask server on http://localhost:9001
```

### Full Development Setup
Run two terminals: backend (`python gua_app.py`) and frontend (`cd frontend && npm run dev`). Access via http://localhost:3000 — API calls are proxied to :9001 via Vite config.

### Production
```bash
cd frontend && npm run build    # Build frontend into static/
cd .. && python gua_app.py      # Serves SPA + API on :9001
```

No tests, linting, or formatting tools are configured.

## Architecture

### Frontend (`frontend/`)

**Tech**: Vue 3 (Composition API) + Vue Router + Vite + Axios

**State management**: No Vuex/Pinia. Uses `sessionStorage` for page-to-page divination flow data and `localStorage` for persistent data (records, auth token, language). When logged in, records sync to server via `/api/records`.

**Key sessionStorage keys**: `liuyao_date`, `liuyao_yaoValues`, `liuyao_guaXiangInfo`, `liuyao_category`, `liuyao_sessionId`, `liuyao_initialMessage`

**User flow**: Home → YaoInput (time + 6 yao values) → Hexagram (calculation result) → Category (question type) → Analysis (submit to AI) → Chat (follow-up conversation)

**Routing** (`src/router/index.js`): 13 routes across 3 tab groups (`qigua`, `records`, `settings`). All routes lazy-loaded. SPA with `createWebHistory`.

**Core calculation engine** (`src/core/`):
- `liuyao.js` — Main `Liuyao` class. Faithful port from iOS Swift. Calculates six relatives (六亲), six spirits (六神), hidden spirits (伏神), world/response (世应), void (空亡), combinations/clashes (六合/六冲). Yao encoding: 0=老阴, 1=少阳, 2=少阴, 3=老阳.
- `calendar.js` — Chinese calendar: Heavenly Stems (天干), Earthly Branches (地支), solar terms (节气), Four Pillars (八字). Reference date: 1901-01-01 = 乙卯日.
- `hexagramData.js` — Complete 64 hexagrams dataset with eight palaces (八宫).

**i18n** (`src/utils/locale.js`): Auto-detects zh-CN/zh-TW from browser. Uses `opencc-js` for Simplified↔Traditional conversion. Global `$t()` function.

**Styling** (`src/assets/styles/theme.css`): Dark Chinese aesthetic, 楷体 (Kai) font, max-width 480px mobile-first design. CSS custom properties with gold/black palette (`--color-primary: #F9D47C`, `--color-bg: #141414`).

**API client** (`src/api/index.js`): Axios with 120s timeout, JWT token injection, `X-Lang` header, 401 auto-logout, 3 retries for 5xx errors.

### Backend (project root)

**Tech**: Flask + SQLite + DeepSeek LLM (via OpenAI SDK)

**Entry point**: `gua_app.py` — Port 9001, serves SPA from `static/`, all unmatched routes fall back to `index.html`.

**Key modules**:
- `auth.py` — SQLite DB (users, usage_log, records tables), JWT auth (30-day expiry), werkzeug password hashing, `@require_auth` / `@optional_auth` decorators, credit system.
- `dialog_manager.py` — AI conversation session manager. LRU cache (max 100 sessions), 24h timeout, 50k token limit. Language-aware system prompts.
- `llm/` — Factory pattern. `llm/common/config.py` has prompt templates. `llm/deepseek/client.py` implements DeepSeek API (model: `deepseek-v4-flash` — a reasoning model whose `reasoning_tokens` count against `max_tokens`; runtime params come from `config.py`: temp 0.7, max tokens 16384).
- `config.py` — Guest quota (1 free use), registered quota (50 free uses), JWT config.
- `liuyao_utils.py` — Formats hexagram data for LLM prompt.
- `captcha_utils.py` — CAPTCHA generation/validation for registration.

**API endpoints**:
- Auth: `GET /api/captcha`, `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`
- Records (auth required): `GET/POST /api/records`, `PUT/DELETE /api/records/:id`
- Business: `POST /api/receive` (submit hexagram → AI), `POST /api/chat` (follow-up), `POST /api/chat/restore` (restore from saved record)
- Other: `POST /api/feedback`, `GET /api/config/quota`

**Environment variables** (`.env`): `DEEPSEEK_API_KEY`, `DEEPSEEK_API_BASE`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`

## Code Conventions

- Frontend uses Vue 3 `<script setup>` Composition API pattern
- No TypeScript — plain JavaScript throughout
- Chinese comments and variable naming for domain concepts
- Backend responses follow `{"status": "success", ...}` or `{"error": "message"}` pattern
- The core divination calculation engine (`src/core/`) is a precise port from iOS Swift — maintain parity when modifying
