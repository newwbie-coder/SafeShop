# AGENTS.md

## Cursor Cloud specific instructions

SafeShop is a Python (3.12) FastAPI backend that performs rule-based food
ingredient/nutrition scoring, plus a Chrome browser extension (`extension/`).
The backend is the main runnable and testable surface; see `README.md` for the
`POST /analyze` request/response shape and overall architecture.

Python deps are installed into a virtualenv at `.venv`. Always invoke tools
through it (e.g. `.venv/bin/uvicorn`, `.venv/bin/python`).

### Run / test
- Run API (dev): `.venv/bin/uvicorn backend.main:app --reload` — serves on
  `http://127.0.0.1:8000`. Core endpoint is `POST /analyze`; interactive docs
  are at `http://127.0.0.1:8000/docs`.
- Tests: `.venv/bin/python -m pytest`. Run it as `python -m pytest` (NOT the bare
  `pytest` binary) so the repo root is on `sys.path` — the tests import the
  `backend` package and bare `pytest` fails collection with `No module named 'backend'`.
- Sample data pipeline: `.venv/bin/python -m backend.pipeline` (reads/writes files
  under `data/sample/`; the scored output file is git-tracked, so revert it after
  ad-hoc runs).
- There is no linter configured for this repo.
- The browser extension (`extension/`) is loaded unpacked in Chrome and calls the
  local backend at `http://127.0.0.1:8000/analyze`; it only renders on a supported
  BigBasket product page.

### Optional OCR / ML dependencies (heavy, not installed by default)
`requirements.txt` lists optional OCR/ML extras (`torch`, `easyocr`,
`opencv-python`) used by `ocr_layer/` and `ml_based/`. These are large and finicky
and are intentionally NOT installed by the startup update script (only the core
API/test deps are). They are not required for the main backend + extension demo
path. If you need them, avoid the plain `requirements.txt` defaults and use CPU
wheels to avoid a large CUDA download and a `torchvision::nms does not exist` ABI
mismatch:
- `.venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`
- Use `opencv-python-headless` (not `opencv-python`) — the VM has no libGL for the GUI build.

`ocr_layer/ocr.py` auto-detects GPU (`gpu=torch.cuda.is_available()`), so `OCREngine`
runs on CPU here without changes. On first use, `easyocr` downloads its detection +
recognition models (~100 MB) over the network, so the first `OCREngine()` init is slow
and requires egress. End-to-end OCR flow: `OCRProcessor().process(image)` -> feed the
returned `ingredients` / `nutrition_text` into `POST /analyze`.

The `ml_based/` scripts depend on trained model binaries (`*.pkl`) and large datasets
that are intentionally excluded from the repo (see `ml_based/README.md`), so they are
expected to be non-runnable out of the box — that is by design, not a bug to fix.
