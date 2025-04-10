import requests
from bs4 import BeautifulSoup
import csv

def scrape_quotes():
    base_url = "http://quotes.toscrape.com"
    page_url = "/page/1/"
    quotes_data = []

    while page_url:
        print(f"Scraping {base_url + page_url}")
        response = requests.get(base_url + page_url)
        if response.status_code != 200:
            print(f"Failed to retrieve {base_url + page_url}")
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract quotes on the current page
        for quote_div in soup.find_all('div', class_='quote'):
            text = quote_div.find('span', class_='text').get_text(strip=True)
            author = quote_div.find('small', class_='author').get_text(strip=True)
            quotes_data.append({'text': text, 'author': author})
        
        # Check for next page
        next_button = soup.find('li', class_='next')
        if next_button:
            page_url = next_button.find('a')['href']
        else:
            page_url = None

    return quotes_data

def save_to_csv(quotes, filename='quotes.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['text', 'author'])
        writer.writeheader()
        for quote in quotes:
            writer.writerow(quote)
    print(f"Data successfully written to {filename}")

if __name__ == '__main__':
    quotes = scrape_quotes()
    print(f"Total quotes scraped: {len(quotes)}")
    save_to_csv(quotes)
