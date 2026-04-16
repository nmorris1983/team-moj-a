# team-moj-a
AI Engineering Lab hackathon day April 2026

## Running the app

### Step 1 — Install Python dependencies (once)
```bash
cd ai_summary
uv sync
```

### Step 2 — Generate `ai_notes.json`
Requires Ollama running locally with the `qwen2.5:0.5b` model pulled.
```bash
uv run python main.py
```
This writes `data/ai_notes.json`, which the Node app reads for AI summaries.

### Step 3 — Install Node dependencies (once)
```bash
cd ..
npm install
```

### Step 4 — Start the Node prototype
```bash
npm run dev
```

> If `ai_notes.json` is missing, the app still runs but skips AI notes and logs a warning. 