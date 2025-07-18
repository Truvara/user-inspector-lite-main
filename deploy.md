# Deployment Guide

## Prerequisites
- Python 3.7+
- pip (Python package manager)

## Setup Steps

1. **Clone or download the repository.**
2. **Navigate to the project root directory.**
3. **(Optional) Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
4. **Install dependencies:**
   ```bash
   pip install pandas openpyxl xlsxwriter dateparser python-dateutil
   ```
5. **Prepare your data:**
   - Place your data files (`darwinbox.xlsx`/`.csv`, `okta.xlsx`/`.csv`, `slack.xlsx`/`.csv`, `gws.xlsx`/`.csv`) in the `data/` folder.

6. **Run the application:**
   ```bash
   python app.py
   ```
   - The generated report will be saved in the `data/` folder.

## Notes
- Ensure your data files have the expected columns as per the system (see `parser.py` for details).
- For troubleshooting, check the log output in the console. 