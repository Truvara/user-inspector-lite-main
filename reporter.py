import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccessReporter:
    def __init__(self, parsed_dfs, inspection_results):
        self.dfs = parsed_dfs
        self.results = inspection_results
        self.output_folder = Path('data')
        self.output_folder.mkdir(exist_ok=True, parents=True)

    def generate_full_report(self):
        """Generate complete report with inspection results."""
        try:
            timestamp = datetime.now().strftime('%d%m')
            output_path = self.output_folder / f'user-inspector-report-{timestamp}.xlsx'
            
            with pd.ExcelWriter(
                output_path, 
                engine='xlsxwriter',
                engine_kwargs={'options': {'nan_inf_to_errors': True}}
            ) as writer:
                # Add date format
                date_format = writer.book.add_format({'num_format': 'dd-mm-yyyy'})
                
                # Write main summary sheet first
                self._write_summary_sheet(writer)
                
                # Write detailed results in subsequent sheets with date formatting
                for sheet_name, df in {
                    'Joiner Details': self.results.get('joiner_checks'),
                    'Leaver Details': self.results.get('leaver_checks'),
                    'Idle User Details': self.results.get('idle_checks'),
                    'System User Details': self.results.get('system_user_checks'),
                    **{f'Parsed_{name}': data for name, data in self.dfs.items()}
                }.items():
                    if df is not None:
                        df = df.copy()
                        df.fillna('').to_excel(writer, sheet_name=sheet_name, index=False)
                        worksheet = writer.sheets[sheet_name]
                        
                        # Apply date format to date columns
                        for idx, col in enumerate(df.columns):
                            if any(date_term in col.lower() for date_term in ['date', 'joining', 'exit', 'login']):
                                worksheet.set_column(idx, idx, None, date_format)
            
            logger.info(f"Generated full report at {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating full report: {str(e)}")
            raise

    def _write_summary_sheet(self, writer):
        """Write the main summary sheet in the format shown in screenshot."""
        workbook = writer.book
        worksheet = workbook.add_worksheet('Summary')
        
        # Add formatting
        bold = workbook.add_format({'bold': True})
        
        # Write HR Summary section
        worksheet.write('A1', 'HR Summary', bold)
        worksheet.write('A2', 'Employee Type')
        worksheet.write('B2', 'New Joiners')
        worksheet.write('C2', 'Active Employees')
        worksheet.write('D2', 'Terminated Users')
        
        # Populate HR data
        row = 2
        for idx, data in self.results['hr_summary'].iterrows():
            worksheet.write(row, 0, data['Employee Type'])
            worksheet.write(row, 1, data['New Joiners'])
            worksheet.write(row, 2, data['Active Employees'])
            worksheet.write(row, 3, data['Terminated Users'])
            row += 1
        
        # Write IT Systems Summary section
        current_row = row + 2  # Add spacing
        worksheet.write(f'A{current_row}', 'IT Systems Summary', bold)
        worksheet.write(f'A{current_row+1}', 'System')
        worksheet.write(f'B{current_row+1}', 'Total Users')
        worksheet.write(f'C{current_row+1}', 'Active Users')
        worksheet.write(f'D{current_row+1}', 'Inactive Users')
        
        # Populate IT Systems data
        current_row += 2
        for idx, data in self.results['it_summary'].iterrows():
            worksheet.write(current_row, 0, data['System'])
            worksheet.write(current_row, 1, data['Total Users'])
            worksheet.write(current_row, 2, data['Active Users'])
            worksheet.write(current_row, 3, data['Inactive Users'])
            current_row += 1
        
        # Write Compliance Summary section
        current_row += 2  # Add spacing
        worksheet.write(f'A{current_row}', 'Compliance Summary', bold)
        worksheet.write(f'A{current_row+1}', 'Check Type')
        worksheet.write(f'B{current_row+1}', 'description')
        worksheet.write(f'C{current_row+1}', 'Total Checked')
        worksheet.write(f'D{current_row+1}', 'Non Compliant')
        worksheet.write(f'E{current_row+1}', 'Compliance Rate')
        worksheet.write(f'F{current_row+1}', 'Okta')
        worksheet.write(f'G{current_row+1}', 'Slack')
        worksheet.write(f'H{current_row+1}', 'GWS')
        
        # Add descriptions
        descriptions = {
            'New Joiner Access': 'whether new joiners have got access prior to date of joining',
            'Leaver Access': 'whether exit employees retained access after LWD and / or logged in post LWD',
            'Idle Users': 'whether active employees have not logged into IT systems',
            'System Users': 'whether IT system users are tracked accurately in HR records'
        }
        
        # Populate Compliance data with descriptions
        current_row += 2
        compliance_data = self.results['compliance_summary']
        for idx, data in compliance_data.iterrows():
            check_type = data['Check Type']
            worksheet.write(current_row, 0, check_type)
            worksheet.write(current_row, 1, descriptions.get(check_type, ''))
            worksheet.write(current_row, 2, data['Total Checked'])
            
            if check_type in ['New Joiner Access', 'Leaver Access']:
                if 'Non Compliant' in data:
                    worksheet.write(current_row, 3, data['Non Compliant'])
                if 'Compliance Rate' in data:
                    worksheet.write(current_row, 4, data['Compliance Rate'])
            
            elif check_type == 'Idle Users':
                worksheet.write(current_row, 5, data['Okta'])
                worksheet.write(current_row, 6, data['Slack'])
                worksheet.write(current_row, 7, data['GWS'])
            
            elif check_type == 'System Users':
                worksheet.write(current_row, 5, data['Okta'])
                worksheet.write(current_row, 6, data['Slack'])
                worksheet.write(current_row, 7, data['GWS'])
            
            current_row += 1