# PromptCraft Pro v3

Advanced AI Prompt Studio — Flask · Python · Pydantic · Anthropic SDK

---

## What it does

Three tools in one web app, all powered by Claude:

| Module | What it does |
|---|---|
| **Prompt Generator** | Turn a plain-English goal into a structured, production-ready prompt in 7 model variants |
| **Token Optimizer** | Paste any prompt → get 3 compressed versions with full waste analysis and model tips |
| **History** | Every generated prompt is auto-saved per-session; reload and continue refining at any time |

**Generator features:**
- 11 prompt frameworks (RISEN, COAST, BROKE, ROSES, CARE, RACE, TRACE, PTCF, RTF, APE, Chain)
- 7 model variants generated simultaneously: Claude 4.6, ChatGPT, Gemini 2.5, GPT-5, DeepSeek, Grok 3, Universal
- Token-optimized version generated alongside every full prompt (40–60% smaller, 100% intent preserved)
- Iterative refinement loop — keep improving with natural-language feedback
- Model-specific cheat codes injected automatically (Claude XML tags, Gemini responseSchema, DeepSeek R1 tips, etc.)
- Quality scoring with animated ring + per-dimension bars

---

## Project structure

```
promptcraft_v3/
│
├── run.py                         Entry point
├── requirements.txt
├── .env.example                   Copy to .env and add your key
├── pytest.ini
│
├── config/
│   └── settings.py                Dev / Prod / Test configs loaded from .env
│
├── app/
│   ├── __init__.py                Flask Application Factory (create_app)
│   │
│   ├── utils/                     Shared utilities — no Flask dependency
│   │   ├── logger.py              get_logger(__name__) — used by every module
│   │   ├── errors.py              Custom exceptions with HTTP status codes
│   │   └── json_parser.py         Safe JSON extraction from LLM responses
│   │
│   ├── models/                    Pydantic — validates ALL input and output
│   │   ├── prompt_models.py       GenerateRequest, GenerateResponse, RefineRequest, RefineResponse
│   │   ├── optimizer_models.py    OptimizeRequest, OptimizeResponse
│   │   └── history_models.py      HistoryEntry, HistoryListItem, SaveHistoryRequest
│   │
│   ├── core/                      Pure Python business logic — zero Flask dependency
│   │   ├── frameworks/
│   │   │   └── registry.py        11 frameworks as frozen Python dataclasses
│   │   ├── cheatcodes/
│   │   │   └── registry.py        All model cheat codes as typed Python objects
│   │   └── engines/
│   │       ├── prompt_engine.py   Assembles system prompts from registry data
│   │       └── token_engine.py    Assembles optimizer prompts + token estimator
│   │
│   ├── services/                  Orchestration layer
│   │   ├── anthropic_client.py    Single Anthropic SDK wrapper — error mapping
│   │   ├── generator_service.py   Engine → Client → JSON parse → Pydantic validate
│   │   ├── optimizer_service.py   Engine → Client → JSON parse → Pydantic validate
│   │   └── history_service.py     Session-based history (swap to DB: change this file only)
│   │
│   └── api/routes/                Thin Flask blueprints — validate, call service, return JSON
│       ├── key_routes.py          /api/key/set | /api/key/clear | /api/key/status
│       ├── generator_routes.py    /api/generator/generate | /api/generator/refine
│       ├── optimizer_routes.py    /api/optimizer/optimize
│       └── history_routes.py      /api/history/save | list | /<id> | clear
│
├── tests/
│   ├── conftest.py                Shared fixtures
│   ├── unit/                      No Flask, no Anthropic — pure Python
│   │   ├── test_frameworks.py     Framework registry tests
│   │   ├── test_cheatcodes.py     Cheat code registry tests
│   │   ├── test_json_parser.py    JSON extraction edge cases
│   │   └── test_prompt_engine.py  Prompt building — all frameworks
│   └── integration/               Flask test client, Anthropic is mocked
│       └── test_routes.py         All routes — happy path + validation + errors
│
├── static/
│   ├── css/main.css               Full design system
│   └── js/
│       ├── api.js                 All HTTP calls to Flask in one place
│       ├── ui.js                  Shared helpers + KEY manager + APP switcher
│       ├── generator.js           Generator module logic
│       └── optimizer.js           Optimizer + History module logic
│
└── templates/
    └── index.html                 Single-page app — 3 modules in one template
```

---

## Setup

### Option A — Conda (recommended, Windows Anaconda Prompt)

**One-time setup:**

```bat
REM Open Anaconda Prompt / Conda Prompt, cd into the project folder
cd promptcraft_v3

REM Run the setup script (creates env, copies .env, verifies packages)
setup.bat
```

Or do it manually step by step:

```bat
REM 1. Create the conda environment from environment.yml
conda env create -f environment.yml

REM 2. Activate it
conda activate promptcraft

REM 3. Copy config
copy .env.example .env
REM  → Open .env and set ANTHROPIC_API_KEY=sk-ant-...

REM 4. Run
python run.py
```

**Every time after that:**

```bat
REM Option 1 — use the script
run.bat

REM Option 2 — manually
conda activate promptcraft
python run.py
```

Open [http://localhost:5000](http://localhost:5000)

---

### Option B — pip + venv (any OS)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # then add ANTHROPIC_API_KEY
python run.py
```

---

### Get your Anthropic API key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up / log in
3. Create an API key
4. Paste it into `.env` as `ANTHROPIC_API_KEY=sk-ant-...`

The key is stored only in the Flask server-side session — never in the browser.

---

## Running tests

```bash
# All tests
pytest

# Unit tests only (no API key needed — pure Python)
pytest tests/unit/ -v

# Integration tests only (Anthropic is mocked — no API key needed)
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_frameworks.py -v

# With coverage
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

**All tests run without an Anthropic API key.** Unit tests have zero external dependencies. Integration tests mock `AnthropicClient.complete()`.

---

## API reference

### Key management

| Method | Endpoint | Body | Response |
|---|---|---|---|
| `POST` | `/api/key/set` | `{"key": "sk-ant-..."}` | `{"ok": true, "masked": "sk-ant-api0••••123"}` |
| `POST` | `/api/key/clear` | — | `{"ok": true}` |
| `GET` | `/api/key/status` | — | `{"set": true, "masked": "..."}` |

### Prompt Generator

| Method | Endpoint | Body |
|---|---|---|
| `POST` | `/api/generator/generate` | See `GenerateRequest` |
| `POST` | `/api/generator/refine` | See `RefineRequest` |

**GenerateRequest fields:**

```json
{
  "goal":          "string (required, 10–4000 chars)",
  "model":         "claude | chatgpt | gpt5 | gemini | deepseek | grok | universal",
  "category":      "auto | writing | coding | analysis | creative | business | ...",
  "output_format": "auto | structured | markdown | json | plain | steps | table",
  "complexity":    "auto | simple | moderate | advanced | expert",
  "tones":         ["professional", "technical", "..."],
  "framework":     "RISEN | COAST | BROKE | ROSES | CARE | RACE | TRACE | PTCF | RTF | APE | chain",
  "techniques":    ["cot", "fewshot", "role", "cod", "selfcheck", "xml", ...],
  "cheat_codes":   ["claude_xml", "claude_effort", "claude_cache", "token_budget", ...]
}
```

**RefineRequest fields:**

```json
{
  "current_prompt": "string (required, existing prompt text)",
  "feedback":       "string (required, what to improve)"
}
```

### Token Optimizer

| Method | Endpoint | Body |
|---|---|---|
| `POST` | `/api/optimizer/optimize` | See `OptimizeRequest` |

**OptimizeRequest fields:**

```json
{
  "prompt":       "string (required, 10–8000 chars)",
  "target_model": "universal | claude | chatgpt | gpt5 | gemini | deepseek | grok",
  "level":        "balanced | aggressive | ultra",
  "sensitivity":  "general | creative | technical | legal",
  "techniques":   ["semantic", "structure", "cod", "filler", "negative", "primacy", ...]
}
```

### History

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/history/save` | Save a prompt entry |
| `GET` | `/api/history/list` | List all entries (lightweight, no full_data) |
| `GET` | `/api/history/<id>` | Get full entry by id |
| `POST` | `/api/history/clear` | Delete all history for this session |

---

## Architecture decisions

### Why Application Factory (`create_app`)?
Each call to `create_app()` returns a fresh Flask app. Tests get their own isolated instance with `TestingConfig`. No global state.

### Why a `core/` layer?
`app/core/` has **zero Flask imports**. Frameworks and cheat codes are Python dataclasses in a registry. This means:
- The entire prompt-building logic is testable without starting Flask
- Frameworks/cheat codes can be updated in one file and reflected everywhere
- Easy to add new models or frameworks without touching routes

### Why Pydantic models?
Every request is validated before it reaches a service. Bad input raises a `ValidationError` that the route converts to a clean `400` response. No silent failures from missing or wrong-typed fields.

### Why a Services layer?
Routes never call `anthropic` directly. The flow is always:  
`Route → Pydantic validation → Service → Engine (build prompt) → AnthropicClient → JSON parse → Pydantic response`

This means swapping Claude for another model means changing only `AnthropicClient`.

### Why custom exceptions?
`APIKeyMissingError`, `AnthropicTimeoutError`, etc. each carry an `http_status`. Routes catch `PromptCraftError` and return the right HTTP code automatically. No if/else chains in routes.

### Why session-based history?
Simple and zero-config. To upgrade to a real database, replace `HistoryService` only — routes don't change.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)* | Your Anthropic API key |
| `FLASK_SECRET_KEY` | `dev-secret-...` | Flask session signing key — change in production |
| `FLASK_ENV` | `production` | `development` / `production` / `testing` |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode |
| `MAX_HISTORY` | `30` | Max saved prompts per session |
| `SESSION_LIFETIME_HOURS` | `8` | How long sessions last |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

---

## Quick start (Windows Conda Prompt)

```bat
cd promptcraft_v3
setup.bat
REM → adds your key to .env when prompted
run.bat
REM → opens http://localhost:5000
```

```bat
REM Run tests (no API key needed)
conda activate promptcraft
pytest
```
