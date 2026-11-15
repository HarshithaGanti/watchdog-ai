# 🛡️ WatchdogAI: Who Watches the Watchdog?

> *An intelligent, minimalist RAG-based compliance auditor that checks whether AI-generated suggestions violate official platform terms, campus rules, or legal frameworks.*

---

## 🚀 Overview
Large Language Models (like ChatGPT or Gemini) frequently output helpful-sounding suggestions that can violate platform terms of service, university regulations, or local laws (e.g., automated scraping, unauthorized local video downloading, substance policy violations, or campus code breaches). 

**WatchdogAI** acts as an independent oversight auditor. By leveraging a lightweight RAG architecture and Google Gemini’s massive context window, it intercepts suspicious AI advice, cross-references it against official source documents, and outputs a structured compliance verdict (**Supported**, **Contradicted**, or **Unverified**) backed by exact policy citations.

---

## ✨ Key Features
- **Split-Screen Interactive UI:** Input suspicious LLM claims on the left panel and stream your audit and follow-up conversation on the right.
- **Strict Compliance Verdicts:** Automatically parses and flags violations with high-contrast banner alerts (`[CONTRADICTED]`, `[SUPPORTED]`, `[UNVERIFIABLE]`).
- **Conversational Follow-up:** Unlock a dynamic chat history stream to interrogate or discuss the audit results further.
- **Markdown Export:** Download complete audit reports instantly as `.md` files for record-keeping or assignment submissions.
- **Zero-Database RAG Pipeline:** Built for lightning-fast execution without heavy database overhead (compatible with Python 3.11+).
- **Automated Evaluation Runner:** Includes a checkpointed evaluation script (`report_generator.py`) and synthetic test set (`test_set.csv`) to compute system accuracy and generate presentation charts.

---

## 📂 Project File Structure
```text
watchdog-ai/
│
├── data/                          # Official policy source files
│   ├── youtube.txt                # YouTube Terms of Service & API Rules
│   ├── instagram.txt              # Instagram Terms of Service & Automation Policies
│   ├── ugc_campus_policy.txt      # UGC Anti-Ragging & Campus Conduct Norms
│   └── hostel_rules.txt           # University Hostel & Substance Restrictions
│
├── app.py                         # Main Streamlit web application
├── report_generator.py            # Automated evaluation and accuracy script
├── test_set.csv                   # 40-row synthetic test evaluation set
├── evaluation_results.csv         # Resumable evaluation checkpoint output
├── accuracy_chart.png             # Generated performance chart for slides
├── requirements.txt               # Python package dependencies
├── .env                           # Secure environment API keys (excluded from git)
└── README.md                      # Project documentation
```

## 🛠️ Tech Stack
- Frontend / UI: Streamlit (Custom minimalist styling, pitch-black #000000 theme, zero rounded corners, custom Google Fonts: Redaction 50 & Space Grotesk).

- LLM & RAG Engine: Google GenAI SDK (google-genai using gemini-3.5-flash-lite).

- Data Handling & Evaluation: Pandas, Matplotlib.

## Setup & Installation Guide

- Clone or Open Project: Open your project directory in VS Code or your local terminal.

- Install Dependencies: Make sure you have Python installed, then run:

```
pip install -r requirements.txt
```