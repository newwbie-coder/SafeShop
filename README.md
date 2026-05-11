# SafeShop

AI-powered real-time food ingredient and nutrition analysis system.

SafeShop is an end-to-end applied AI + data engineering product that helps users understand packaged food products beyond marketing claims. It analyzes ingredients and nutrition data in real time, detects additives and ultra-processed signals, and returns an explainable food-health score through a FastAPI backend and browser extension workflow.

## Problem Statement

Consumers often struggle to understand:

- hidden additives
- misleading nutrition labels
- ultra-processed foods
- ingredient safety

SafeShop addresses that gap by extracting product information from live product pages, normalizing ingredient text, parsing nutrition labels, and converting those signals into an interpretable score with reasons.

## Features

- Real-time ingredient extraction from supported product pages
- Nutrition parsing from messy semi-structured label text
- Explainable food-health scoring with human-readable reasons
- Browser extension integration for live product analysis
- Ingredient normalization pipeline for noisy label data
- OCR-ready architecture for label-image workflows
- Expandable ML-based scoring layer for future experiments

## Positioning

SafeShop should be viewed as a polished real-world AI product system, not just a scraper or a standalone ML model. Its strongest engineering signals are:

- live product-page extraction
- explainable scoring
- backend API integration
- browser-extension UX
- scalable modular architecture
- OCR and ML extensibility

## Tech Stack

- Python
- FastAPI
- Pydantic
- Requests
- BeautifulSoup
- Browser Extension APIs
- OCR tooling with EasyOCR/OpenCV
- Machine learning experiments with pandas and scikit-learn

## How It Works

1. The browser extension reads product information from a supported product page.
2. It sends ingredient and nutrition text to the FastAPI backend.
3. The backend normalizes ingredients and parses nutrition values.
4. Additives, sweeteners, processed oils, and ultra-processed signals are detected.
5. The scoring engine returns a score, verdict, reasons, and health flags.
6. The extension injects the result directly into the shopping experience.

## Project Structure

```text
SafeShop/
├── backend/
│   ├── main.py
│   ├── pipeline.py
│   ├── final_scoring_engine.py
│   ├── ingredient_analyzer.py
│   ├── ingredient_cleaner.py
│   ├── normalize_dataset.py
│   └── nutrition_parser4.py
├── knowledge/
├── scraper/
├── extension/
├── ocr_layer/
├── ml_based/
├── data/
│   └── sample/
├── tests/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
└── LICENSE
```

## API Example

### Request

```json
POST /analyze
{
  "name": "Sample Instant Noodles",
  "ingredients": "Refined wheat flour, palm oil, flavour enhancer (INS 621)",
  "nutrition_text": "Energy 420 kcal, Protein 8 g, Carbohydrate 65 g, Sugars 5 g, Sodium 980 mg"
}
```

### Response

```json
{
  "score": 36.36,
  "verdict": "Unhealthy",
  "reasons": [
    "High salt (can increase BP)",
    "Highly processed product",
    "Artificial additive present"
  ],
  "flags": {
    "msg": true,
    "ultra_processed": true,
    "sweeteners": []
  }
}
```

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the API

```bash
uvicorn backend.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

## Browser Extension Setup

1. Open `chrome://extensions/`
2. Enable `Developer mode`
3. Click `Load unpacked`
4. Select the `extension/` folder
5. Open a supported BigBasket product page

The extension calls the local backend at `http://127.0.0.1:8000/analyze` and renders the SafeShop score card on the page.

## Sample Data And Pipeline

This repository includes lightweight example files under `data/sample/` so the normalization and scoring flow can be understood without uploading the full scraped datasets.

Example commands:

```bash
python -m backend.normalize_dataset
python -m backend.nutrition_parser4
python -m backend.pipeline
```

Generated scraper outputs are written under `data/generated/` and are gitignored.

## OCR And ML Modules

- `ocr_layer/` contains optional OCR utilities for label-image extraction workflows.
- `ml_based/` contains experimental ML scripts for future scoring expansion.

These folders are included to show the system's extensibility, but the main public demo path is the rule-based backend plus browser extension integration.

## Tests

Lightweight tests are included for:

- nutrition parsing
- scoring engine behavior
- ingredient cleaning

Run them with:

```bash
pytest
```

## Recommended GitHub Name And Subtitle

Repository name: `SafeShop`

Subtitle: `AI-powered real-time food ingredient and nutrition analysis system.`

## High-Impact Next Improvements

- Add 1-2 screenshots of the extension in action
- Add a short demo GIF
- Expand parser and scoring coverage with more edge-case tests
- Add a few more sample products in `data/sample/`

## Why This Repository Works Well Publicly

SafeShop presents as a production-oriented applied AI project with a clear user problem, an understandable system design, and a real user-facing interface. That makes it much stronger for recruiters than a repository that looks like a loose collection of scripts and experiments.
