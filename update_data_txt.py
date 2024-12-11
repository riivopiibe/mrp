import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import base64
import json

# Debug function (optional for logging)
def debug(message):
    print(f"[DEBUG] {message}")

# Google Sheets Setup
def setup_sheets():
    debug("Setting up Google Sheets API...")
    
    # Decode credentials from environment variable
    credentials_content = os.getenv("CREDENTIALS_JSON")
    if not credentials_content:
        raise ValueError("Environment variable CREDENTIALS_JSON is not set.")
    
    decoded_credentials = base64.b64decode(credentials_content).decode("utf-8")
    credentials_dict = json.loads(decoded_credentials)

    # Authenticate Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)

    # Open Google Sheets by name
    sheet = client.open("Motorott products").sheet1  # Replace with your sheet's name
    return sheet

# Fetch data from Google Sheets
def fetch_data_from_google_sheets(sheet):
    debug("Fetching data from Google Sheets...")
    data = sheet.get_all_records()
    return data

# Format data into a text file
def format_data_to_txt(data, output_path):
    debug(f"Formatting data to {output_path}...")
    lines = []
    for row in data:
        lines.append(f"Title: {row['Title']}")
        lines.append(f"Price: {row['Price']}")
        lines.append(f"Stock: {row['Stock']}")
        lines.append(f"URL: {row['URL']}")
        lines.append("")  # Blank line for separation

    # Write to file
    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))
    debug("Data formatted successfully!")

if __name__ == "__main__":
    debug("Starting script...")
    
    try:
        # Set up Google Sheets API
        sheet = setup_sheets()
        
        # Fetch and format data
        data = fetch_data_from_google_sheets(sheet)
        output_file = "data.txt"
        format_data_to_txt(data, output_file)
        debug(f"Data saved to {output_file}")
    except Exception as e:
        print(f"[ERROR] {e}")
