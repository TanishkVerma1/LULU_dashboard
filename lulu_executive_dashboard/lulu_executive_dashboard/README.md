# Lulu Executive Dashboard (Streamlit)

A corporate-grade, interactive dashboard to surface business insights from Lulu UAE transactional data.
Every chart includes a **Business outcome idea** to help decision-makers take action.

## Features
- KPI tiles (Revenue, AOV, Units, Repeat customer rate)
- Revenue by Department/Category/City (+ Gender & Age Group comparisons)
- Monthly revenue trend (seasonality planning)
- AOV by Channel and Store Format
- Price vs Quantity scatter with trendline (elasticity proxy)
- Sidebar filters for City, Department, Category, Brand, Channel, Gender, Age Group, Store Format
- Auto-detection of column names from the provided metadata/schema

## Project Structure
```
.
├── app.py
├── utils.py
├── plots.py
├── requirements.txt
├── data/
│   ├── lulu_uae_master_2000.csv
│   └── lulu_uae_master_metadata.csv
└── assets/
    └── logo.png (optional)
```

## Quickstart

1. **Create a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run locally**
```bash
streamlit run app.py
```

4. **Deploy to Streamlit Cloud**
- Push this repository to GitHub.
- On Streamlit Cloud, create a new app pointing to `app.py` (Python 3.9+).
- Add any required secrets in Streamlit settings if later needed.

## Notes
- Replace `assets/logo.png` with your corporate logo (transparent PNG recommended).
- The app attempts to infer column names. If your schema differs, adjust `infer_columns()` in `utils.py`.
- **Under each graph** the app prints a Business outcome idea tailored to the specific chart.
