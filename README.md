# User Inspector Lite

User Inspector Lite is a Python tool for automating user access reviews across HR and IT systems (Okta, Slack, Google Workspace, Darwinbox). It parses user data, checks compliance for joiners, leavers, idle users, and system users, and generates detailed Excel reports.

## Features
- Parses data from multiple sources (Excel/CSV)
- Checks compliance for new joiners, leavers, idle users, and system users
- Generates summary and detailed reports in Excel format
- Designed for IT and HR compliance teams

## Quick Start
1. Place your data files (darwinbox, okta, slack, gws) in the `data/` folder as `.xlsx` or `.csv`.
2. Run the main application:
   ```bash
   python app.py
   ```
3. Find the generated report in the `data/` folder.

See `deploy.md` for full deployment instructions.
