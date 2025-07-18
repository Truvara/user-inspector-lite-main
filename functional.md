# Functional Documentation

## Overview
User Inspector Lite automates the process of reviewing user access across HR and IT systems. It parses user data, performs compliance checks, and generates reports for IT/HR review.

## Main Functional Modules

### 1. Data Parsing (`parser.py`)
- Loads user data from Excel/CSV files for Darwinbox, Okta, Slack, and Google Workspace.
- Standardizes and parses date fields across different formats.
- Outputs cleaned dataframes for further processing.

### 2. Compliance Inspection (`inspector.py`)
- **Joiner Checks:** Ensures new joiners receive access only after their joining date.
- **Leaver Checks:** Ensures leavers' access is revoked after their exit date.
- **Idle Checks:** Identifies users who have not logged in for 45, 90, or 120+ days.
- **System User Checks:** Detects system accounts not tracked in HR records.
- **Summary Generation:** Aggregates HR, IT, and compliance statistics for reporting.

### 3. Reporting (`reporter.py`)
- Generates an Excel report with:
  - HR summary
  - IT systems summary
  - Compliance summary
  - Detailed sheets for each check and parsed data

### 4. Application Entrypoint (`app.py`)
- Orchestrates the workflow: parsing, inspection, summary, and reporting.
- Handles logging and error management.

## Workflow
1. **Data files** are placed in the `data/` directory.
2. **Run** the application (`python app.py`).
3. **Parser** loads and standardizes data.
4. **Inspector** performs compliance checks and generates summaries.
5. **Reporter** creates a comprehensive Excel report in the `data/` folder. 