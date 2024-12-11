import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# Google Sheets API setup
def fetch_data_from_google_sheets(sheet_url, credentials_path):
    # Set up the credentials
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(credentials)

    # Open the Google Sheet
    spreadsheet = client.open_by_url(sheet_url)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_records()
    return data

# Format the text file
def format_data_to_txt(data, output_path):
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

if __name__ == "__main__":
    # Replace with your Google Sheets URL
    sheet_url = os.getenv("https://docs.google.com/spreadsheets/d/1CmuKdsDSH5Qj1c51145bn6UTckIwLgZnpcnGW7kTRGQ/edit?usp=sharing")
    credentials_content = os.getenv("CREDENTIALS_JSON")

    # Write credentials to a temporary file
    temp_credentials_path = "credentials.json"
    if not credentials_content:
        raise ValueError("Environment variable CREDENTIALS_JSON is not set.")
    try:
        json.loads(credentials_content)  # Validate JSON content
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in CREDENTIALS_JSON.")

    with open(temp_credentials_path, "w") as temp_file:
        temp_file.write(credentials_content)

    # Output file location
    output_file = "data.txt"

    try:
        # Fetch data and format
        data = fetch_data_from_google_sheets(sheet_url, temp_credentials_path)
        format_data_to_txt(data, output_file)
        print(f"Updated {output_file}")
    finally:
        # Remove the temporary credentials file
        os.remove(temp_credentials_path)
