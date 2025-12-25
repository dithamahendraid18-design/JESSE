# JESSE (Multi-Client Restaurant Chatbot)

## Architecture
- `clients/` : semua data per klien (config, theme, knowledge, responses, dll).
- `backend/` : Flask API (multi-client loader, routing, analytics).
- `frontend/`: Webchat UI (Vite + Vanilla JS).
- `deploy/`  : Docker Compose + Nginx (production-like).

## Run (Dev)
### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -U pip
pip install -e .
python -m jesse.main
