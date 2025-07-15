import pandas as pd
from datetime import datetime
import openpyxl
import logging
from pathlib import Path
import dateparser
from dateutil import parser as date_parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataParser:
    def __init__(self, data_folder):
        self.data_folder = Path(data_folder)
        self.parsed_dates = {}
        
    def parse_date(self, date_str):
        """Parse different date formats to dd-mm-yyyy using dateparser."""
        # Handle empty values and "Never logged in"
        if pd.isna(date_str) or str(date_str).strip() == '' or str(date_str).strip().lower() == 'never logged in':
            return None
            
        try:
            # Step 1: Clean and standardize input
            if isinstance(date_str, datetime):
                return date_str.strftime('%d-%m-%Y')
            
            date_str = str(date_str).strip()
            
            # New Step: Handle Excel timestamp numbers
            try:
                if date_str.replace('.', '').isdigit():
                    # Convert to float and check if it looks like an Excel timestamp
                    timestamp = float(date_str)
                    if timestamp > 25569:  # Excel timestamps start from 1900-01-01
                        # Convert Excel timestamp to datetime
                        delta = pd.Timedelta(days=timestamp-25569)
                        base_date = pd.Timestamp('1900-01-01')
                        parsed_date = base_date + delta
                        return parsed_date.strftime('%d-%m-%Y')
            except:
                pass
            
            # Step 2: Handle GWS format specifically (YYYY/MM/DD HH:MM:SS)
            if '/' in date_str and ':' in date_str:
                try:
                    # Replace '/' with '-' for consistent parsing
                    date_str = date_str.replace('/', '-')
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    return parsed_date.strftime('%d-%m-%Y')
                except:
                    pass
            
            # Step 3: Try common specific formats
            specific_formats = [
                # ISO formats
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                
                # Common formats
                '%d-%m-%Y',
                '%d/%m/%Y',
                '%m/%d/%Y',
                
                # With time
                '%d-%m-%Y %H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%m/%d/%Y %H:%M:%S',
                
                # GWS format
                '%Y/%m/%d %H:%M:%S'
            ]
            
            for fmt in specific_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%d-%m-%Y')
                except ValueError:
                    continue
            
            # Step 4: Handle GWS AM/PM format
            if 'AM' in date_str.upper() or 'PM' in date_str.upper():
                try:
                    parsed_date = date_parser.parse(date_str)
                    return parsed_date.strftime('%d-%m-%Y')
                except:
                    pass
            
            # Step 5: Handle Unix timestamps
            if date_str.replace('.', '').isdigit():
                try:
                    # Handle milliseconds
                    if len(date_str) > 10:
                        timestamp = float(date_str) / 1000
                    else:
                        timestamp = float(date_str)
                    return datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y')
                except:
                    pass
            
            # Step 6: Use dateparser as final fallback
            try:
                parsed_date = dateparser.parse(
                    date_str,
                    settings={
                        'DATE_ORDER': 'DMY',
                        'STRICT_PARSING': False,
                        'PREFER_DAY_OF_MONTH': 'first',
                        'RETURN_AS_TIMEZONE_AWARE': False
                    }
                )
                if parsed_date:
                    return parsed_date.strftime('%d-%m-%Y')
            except:
                pass
            
            # Step 7: Log unparseable dates (except "Never logged in")
            if date_str.lower() != 'never logged in':
                logger.warning(f"Could not parse date: {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {str(e)}")
            return None

    def load_and_parse(self):
        """Load all sheets and parse dates."""
        try:
            # Configuration for each sheet
            sheets_config = {
                'darwinbox': {
                    'date_cols': ['Date Of Joining', 'Date Of Exit'],
                    'email_cols': ['Official Email ID'],
                    'status_cols': ['Employee Type', 'Employment Status']
                },
                'gws': {
                    'date_cols': ['Last Sign In [READ ONLY]'],
                    'email_cols': ['Email Address [Required]'],
                    'status_cols': ['Status [READ ONLY]']
                },
                'okta': {
                    'date_cols': ['user.lastUpdate', 'user.created', 'user.activation', 
                                'user.statusChange', 'user.lastLogin'],
                    'email_cols': ['user.email', 'user.secondEmail'],
                    'status_cols': ['user.status']
                },
                'slack': {
                    'date_cols': ['Account created (UTC)', 'Last active (UTC)', 
                                'Deactivated date (UTC)'],
                    'email_cols': ['Email'],
                    'status_cols': ['Account type']
                }
            }
            
            parsed_dfs = {}
            
            # Process each sheet
            for sheet_name, config in sheets_config.items():
                xlsx_path = self.data_folder / f"{sheet_name}.xlsx"
                csv_path = self.data_folder / f"{sheet_name}.csv"
                
                if xlsx_path.exists():
                    logger.info(f"Processing Excel file: {xlsx_path}")
                    df = pd.read_excel(xlsx_path, na_values=['', 'NA', 'N/A'])
                elif csv_path.exists():
                    logger.info(f"Processing CSV file: {csv_path}")
                    df = pd.read_csv(csv_path, na_values=['', 'NA', 'N/A'])
                else:
                    logger.warning(f"No file found for {sheet_name}")
                    continue
                
                # Add source system column
                df['Source System'] = sheet_name
                
                # Special handling for GWS status
                if sheet_name == 'gws' and 'Status [READ ONLY]' in df.columns:
                    # Ensure status is properly formatted
                    df['Status [READ ONLY]'] = df['Status [READ ONLY]'].str.upper()
                
                # Parse dates
                for date_col in config['date_cols']:
                    if date_col in df.columns:
                        logger.info(f"Parsing dates for column: {date_col} in {sheet_name}")
                        
                        # Special handling for darwinbox Date Of Joining
                        if sheet_name == 'darwinbox' and date_col == 'Date Of Joining':
                            df[date_col] = df[date_col].fillna('')
                            df[date_col] = df[date_col].astype(str)
                            df[date_col] = df[date_col].apply(self.parse_date)
                            # Skip the additional datetime conversion since parse_date already returns
                            # the correct format
                        else:
                            # Original date parsing logic for other columns
                            df[date_col] = df[date_col].fillna('')
                            df[date_col] = df[date_col].astype(str)
                            df[date_col] = df[date_col].apply(self.parse_date)
                            df[date_col] = pd.to_datetime(df[date_col], format='%d-%m-%Y', errors='coerce')
                            df[date_col] = df[date_col].dt.strftime('%d-%m-%Y')
                        
                        self.parsed_dates[f"{sheet_name}_{date_col}"] = date_col
                        
                        # Log any unparsed dates (excluding empty and "Never logged in")
                        unparsed = df[
                            (df[date_col].isna()) & 
                            (df[date_col].astype(str).str.strip() != '') & 
                            (df[date_col].astype(str).str.lower() != 'never logged in')
                        ][date_col].unique()
                        if len(unparsed) > 0:
                            logger.warning(f"Unparsed dates in {sheet_name}.{date_col}: {[x for x in unparsed if str(x).strip() != '']}")
                
                # Reorder columns with Source System first
                priority_cols = ['Source System'] + config['email_cols'] + config['date_cols'] + config['status_cols']
                remaining_cols = [col for col in df.columns if col not in priority_cols]
                df = df[priority_cols + remaining_cols]
                
                parsed_dfs[sheet_name] = df
            
            # Save all parsed data to a single Excel file with multiple sheets
            output_path = self.data_folder / "parsed_data.xlsx"
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, df in parsed_dfs.items():
                    # Convert datetime columns to dd-mm-yyyy format before saving
                    df_to_save = df.copy()
                    for col in df_to_save.columns:
                        if any(date_term in col.lower() for date_term in ['date', 'joining', 'exit', 'login']):
                            # Skip conversion if the column is already in the correct format
                            if df_to_save[col].dtype == 'object':
                                # Check if values are already in dd-mm-yyyy format
                                continue
                            # For any other format, convert explicitly with dayfirst=True
                            df_to_save[col] = pd.to_datetime(
                                df_to_save[col], 
                                format='%d-%m-%Y',
                                errors='coerce',
                                dayfirst=True
                            ).dt.strftime('%d-%m-%Y')
                    
                    df_to_save.to_excel(writer, sheet_name=sheet_name, index=False)
                    logger.info(f"Saved sheet {sheet_name} to parsed_data.xlsx")
            
            logger.info(f"Saved all parsed data to {output_path}")
            
            return parsed_dfs
            
        except Exception as e:
            logger.error(f"Error in parsing data: {str(e)}")
            raise

    def get_parsed_date_columns(self):
        """Return information about parsed date columns."""
        return self.parsed_dates