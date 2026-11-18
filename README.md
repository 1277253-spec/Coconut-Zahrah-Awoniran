# Career Venture Lab - Team Coconut (Pathway ROB-4)
**Course:** AP Statistics | **Challenge Level:** Foundation | **Business:** Robotics Kit and Repair Studio

## Stage 1 Scope
This Stage 1 build implements the deterministic core simulation engine, dated ledger, inventory/cash accounting rules, AP Statistics Foundation synthetic invitation experiment panel, manual JSON snapshot save/load, duplicate-run protection, and automated fixture acceptance tests.

## Local Setup & Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run Automated Acceptance Tests
```bash
pytest -v
```

## Render Deployment Command
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```
