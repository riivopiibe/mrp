import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Debug helper
def debug(message):
    print(f"[DEBUG] {message}")

# Google Sheets Setup
def setup_sheets():
    debug("Setting up Google Sheets API...")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("Motorott products").sheet1
    return sheet

# Scrape sitemap
def scrape_sitemap(url):
    debug(f"Fetching sitemap from {url}...")
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'lxml')  # Use XML parser
    products = []

    debug("Parsing products...")
    for url in soup.find_all('url'):
        loc = url.find('loc').text if url.find('loc') else None
        lastmod = url.find('lastmod').text if url.find('lastmod') else None

        if loc and lastmod:
            products.append((loc, lastmod))
    
    debug(f"Found {len(products)} products.")
    return products

# Update Google Sheets
def update_sheet(sheet, products):
    debug("Reading existing URLs from Google Sheets...")
    data = sheet.get_all_records()
    url_to_row = {row['URL']: idx + 2 for idx, row in enumerate(data)}  # Map URL to row number

    for url, modified_date in products:
        debug(f"Checking product: {url} with modified date: {modified_date}")
        if url in url_to_row:
            row_idx = url_to_row[url]
            sheet_date = sheet.cell(row_idx, 2).value  # Second column: "Last modified"
            
            # Compare dates
            if datetime.strptime(modified_date, '%d/%m/%Y %H:%M') > datetime.strptime(sheet_date, '%d/%m/%Y %H:%M'):
                debug(f"Updating {url} in row {row_idx} with new modified date.")
                sheet.update_cell(row_idx, 2, modified_date)
            else:
                debug(f"No update needed for {url}.")
        else:
            # Add new product
            debug(f"Adding new product {url}.")
            sheet.append_row([url, modified_date])

# Main script
def main():
    try:
        debug("Starting script...")
        sheet = setup_sheets()
        sitemap_url = "https://pood.motorott.ee/product-sitemap.xml"
        products = scrape_sitemap(sitemap_url)
        update_sheet(sheet, products)
        debug("Script completed successfully.")
    except Exception as e:
        debug(f"Error: {e}")

if __name__ == "__main__":
    main()
