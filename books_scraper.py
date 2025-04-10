from bs4 import BeautifulSoup
import requests

url = "https://books.toscrape.com/"

response = requests.get(url)

soup = BeautifulSoup(response.text, 'html.parser')

# Extract book informatin: Title, Price, Rating, Availability

# Find all books on the page
books = soup.find_all('article', class_='product_pod')

for book in books:
    title = book.find('h3').find('a')['title']
    price = book.find('p', class_='price_color').text
    rating = book.find('p', class_='star-rating')['class']
    availability = book.find('p', class_='instock availability').text.strip()

    print(f"Title: {title}")
    print(f"Price: {price}")
    print(f"Rating: {rating}")
    print(f"Availability: {availability}")
    print("\n")