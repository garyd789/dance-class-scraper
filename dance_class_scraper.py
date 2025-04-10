from playwright.sync_api import sync_playwright
import time
import json
import os

print("Starting the dance class scraper...")

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
        
        # Navigate to the the schedule
        print("Navigating to Broadway Dance Center website...")
        page.goto("https://broadwaydancecenter.com/schedule/schedule-in-person", wait_until="networkidle")
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
                page.wait_for_url("**/in-person-classes", timeout=30000)
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
        page.wait_for_selector("div.bw-widget__sessions")
        print("Schedule table found!")
        
        # Take a screenshot for debugging
        page.screenshot(path="schedule_table.png")
        print("Screenshot of schedule table saved as 'schedule_table.png'")
        
        # Extract all date elements
        print("\nExtracting dates from the schedule...")
        date_elements = page.query_selector_all("div.bw-widget__date")
        print(f"Found {len(date_elements)} date elements")
        
        # Print each date
        print("\nSchedule Dates:")
        print("-" * 30)
        for i, date_element in enumerate(date_elements):
            date_text = date_element.inner_text().strip()
            print(f"{i+1}. {date_text}")
        
        # Also extract the day elements to see their structure
        print("\nExtracting day elements...")
        day_elements = page.query_selector_all("div.bw-widget__day")
        print(f"Found {len(day_elements)} day elements")
        
        # Create a list to store all class data
        all_class_data = []
        
        # Extract data from all day elements
        for day_index, day_element in enumerate(day_elements):
            print(f"\nProcessing day {day_index + 1} of {len(day_elements)}...")
            
            # Get the date for this day
            date_element = day_element.query_selector("div.bw-widget__date")
            date_text = date_element.inner_text().strip() if date_element else "Unknown Date"
            
            # Find all session elements within this day
            session_elements = day_element.query_selector_all("div.bw-session")
            print(f"Found {len(session_elements)} sessions for {date_text}")
            
            for session_index, session_element in enumerate(session_elements):
                print(f"  Processing session {session_index + 1} of {len(session_elements)}...")
                
                # Initialize session data
                session_data = {
                    "date": date_text,
                    "time": "",
                    "name": "",
                    "staff": "",
                    "room": "",
                    "instructor": "",
                    "instructor_bio": "",
                    "description": ""
                }
                
                # Extract session basics
                basics_element = session_element.query_selector("div.bw-session__basics")
                if basics_element:
                    # Extract time
                    time_element = basics_element.query_selector("span.hc_time")
                    if time_element:
                        session_data["time"] = time_element.inner_text().strip()
                    
                    # Extract name
                    name_element = basics_element.query_selector("div.bw-session__name")
                    if name_element:
                        session_data["name"] = name_element.inner_text().strip()
                    
                    # Extract staff
                    staff_element = basics_element.query_selector("div.bw-session__staff")
                    if staff_element:
                        session_data["staff"] = staff_element.inner_text().strip()
                
                # Extract session details
                details_element = session_element.query_selector("div.bw-session__details")
                if details_element:
                    # Extract room
                    room_element = details_element.query_selector("div.bw-session__room")
                    if room_element:
                        session_data["room"] = room_element.inner_text().strip()
                    
                    # Extract instructor
                    instructor_element = details_element.query_selector("div.bw-session__instructor")
                    if instructor_element:
                        session_data["instructor"] = instructor_element.inner_text().strip()

                    # Extract instructor bio
                    instructor_bio_element = details_element.query_selector("div.bw-session__bio")
                    if instructor_bio_element:
                        session_data["instructor_bio"] = instructor_bio_element.inner_text().strip()
                    
                    # Extract description
                    description_element = details_element.query_selector("div.bw-session__description")
                    if description_element:
                        session_data["description"] = description_element.inner_text().strip()
                
                # Add this session's data to our list
                all_class_data.append(session_data)
        
        # Save the data to a JSON file
        json_filename = "broadway_dance_classes.json"
        print(f"\nSaving {len(all_class_data)} class records to {json_filename}...")
        
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(all_class_data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"Data successfully saved to {json_filename}")
        
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
