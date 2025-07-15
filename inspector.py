import pandas as pd
from datetime import datetime, timedelta
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccessInspector:
    def __init__(self, parsed_dfs):
        """Initialize with dictionary of parsed dataframes"""
        self.dfs = parsed_dfs
        self.current_fy_start = self._get_current_fy_start()
        
    def _get_current_fy_start(self):
        """Get the start date of current financial year (April-March)."""
        today = datetime.now()
        if today.month < 4:
            return datetime(today.year - 1, 4, 1)
        return datetime(today.year, 4, 1)

    def _convert_to_datetime(self, date_str):
        """Convert string date to datetime for comparison."""
        if pd.isna(date_str) or date_str == '':
            return None
        try:
            if isinstance(date_str, str):
                return pd.to_datetime(date_str, format='%d-%m-%Y')
            return date_str
        except:
            return None

    def _format_date(self, date):
        """Format datetime to dd-mm-yyyy string."""
        if pd.isna(date) or date is None:
            return None
        if isinstance(date, str):
            return date
        return date.strftime('%d-%m-%Y')

    def joiner_checks(self):
        """Perform new joiner compliance checks."""
        try:
            df_darwinbox = self.dfs['darwinbox'].copy()
            df_okta = self.dfs['okta']
            df_slack = self.dfs['slack']
            df_gws = self.dfs['gws']
            
            # Filter new joiners in current FY
            df_darwinbox['Date Of Joining'] = df_darwinbox['Date Of Joining'].apply(self._convert_to_datetime)
            df_darwinbox['is_new_joiner'] = df_darwinbox['Date Of Joining'] >= self.current_fy_start
            
            # Add compliance and system access columns
            df_darwinbox['compliance_status'] = 'Compliant'
            df_darwinbox['action_item'] = 'No Action Required'
            df_darwinbox['okta_created_date'] = None
            df_darwinbox['slack_created_date'] = None
            df_darwinbox['gws_created_date'] = None
            
            for idx, row in df_darwinbox[df_darwinbox['is_new_joiner']].iterrows():
                email = row['Official Email ID']
                joining_date = row['Date Of Joining']
                
                # Check access dates in each system
                okta_record = df_okta[df_okta['user.email'] == email]
                if not okta_record.empty:
                    df_darwinbox.at[idx, 'okta_created_date'] = okta_record['user.created'].iloc[0]
                    
                slack_record = df_slack[df_slack['Email'] == email]
                if not slack_record.empty:
                    df_darwinbox.at[idx, 'slack_created_date'] = slack_record['Account created (UTC)'].iloc[0]
                    
                gws_record = df_gws[df_gws['Email Address [Required]'] == email]
                if not gws_record.empty:
                    df_darwinbox.at[idx, 'gws_created_date'] = gws_record['Last Sign In [READ ONLY]'].iloc[0]
                
                # Check compliance based on access dates
                for system, date_col in [
                    ('Okta', 'okta_created_date'),
                    ('Slack', 'slack_created_date'),
                    ('GWS', 'gws_created_date')
                ]:
                    if pd.notna(df_darwinbox.at[idx, date_col]):
                        access_date = pd.to_datetime(df_darwinbox.at[idx, date_col], format='%d-%m-%Y')
                        if access_date < (joining_date - timedelta(hours=24)):
                            df_darwinbox.at[idx, 'compliance_status'] = 'Non Compliant'
                            df_darwinbox.at[idx, 'action_item'] = 'Investigate'
            
            # Before returning, convert dates back to string format
            for col in ['Date Of Joining', 'okta_created_date', 'slack_created_date', 'gws_created_date']:
                if col in df_darwinbox.columns:
                    df_darwinbox[col] = df_darwinbox[col].apply(self._format_date)
            
            return df_darwinbox[df_darwinbox['is_new_joiner']]
            
        except Exception as e:
            logger.error(f"Error in joiner checks: {str(e)}")
            if 'gws' in self.dfs:
                logger.debug(f"GWS columns available: {self.dfs['gws'].columns.tolist()}")
            raise

    def leaver_checks(self):
        """Perform leaver compliance checks."""
        try:
            df_darwinbox = self.dfs['darwinbox'].copy()
            df_okta = self.dfs['okta']
            df_slack = self.dfs['slack']
            df_gws = self.dfs['gws']
            
            # Filter leavers in current FY
            df_darwinbox['Date Of Exit'] = df_darwinbox['Date Of Exit'].apply(self._convert_to_datetime)
            df_darwinbox['is_leaver'] = (df_darwinbox['Date Of Exit'] >= self.current_fy_start) & \
                                      (df_darwinbox['Date Of Exit'].notna())
            
            # Add compliance and system access columns
            df_darwinbox['compliance_status'] = 'Compliant'
            df_darwinbox['action_item'] = 'No Action Required'
            df_darwinbox['okta_last_login'] = None
            df_darwinbox['slack_last_login'] = None
            df_darwinbox['gws_last_login'] = None
            df_darwinbox['okta_status'] = None
            df_darwinbox['slack_status'] = None
            df_darwinbox['gws_status'] = None
            
            for idx, row in df_darwinbox[df_darwinbox['is_leaver']].iterrows():
                email = row['Official Email ID']
                exit_date = row['Date Of Exit']
                
                # Get system access details
                okta_record = df_okta[df_okta['user.email'] == email]
                if not okta_record.empty:
                    df_darwinbox.at[idx, 'okta_last_login'] = okta_record['user.lastLogin'].iloc[0]
                    df_darwinbox.at[idx, 'okta_status'] = okta_record['user.status'].iloc[0]
                    
                slack_record = df_slack[df_slack['Email'] == email]
                if not slack_record.empty:
                    df_darwinbox.at[idx, 'slack_last_login'] = slack_record['Last active (UTC)'].iloc[0]
                    df_darwinbox.at[idx, 'slack_status'] = 'Deactivated' if pd.notna(slack_record['Deactivated date (UTC)'].iloc[0]) else 'Active'
                    
                gws_record = df_gws[df_gws['Email Address [Required]'] == email]
                if not gws_record.empty:
                    df_darwinbox.at[idx, 'gws_last_login'] = gws_record['Last Sign In [READ ONLY]'].iloc[0]
                    df_darwinbox.at[idx, 'gws_status'] = gws_record['Status [READ ONLY]'].iloc[0]
                
                # Check compliance based on access status and last login
                for system in ['okta', 'slack', 'gws']:
                    status_col = f'{system}_status'
                    login_col = f'{system}_last_login'
                    
                    if pd.notna(df_darwinbox.at[idx, status_col]) and df_darwinbox.at[idx, status_col] == 'ACTIVE':
                        if datetime.now() > (exit_date + timedelta(hours=24)):
                            df_darwinbox.at[idx, 'compliance_status'] = 'Non Compliant'
                            df_darwinbox.at[idx, 'action_item'] = 'Investigate'
                    
                    if pd.notna(df_darwinbox.at[idx, login_col]):
                        last_login = pd.to_datetime(df_darwinbox.at[idx, login_col], format='%d-%m-%Y')
                        if last_login > exit_date:
                            df_darwinbox.at[idx, 'compliance_status'] = 'Non Compliant'
                            df_darwinbox.at[idx, 'action_item'] = 'Revoke'
            
            # Before returning, convert dates back to string format
            for col in ['Date Of Exit', 'okta_last_login', 'slack_last_login', 'gws_last_login']:
                if col in df_darwinbox.columns:
                    df_darwinbox[col] = df_darwinbox[col].apply(self._format_date)
            
            return df_darwinbox[df_darwinbox['is_leaver']]
            
        except Exception as e:
            logger.error(f"Error in leaver checks: {str(e)}")
            raise

    def idle_checks(self):
        """Perform idle user checks."""
        try:
            df_darwinbox = self.dfs['darwinbox'].copy()
            df_okta = self.dfs['okta']
            df_slack = self.dfs['slack']
            df_gws = self.dfs['gws']
            
            # Filter active users
            active_users = df_darwinbox[df_darwinbox['Date Of Exit'].isna()].copy()
            
            # Add idle check columns
            for days in [45, 90, 120]:
                active_users[f'idle_{days}_days'] = False
            active_users['action_item'] = 'No Action Required'
            
            # Add system-specific columns
            active_users['idle_systems'] = ''
            active_users['okta_last_login'] = None
            active_users['slack_last_login'] = None
            active_users['gws_last_login'] = None
            
            for idx, row in active_users.iterrows():
                email = row['Official Email ID']
                idle_systems = []
                
                for system, df, login_col, email_col in [
                    ('Okta', df_okta, 'user.lastLogin', 'user.email'),
                    ('Slack', df_slack, 'Last active (UTC)', 'Email'),
                    ('GWS', df_gws, 'Last Sign In [READ ONLY]', 'Email Address [Required]')
                ]:
                    user_record = df[df[email_col] == email]
                    if not user_record.empty:
                        last_login = pd.to_datetime(user_record[login_col].iloc[0], format='%d-%m-%Y')
                        # Store last login date for each system
                        active_users.at[idx, f'{system.lower()}_last_login'] = self._format_date(last_login)
                        
                        days_idle = (datetime.now() - last_login).days
                        
                        for threshold in [45, 90, 120]:
                            if days_idle >= threshold:
                                active_users.at[idx, f'idle_{threshold}_days'] = True
                                if system not in idle_systems:
                                    idle_systems.append(system)
                                if threshold >= 120:
                                    active_users.at[idx, 'action_item'] = 'Disable'
                                elif threshold >= 90 and active_users.at[idx, 'action_item'] != 'Disable':
                                    active_users.at[idx, 'action_item'] = 'Investigate'
                
                active_users.at[idx, 'idle_systems'] = ', '.join(idle_systems) if idle_systems else 'None'
            
            return active_users
            
        except Exception as e:
            logger.error(f"Error in idle checks: {str(e)}")
            raise

    def system_user_checks(self):
        """Perform system user checks."""
        try:
            df_darwinbox = self.dfs['darwinbox']
            df_okta = self.dfs['okta'].copy()
            df_slack = self.dfs['slack'].copy()
            df_gws = self.dfs['gws'].copy()
            
            hr_emails = set(df_darwinbox['Official Email ID'])
            
            def is_human_email(email):
                """Check if email follows firstname.lastname@domain format."""
                try:
                    local_part = email.split('@')[0]
                    parts = local_part.split('.')
                    return len(parts) == 2 and all(part.isalpha() for part in parts)
                except:
                    return False
            
            system_users = []
            for system, df, email_col, login_col, status_col in [
                ('Okta', df_okta, 'user.email', 'user.lastLogin', 'user.status'),
                ('Slack', df_slack, 'Email', 'Last active (UTC)', 'Deactivated date (UTC)'),
                ('GWS', df_gws, 'Email Address [Required]', 'Last Sign In [READ ONLY]', 'Status [READ ONLY]')
            ]:
                # For Okta, filter out deprovisioned/suspended users
                if system == 'Okta':
                    df = df[~df[status_col].isin(['DEPROVISIONED', 'SUSPENDED'])]
                
                system_emails = set(df[email_col]) - hr_emails
                for email in system_emails:
                    user_record = df[df[email_col] == email].iloc[0]
                    is_human = is_human_email(email)
                    
                    # Get status based on system
                    if system == 'Slack':
                        status = 'Deactivated' if pd.notna(user_record[status_col]) else 'Active'
                        if status == 'Deactivated':
                            continue
                    else:
                        status = user_record[status_col] if pd.notna(user_record[status_col]) else 'Unknown'
                    
                    system_users.append({
                        'Email': email,
                        'Source System': system,
                        'is_human_user?': is_human,
                        'Last Login': self._format_date(pd.to_datetime(user_record[login_col], format='%d-%m-%Y')),
                        'Status': status,
                        'tracked_in_darwinbox': False,
                        'Action Item': 'Investigate' if is_human else 'No Action Required'
                    })
            
            return pd.DataFrame(system_users)
            
        except Exception as e:
            logger.error(f"Error in system user checks: {str(e)}")
            raise

    def generate_summaries(self):
        """Generate all summary data needed for the report."""
        try:
            # HR Summary
            df_darwinbox = self.dfs['darwinbox']
            
            # First ensure Date Of Joining is in datetime format
            df_darwinbox['Date Of Joining'] = pd.to_datetime(
                df_darwinbox['Date Of Joining'], 
                format='%d-%m-%Y',  # Specify the format explicitly
                errors='coerce'
            )
            
            # Calculate new joiners based on current FY
            df_darwinbox['is_new_joiner'] = df_darwinbox['Date Of Joining'] >= self.current_fy_start
            
            hr_summary = []
            for emp_type in df_darwinbox['Employee Type'].unique():
                type_df = df_darwinbox[df_darwinbox['Employee Type'] == emp_type]
                hr_summary.append({
                    'Employee Type': emp_type,
                    'New Joiners': len(type_df[type_df['is_new_joiner']]),
                    'Active Employees': len(type_df[type_df['Date Of Exit'].isna()]),
                    'Terminated Users': len(type_df[type_df['Date Of Exit'].notna()])
                })
            
            # IT Systems Summary
            it_summary = []
            for system, df, status_col in [
                ('Okta', self.dfs['okta'], 'user.status'),
                ('Slack', self.dfs['slack'], None),
                ('GWS', self.dfs['gws'], 'Status [READ ONLY]')
            ]:
                total_users = len(df)
                if system == 'Slack':
                    active_users = len(df[df['Deactivated date (UTC)'].isna()])
                elif system == 'GWS':
                    active_users = len(df[df[status_col].str.upper() != 'SUSPENDED']) if status_col in df.columns else total_users
                else:
                    active_users = len(df[df[status_col] == 'ACTIVE']) if status_col in df.columns else total_users
                
                it_summary.append({
                    'System': system,
                    'Total Users': total_users,
                    'Active Users': active_users,
                    'Inactive Users': total_users - active_users
                })
            
            # Compliance Summary
            compliance_summary = []
            
            # Joiner compliance
            joiner_results = self.joiner_checks()
            non_compliant = len(joiner_results[joiner_results['compliance_status'] == 'Non Compliant'])
            total = len(joiner_results)
            compliance_summary.append({
                'Check Type': 'New Joiner Access',
                'Total Checked': total,
                'Non Compliant': non_compliant,
                'Compliance Rate': f"{((total - non_compliant) / total * 100):.1f}%" if total > 0 else "N/A"
            })
            
            # Leaver compliance
            leaver_results = self.leaver_checks()
            non_compliant = len(leaver_results[leaver_results['compliance_status'] == 'Non Compliant'])
            total = len(leaver_results)
            compliance_summary.append({
                'Check Type': 'Leaver Access',
                'Total Checked': total,
                'Non Compliant': non_compliant,
                'Compliance Rate': f"{((total - non_compliant) / total * 100):.1f}%" if total > 0 else "N/A"
            })
            
            # Idle user compliance with system breakdown
            idle_results = self.idle_checks()
            idle_summary = {
                'Check Type': 'Idle Users',
                'Total Checked': len(idle_results),
                'Idle >45 Days': 0,
                'Idle >90 Days': 0,
                'Idle >120 Days': 0,
                'Okta': 'xx',
                'Slack': 'xx',
                'GWS': 'xx'
            }

            # Count idle users per system
            for system in ['Okta', 'Slack', 'GWS']:
                system_idle = idle_results[idle_results['idle_systems'].str.contains(system, case=False, na=False)]
                idle_summary[system] = len(system_idle)

            # Count total idle users per threshold
            for threshold in [45, 90, 120]:
                idle_summary[f'Idle >{threshold} Days'] = len(idle_results[idle_results[f'idle_{threshold}_days']])

            compliance_summary.append(idle_summary)

            # System user compliance with system breakdown
            system_results = self.system_user_checks()
            system_summary = {
                'Check Type': 'System Users',
                'Total Checked': len(system_results),
                'Human Format': len(system_results[system_results['is_human_user?']]),
                'System Format': len(system_results[~system_results['is_human_user?']]),
                'Okta': 'xx',
                'Slack': 'xx',
                'GWS': 'xx'
            }

            # Count users per system
            for system in ['Okta', 'Slack', 'GWS']:
                system_users = system_results[system_results['Source System'] == system]
                system_summary[system] = len(system_users)

            compliance_summary.append(system_summary)

            return {
                'hr_summary': pd.DataFrame(hr_summary),
                'it_summary': pd.DataFrame(it_summary),
                'compliance_summary': pd.DataFrame(compliance_summary)
            }
            
        except Exception as e:
            logger.error(f"Error generating summaries: {str(e)}")
            raise