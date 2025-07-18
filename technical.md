# Technical Documentation

## Architecture Overview
User Inspector Lite is structured as a modular Python application with clear separation between data parsing, compliance inspection, and reporting. The main workflow is orchestrated in `app.py`.

## Key Components

### 1. DataParser (`parser.py`)
- Loads data from Excel/CSV files for each system (Darwinbox, Okta, Slack, GWS).
- Handles various date formats and normalizes them to a standard format.
- Returns a dictionary of pandas DataFrames keyed by system name.

### 2. AccessInspector (`inspector.py`)
- Accepts parsed dataframes and performs compliance checks:
  - `joiner_checks()`: Validates access provisioning for new joiners.
  - `leaver_checks()`: Validates deprovisioning for leavers.
  - `idle_checks()`: Flags users idle for 45/90/120+ days.
  - `system_user_checks()`: Identifies system accounts not tracked in HR.
  - `generate_summaries()`: Aggregates summary statistics for reporting.
- Uses pandas for data manipulation and datetime for date logic.

### 3. AccessReporter (`reporter.py`)
- Consumes parsed data and inspection results.
- Generates a multi-sheet Excel report using pandas and xlsxwriter.
- Formats summary and detail sheets, applying date formatting and descriptions.

### 4. Main Application (`app.py`)
- Sets up logging and error handling.
- Instantiates parser, inspector, and reporter in sequence.
- Handles the end-to-end workflow from data loading to report generation.

## Data Flow
1. Data files are loaded and parsed into DataFrames.
2. DataFrames are passed to AccessInspector for compliance checks.
3. Inspection results and summaries are passed to AccessReporter.
4. AccessReporter writes the final Excel report.

## Extensibility
- **Adding new systems:** Update `parser.py` and `inspector.py` to handle new data sources.
- **Custom checks:** Implement new methods in `AccessInspector`.
- **Report customization:** Extend `AccessReporter` for new report sections or formats.

## Dependencies
- pandas
- openpyxl
- xlsxwriter
- dateparser
- python-dateutil

See `deploy.md` for environment setup. 