# Lulu UAE – Executive Analytics Dashboard (Streamlit)

Corporate-grade, interactive dashboard for Lulu Market leadership. Built with Streamlit and Plotly.

## Features
- KPI overview and drill-downs
- Sales & Revenue trends (daily, monthly), category mix treemap, city rankings
- Customer segments & loyalty impact
- Inventory / stock-out analysis and returns
- Geography / City insights
- Actions & Recommendations with export to Markdown
- Sidebar filters: date range, city, category, store format, Top-N selector
- Data-quality checks & anomaly detection visible in-app
- Optional simulation to scale rows for demo

## Project Structure
```
app.py
utils.py
plots.py
requirements.txt
README.md
assets/
  logo.png
data/
  lulu_uae_master_2000.csv
```

## Setup
```bash
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
streamlit run app.py
```

## Notes & Assumptions
- Uses the provided `data/lulu_uae_master_2000.csv`. If some fields are missing in future datasets, the app will derive: hour_of_day, day_of_week, order_month.
- If your dataset is very small, enable "Simulate larger dataset" in the sidebar to duplicate with jitter for UI testing.
- Click interactions use `streamlit-plotly-events` for contextual messages. If unavailable, the app degrades gracefully.

## Deploy
- Push this repo to GitHub.
- On Streamlit Cloud: create a new app pointing to `app.py`, set Python version to 3.9+ and use this `requirements.txt`.
