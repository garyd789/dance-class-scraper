from playwright.sync_api import sync_playwright
import time
import json
import os

print("Starting the Modega dance class scraper...")

try:
    with sync_playwright() as p:
        print("Launching browser in stealth mode...")
        # Launch a browser with stealth options to bypass Cloudflare
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        
        # Create a new context with specific viewport and user agent
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        # Create a new page from the context
        page = context.new_page()
        
        # Set additional headers to appear more like a regular browser
        page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        
        # Navigate to the Modega website
        print("Navigating to Modega website...")
        page.goto("https://sutrapro.com/modega")
        print("Page loaded successfully")
        
        # Print the current URL to verify we're on the right page
        print(f"Current URL: {page.url}")
        
        # Take a screenshot for debugging
        page.screenshot(path="initial_page.png")
        print("Screenshot saved as 'initial_page.png'")
        
        # Check if we're on a Cloudflare challenge page
        if "challenge" in page.url or page.query_selector("#challenge-error-text"):
            print("Detected Cloudflare challenge page. Waiting for it to resolve...")
            # Wait for the challenge to be resolved (up to 30 seconds)
            try:
                page.wait_for_url("**/modega", timeout=30000)
                print("Cloudflare challenge resolved successfully!")
            except Exception as e:
                print(f"Cloudflare challenge not resolved within timeout: {e}")
                print("Current page content:")
                print(page.content())
                page.screenshot(path="cloudflare_challenge.png")
                print("Screenshot of challenge page saved as 'cloudflare_challenge.png'")
                raise Exception("Failed to bypass Cloudflare security")
        
        # Check if the schedule table exists
        print("Looking for schedule table...")
        page.wait_for_selector("div.card-list__card-group")
        print("Schedule table found!")
        
        # Take a screenshot for debugging
        page.screenshot(path="modega_schedule_table.png")
        print("Screenshot of schedule table saved as 'modega_schedule_table.png'")

        for i in range(8):
            page.click("text=Show More")
        
        # Extract all day elements
        print("\nExtracting day elements...")
        day_elements = page.query_selector_all("div.card-list__card-group")
        print(f"Found {len(day_elements)} day elements")
        
        # Create a list to store all class data
        all_class_data = []
        
        # Extract data from all day elements
        for day_index, day_element in enumerate(day_elements):
            print(f"\nProcessing day {day_index + 1} of {len(day_elements)}...")
            
            # Get the date for this day
            date_element = day_element.query_selector("div.class-list__day")
            date_text = date_element.inner_text().strip() if date_element else "Unknown Date"
            print(f"Date: {date_text}")
            
            # Find all class cards within this day
            class_cards = day_element.query_selector_all("div.class-list__card")
            print(f"Found {len(class_cards)} class sessions for {date_text}")
            
            for card_index, card in enumerate(class_cards):
                print(f"  Processing class {card_index + 1} of {len(class_cards)}...")
                
                # Initialize class data
                class_data = {
                    "date": date_text,
                    "time": "",
                    "name": "",
                    "staff": "",
                    "room": "",
                    "instructor": "",
                    "instructor_bio": "",
                    "description": ""
                }
                
                # Extract class time
                time_element = card.query_selector("p.dateTimeText")
                if time_element:
                    class_data["time"] = time_element.inner_text().strip()
                    print(f"    Time: {class_data['time']}")
                
                # Extract class name
                name_element = card.query_selector("div.card-title")
                if name_element:
                    class_data["name"] = name_element.inner_text().strip()
                    print(f"    Name: {class_data['name']}")
                
                # Extract instructor
                instructor_element = card.query_selector("p.font-weight-bold")
                if instructor_element:
                    class_data["instructor"] = instructor_element.inner_text().strip()
                    print(f"    Instructor: {class_data['instructor']}")
                
                # Extract description
                description_element = card.query_selector("div.collapse show")
                if description_element:
                    class_data["description"] = description_element.inner_text().strip()
                    print(f"    Description: {class_data['description']}")
                
                # Add this class's data to our list
                all_class_data.append(class_data)
        
        # Print a summary of the extracted data
        print("\nSummary of extracted data:")
        print("-" * 30)
        print(f"Total days: {len(day_elements)}")
        print(f"Total classes: {len(all_class_data)}")
        
        # Save the data to a JSON file
        print("\nSaving data to modega_classes.json...")
        with open("modega_classes.json", "w", encoding="utf-8") as f:
            json.dump(all_class_data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to modega_classes.json")
        
        # Print a sample of the data
        print("\nSample of extracted data:")
        print("-" * 30)
        if all_class_data:
            sample = all_class_data[0]
            for key, value in sample.items():
                print(f"{key}: {value}")
        
        print("\nClosing browser...")
        browser.close()
        print("Browser closed successfully")

except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    print(traceback.format_exc())
