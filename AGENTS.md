# AGENTS.md

## Cursor Cloud specific instructions

SafeShop is a Python FastAPI backend (rule-based food ingredient/nutrition scoring)
plus a Chrome browser extension. The backend is the main runnable, testable surface.

Python deps are installed into a virtualenv at `.venv` (Python 3.12). Always invoke
tools through it, e.g. `.venv/bin/pytest`, `.venv/bin/uvicorn`.

### Run / test / lint
- Run API (dev): `.venv/bin/uvicorn backend.main:app --reload` — serves on `http://127.0.0.1:8000`.
  Core endpoint is `POST /analyze` (see `README.md` for the request/response shape).
- Tests: `.venv/bin/pytest` (unit tests for nutrition parsing, scoring, ingredient cleaning).
- There is no linter configured for this repo.
- The browser extension (`extension/`) is loaded unpacked in Chrome and calls the local
  backend at `http://127.0.0.1:8000/analyze`; it needs a supported product page to render.

### Optional OCR/ML dependencies (heavy, not in the startup update script)
`requirements.txt` lists optional OCR/ML deps (`torch`, `easyocr`, `opencv-python`). These
are large and finicky, so they are intentionally excluded from the automatic update script
(only the core API/test deps are refreshed on startup). They are pre-installed in the VM
snapshot. If you ever need to (re)install them, avoid the defaults in `requirements.txt`
and use the CPU wheels instead, otherwise you get a CUDA download and a
`torchvision::nms does not exist` ABI mismatch:
- `.venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`
- Use `opencv-python-headless` (not `opencv-python`) — the VM has no libGL for the GUI build.
