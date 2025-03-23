import requests
from dataclasses import dataclass
import pandas as pd
import json
import time
import random

from Permit import Permit, Section


def save_previous_data(data, filename="previous_permits.json"):
    with open(filename, "w") as f:
        json.dump(data, f)

def load_previous_data(filename="previous_permits.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}  # If no previous data exists, return empty dictionary

def find_canceled_permits(old_data, new_data):
    canceled_permits = []
    for section in new_data:
        if section in old_data:
            for date, new_value in new_data[section].items():
                if date in old_data[section]:
                    # If it went from 0 to some positive number, a cancellation occurred
                    if old_data[section][date] == 0 and new_value > 0:
                        canceled_permits.append(f"{section} - {date} - {new_value} permits available")
                # If the date doesn't exist in old_data but does in new_data, it's new availability
                else:
                    if new_value > 0:
                        canceled_permits.append(f"{section} - {date} - {new_value} permits available (new listing)")
        # If the section doesn't exist in old_data, all dates with availability are new
        else:
            for date, new_value in new_data[section].items():
                if new_value > 0:
                    canceled_permits.append(f"{section} - {date} - {new_value} permits available (new section)")
    
    return canceled_permits

def get_permit():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    ]
    headers = {"User-Agent": random.choice(user_agents)}
    
    new_data = {}
    old_data = load_previous_data()
    
    for sec in Permit.sections:
        try:
            url = (f"https://www.recreation.gov/api/permits/{sec.permit}/availability")
            params = {
                "start_date": sec.startdt,
                "end_date": sec.enddt,
                "commercial_acc": False,
                "is_lottery": True
            }
            r = requests.get(url, params = params, headers = headers)
            if r.status_code == 200:
                data = r.json()
                division_id = list(data['payload']['availability'].keys())[0]
                
                availability = {
                    date: date_info.get('remaining', 0)
                    for date, date_info in data['payload']['availability'][division_id]['date_availability'].items()
                }
                new_data[f'{sec.sectionname}'] = availability
            else:
                print(f'Error: {r.status_code} for {sec.river} - {sec.sectionname}')
            
        except Exception as e:
            print (f'fetching error: {sec.river} - {sec.sectionname}: {e}')
        
        time.sleep(5)


    save_previous_data(new_data)

    # Compare old and new data for cancellations
    canceled_permits = find_canceled_permits(old_data, new_data)

    # Display results
    if canceled_permits:
        print("Canceled Permits Found:")
        for permit in canceled_permits:
            print(f"- {permit}")
    else:
        print("No cancellations detected.")

    # Display the results in a table
    df = create_table(new_data)
    print("Permit Availability Data:")
    print(df)


def create_table(new_data):
    # Create an empty DataFrame
    df = pd.DataFrame()
    
    # For each section in your data
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