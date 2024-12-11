import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
import os

# Debug helper
def debug(message):
    print(f"[DEBUG] {message}")

# Google Sheets Setup
def setup_sheets():
    debug("Setting up Google Sheets API...")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Motorott products").sheet1
    return sheet

# Scrape product details
def scrape_product_details(url):
    debug(f"Scraping details for: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title
        title_elem = soup.find('h1', class_='product_title')
        title = title_elem.text.strip() if title_elem else "N/A"
        
        # Get price
        price_elem = soup.find('p', class_='price')
        price = price_elem.text.strip().replace(" KM", "") if price_elem else "N/A"
        
        # Get stock status
        stock = "N/A"
        stock_elem = soup.find('p', class_='stock')
        if stock_elem:
            if 'out-of-stock' in stock_elem.get('class', []):
                stock = "Laost otsas"
            elif 'available-on-backorder' in stock_elem.get('class', []):
                stock = "Saadaval järeltellimisel"
            elif 'in-stock' in stock_elem.get('class', []):
                stock = stock_elem.text.strip()
        
        return {
            'title': title,
            'price': price,
            'stock': stock
        }
    except Exception as e:
        debug(f"Error scraping product details: {e}")
        return None

# Scrape sitemap
def scrape_sitemap(url):
    debug(f"Fetching sitemap from {url}...")
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'xml')
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
        debug(f"Processing product: {url}")
        
        if url in url_to_row:
            row_idx = url_to_row[url]
            sheet_date = sheet.cell(row_idx, 2).value  # Second column: "Last modified"
            
            # Compare dates
            modified_dt = parse_date(modified_date)
            sheet_dt = parse_date(sheet_date)

            if modified_dt and sheet_dt and modified_dt > sheet_dt:
                debug(f"Update needed for {url}")
                # Scrape new details
                details = scrape_product_details(url)
                if details:
                    # Update all columns
                    sheet.update(
                        values=[[modified_date, details['title'], details['price'], details['stock']]], 
                        range_name=f'B{row_idx}:E{row_idx}'
                    )
                    time.sleep(1)  # Avoid rate limiting
            else:
                debug(f"No update needed for {url}")
        else:
            # Add new product
            debug(f"Adding new product {url}")
            details = scrape_product_details(url)
            if details:
                sheet.append_row([
                    url,
                    modified_date,
                    details['title'],
                    details['price'],
                    details['stock']
                ])
                time.sleep(1)  # Avoid rate limiting

def parse_date(date_str):
    try:
        # Handle ISO 8601 date
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.replace(tzinfo=None)  # Convert to naive
    except ValueError:
        try:
            # Handle 'DD/MM/YYYY HH:MM'
            return datetime.strptime(date_str, '%d/%m/%Y %H:%M')
        except ValueError:
            debug(f"Error: Unable to parse date '{date_str}'")
            return None

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
