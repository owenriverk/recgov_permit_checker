import requests
import pandas as pd
import json
import time
import random
import smtplib
import logging
import os
from email.message import EmailMessage
from datetime import datetime
from typing import Dict, List, Any
import traceback
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from Permit import Permit, Section

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("permit_checker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("permit_checker")

_last_error_notification_time = None


def save_previous_data(data: Dict, filename: str = "previous_permits.json") -> None:
    """
    Save the current permit availability data to a JSON file.
    
    Args:
        data: Dictionary containing permit availability data by section
        filename: Path to the output JSON file
    """
    try:
        with open(filename, "w") as f:
            json.dump(data, f)
        logger.info(f"Successfully saved data to {filename}")
    except Exception as e:
        logger.error(f"Error saving data: {e}")


def load_previous_data(filename: str = "previous_permits.json") -> Dict:
    """
    Load previously saved permit availability data from a JSON file.
    
    Args:
        filename: Path to the JSON file containing previous data
        
    Returns:
        Dictionary containing the previous permit data, or empty dict if file doesn't exist
    """
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        logger.info(f"Successfully loaded data from {filename}")
        return data
    except FileNotFoundError:
        logger.info(f"No previous data file found at {filename}, creating new")
        return {}  # Return empty dict if no previous data exists
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return {}  # Return empty dict on any other error


def find_canceled_permits(old_data: Dict, new_data: Dict) -> List[str]:
    """
    Compare previous and current permit data to find newly available permits.
    
    This function identifies three types of new availability:
    1. Permits that went from 0 to a positive number (cancellations)
    2. New dates that weren't present before
    3. New sections that weren't present before
    
    Args:
        old_data: Dictionary containing previous permit data
        new_data: Dictionary containing current permit data
        
    Returns:
        List of strings describing newly available permits
    """
    canceled_permits = []
    
    # Iterate through each section in the new data
    for section in new_data:
        if section in old_data:
            # Section exists in both old and new data
            for date, new_value in new_data[section].items():
                if date in old_data[section]:
                    # Date exists in both old and new data
                    # Check if it went from 0 to some positive number (cancellation)
                    if old_data[section][date] == 0 and new_value > 0:
                        canceled_permits.append(f"{section} - {date} - {new_value} permits available")
                else:
                    # Date exists only in new data - it's a new listing
                    if new_value > 0:
                        canceled_permits.append(f"{section} - {date} - {new_value} permits available (new listing)")
        else:
            # Section exists only in new data - it's a new section
            for date, new_value in new_data[section].items():
                if new_value > 0:
                    canceled_permits.append(f"{section} - {date} - {new_value} permits available (new section)")
    
    return canceled_permits


def create_table(new_data: Dict) -> pd.DataFrame:
    """
    Convert the permit availability data to a pandas DataFrame for display.
    
    Args:
        new_data: Dictionary containing permit availability data
        
    Returns:
        Pandas DataFrame with dates as index and sections as columns
    """
    # Create an empty DataFrame
    df = pd.DataFrame()
    
    # For each section in the data
    for section, dates in new_data.items():
        # Convert the section's date availability to a Series
        section_series = pd.Series(dates, name=section)
        
        # Add this Series as a column to the DataFrame
        df = pd.concat([df, section_series], axis=1)
    
    # Clean up the DataFrame
    df = df.fillna(0)  # Fill NaN values with 0
    
    # Sort by date
    df = df.sort_index()
    
    return df


def send_alert(permits_found: List[str]) -> bool:
    """
    Send an email alert with information about newly available permits.
    
    Args:
        permits_found: List of strings describing newly available permits
        
    Returns:
        Boolean indicating whether the email was sent successfully
    """
    try:
        msg = EmailMessage()
        
        # Create a nicely formatted email body
        email_body = "Permit cancellations found!\n\n"
        for permit in permits_found:
            email_body += f"- {permit}\n"
        
        # Add timestamp
        email_body += f"\n\nSent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        msg.set_content(email_body)
        msg['Subject'] = f'River Permit Alert! ({len(permits_found)} permits found)'
        
        # Get email credentials from environment variables for security
        # Falls back to hardcoded values if environment variables aren't set
        sender_email = os.environ.get('PERMIT_EMAIL', 'govrecpermit@gmail.com')
        recipients = [
            os.environ.get('PERMIT_EMAIL', 'govrecpermit@gmail.com'),
            'owenriverk@gmail.com', 'godoggie@gmail.com', 'shellikai@gmail.com', 'lizwilli541@gmail.com'
        ]
        
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipients)
        
        # Connect to SMTP server
        # SECURITY NOTE: Better to use environment variables than hardcoded credentials
        password = os.environ.get('PERMIT_PASSWORD', 'phgxqaoqhbwvnmhi')
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Successfully sent alert email for {len(permits_found)} permits")
        return True
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
        return False

def notify_error(e: Exception, message: str = None, level: str = "ERROR", min_interval_minutes: int = 30) -> bool:
    # modify cooldown interval to prevent email flooding in line above
    """
    Send a notification email about an error that occurred.
    Limits notifications to one per specified time interval to prevent email flooding.
    
    Args:
        e: The exception that was raised
        message: Additional context about what was happening when the error occurred
        level: Severity level (ERROR, WARNING, INFO)
        min_interval_minutes: Minimum minutes between notifications
        
    Returns:
        Boolean indicating whether the notification was sent successfully
    """
    global _last_error_notification_time
    
    current_time = datetime.now()
    
    # Check if we've sent a notification recently
    if _last_error_notification_time is not None:
        time_since_last = (current_time - _last_error_notification_time).total_seconds() / 60
        
        # If it's been less than the minimum interval, just log and don't send
        if time_since_last < min_interval_minutes:
            logger.info(f"Skipping error notification - last one sent {time_since_last:.1f} minutes ago (cooldown: {min_interval_minutes} min)")
            return False
    
    try:
        # Create message context if none provided
        if message is None:
            message = "An error occurred in the permit checker"
            
        # Get full traceback
        error_traceback = traceback.format_exc()
        
        # Create the email
        msg = EmailMessage()
        
        # Format the subject based on error level
        subject_prefix = "🔴 CRITICAL" if level == "ERROR" else "🟠 WARNING" if level == "WARNING" else "🔵 INFO"
        msg['Subject'] = f'{subject_prefix} Permit Checker Alert'
        
        # Format the email body
        email_body = f"{message}\n\n"
        email_body += f"Error Type: {type(e).__name__}\n"
        email_body += f"Error Message: {str(e)}\n\n"
        email_body += f"Traceback:\n{error_traceback}\n\n"
        email_body += f"Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        msg.set_content(email_body)
        
        # Get email credentials
        sender_email = os.environ.get('PERMIT_EMAIL', 'govrecpermit@gmail.com')
        recipients = [
            os.environ.get('PERMIT_EMAIL', 'govrecpermit@gmail.com'),
            'owenriverk@gmail.com'
        ]
        
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipients)
        
        # Send the email
        password = os.environ.get('PERMIT_PASSWORD', 'phgxqaoqhbwvnmhi')
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        
        # Update the last notification time
        _last_error_notification_time = current_time
        
        logger.info(f"Successfully sent error notification email")
        return True
        
    except Exception as notification_error:
        # Log if we can't even send the notification
        logger.error(f"Failed to send error notification: {notification_error}")
        return False

def create_session_with_retries(
    retries=3,
    backoff_factor=0.5,
    status_forcelist=(500, 502, 503, 504, 429)
):
    """
    Create a requests session with automatic retries for failed requests.
    
    Args:
        retries: Number of retries to attempt
        backoff_factor: Factor to apply between retry attempts (exponential backoff)
        status_forcelist: HTTP status codes that should trigger a retry
    
    Returns:
        requests.Session: Session configured with retry mechanism
    """
    s = requests.Session()
    
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "HEAD", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    
    return s

def get_permit() -> List[str]:
    """
    Main function to check for permit availability on recreation.gov.
    
    This function:
    1. Loads previous permit data
    2. Fetches current availability for each section
    3. Compares to find cancellations or new availability
    4. Sends alerts for any found permits
    5. Saves the current data for future comparisons
    
    Returns:
        List of strings describing newly available permits
    """
    logger.info("Starting permit check")
    
    # List of user agents to rotate through to avoid detection
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    ]
    
    new_data = {}  # Will store the current availability data
    old_data = load_previous_data()  # Load previous data for comparison
    
    s = create_session_with_retries()  # Create a session with retry logic
    
    # Iterate through each river section defined in Permit class
    try:
        for sec in Permit.sections:
            try:
                # Select a random user agent for each request
                headers = {"User-Agent": random.choice(user_agents)}
                
                # Construct the API endpoint URL
                url = (f"https://www.recreation.gov/api/permits/{sec.permit}/availability")
                
                # Set up query parameters
                params = {
                    "start_date": sec.startdt,
                    "end_date": sec.enddt,
                    "commercial_acc": False,
                    "is_lottery": True
                }
                
                logger.info(f"Checking {sec.river} - {sec.sectionname}")
                
                # Make the API request
                r = s.get(url, params=params, headers=headers, timeout=(30, 60))
                
                if r.status_code == 200:
                    # If response is successful, parse the JSON data
                    data = r.json()
                    
                    # Get the division ID (typically only one per permit)
                    division_id = list(data['payload']['availability'].keys())[0]
                    
                    # Extract the availability information for each date
                    availability = {
                        date: date_info.get('remaining', 0)
                        for date, date_info in data['payload']['availability'][division_id]['date_availability'].items()
                    }
                    
                    # Store the availability data for this section
                    new_data[f'{sec.sectionname}'] = availability
                    logger.info(f"Successfully retrieved data for {sec.river} - {sec.sectionname}")
                else:
                    # Handle API request errors
                    logger.error(f'Error: {r.status_code} for {sec.river} - {sec.sectionname}')
                    
            except Exception as e:
                # Catch any exceptions during the request
                logger.error(f'Fetching error: {sec.river} - {sec.sectionname}: {e}')
                
        # Save the new data for future comparison
        save_previous_data(new_data)

        # Compare old and new data to find cancellations
        canceled_permits = find_canceled_permits(old_data, new_data)

        # Log and handle results
        if canceled_permits:
            logger.info(f"Found {len(canceled_permits)} canceled permits!")
            for permit in canceled_permits:
                logger.info(f"- {permit}")
            
            # Send email alert with the found permits
            send_alert(canceled_permits)
        else:
            logger.info("No cancellations detected.")

        # Create and log table data for debugging
        df = create_table(new_data)
        logger.debug("Permit Availability Data:\n" + str(df))

    except requests.exceptions.ConnectionError as e:
        # Network error - relatively common, use longer cooldown
        logger.error(f"Network error: {e}")
        notify_error(e, "Network error while checking permits", min_interval_minutes=60)
        return []
        
    except json.JSONDecodeError as e:
        # API returned invalid JSON - might indicate API changes
        logger.error(f"JSON parsing error: {e}")
        notify_error(e, "API returned invalid data format", min_interval_minutes=15)
        return []
        
    except Exception as e:
        # Unexpected error - notify immediately with shorter cooldown
        logger.error(f"Unexpected error in get_permit: {e}")
        notify_error(e, "Unexpected error during permit checking", min_interval_minutes=10)
        return []
    
    return canceled_permits
    
        
