# VLM LLaVA Invoice Intelligence Dashboard 🚀

A premium, state-of-the-art Web Application and CLI utility designed to extract structured information (metadata & line items) from invoice and billing images using Vision-Language Models (LLaVA-1.5-7B) with a lightweight, local, CPU-friendly OCR fallback.

Featuring a beautiful **glassmorphic dark-mode web interface**, real-time visualization, an interactive AI invoice question-answering assistant, and instant client-side Excel exporting.

---

## 🌟 Key Features

1. **8-Field Metadata Extraction**: Automatically parses:
   * **Vendor / Shop Name**
   * **Invoice / Bill Number**
   * **Invoice Date** (normalized to `YYYY-MM-DD` format)
   * **Invoice Time**
   * **Subtotal**
   * **Discount**
   * **Tax / GST**
   * **Total Amount** (accurately resolving final grand totals)
2. **Dynamic Line Items Table**: Parses description, quantity, and unit price for itemized lists.
3. **Dual Execution Modes**:
   * **Hugging Face LLaVA Mode**: Runs the full `llava-hf/llava-1.5-7b-hf` model on CUDA-enabled GPUs.
   * **Lightweight CPU OCR Mode**: Automatically falls back to local `easyocr` and regex-based extraction on CPU machines to prevent Out-Of-Memory (OOM) crashes while returning high-accuracy real data.
4. **Premium UI Dashboard**:
   * Drag-and-drop file upload zone.
   * Glow accents and smooth hover micro-animations.
   * Interactive Invoice QA Chat Assistant (to query specifics like payment terms, address details, or item counts).
   * One-click client-side Excel sheet export (built with SheetJS).
   * Raw JSON payload inspector.

---

## 📂 Project Structure

```
vlm_llava_project/
├── app/
│   ├── main.py          # FastAPI server entry point
│   └── static/          # Premium Frontend Dashboard assets
│       ├── index.html   # Dashboard HTML structure
│       ├── style.css    # HSL-accented glassmorphic CSS rules
│       └── app.js       # File uploads, API fetching, QA chat & Excel export logic
├── config/
│   └── settings.py      # App settings & CPU/GPU device selection
├── core/
│   ├── extractor.py     # OCR & regex parser (CPU) + Hugging Face VLM execution (GPU)
│   ├── cleaner.py       # JSON payload formatter
│   └── prompt.py        # Prompts for VLM inference
├── utils/
│   ├── image_utils.py   # PIL image formatting
│   └── invoice_qa.py    # QA matching logic for interactive chat
├── tests/
│   └── test_api.py      # Automated pytest suite using sample invoices
├── vlm_llava/
│   └── main.py          # Interactive CLI application
├── requirements.txt     # Python dependencies
└── README.md            # Technical manual (this file)
```

---

## ⚙️ Setup & Installation

### 1. Create and Activate Virtual Environment
```bash
# Create Virtual Environment
python -m venv .venv

# Activate Virtual Environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate Virtual Environment (macOS/Linux)
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Web Dashboard

Start the FastAPI server:
```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running:
1. Open your browser to **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**.
2. Drag and drop or browse to select an invoice image (e.g. `wert.jpg` or `sf4.jpg`).
3. Click **Analyze Invoice** to extract the data in real-time.
4. Use the **Q&A Chatbot** to ask custom questions, view the **Raw JSON**, or click **Export to Excel** to download the spreadsheet!

---

## 💻 Running the CLI Application

To run manual question-answering or batch extraction directly in the terminal:
```bash
.\.venv\Scripts\python.exe vlm_llava/main.py
```
* **Mode 1**: Enter questions manually, separated by semicolons (`;`).
* **Mode 2**: Run automatic invoice extraction outputting raw JSON.

---

## 🧪 Running Automated Tests

A comprehensive integration test suite verifies the API routes, 8-field extraction parameters, and QA chatbot functionality using real-world sample images:
```bash
.\.venv\Scripts\python.exe -m pytest
```

---

## 🔧 Environment Configuration

Customize settings using environment variables in a `.env` file at the project root:

```ini
# Toggle mock/CPU OCR mode. If True, uses EasyOCR fallback (highly recommended for CPU).
MOCK_INFERENCE=True

# Model identifier (GPU only)
MODEL_ID=llava-hf/llava-1.5-7b-hf

# Hardware overrides (auto-detects cuda/cpu)
DEVICE=cpu
```
