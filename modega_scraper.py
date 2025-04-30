from playwright.sync_api import sync_playwright
import time
import json
import os
import datetime
from datetime import timedelta


def month_str_to_int(month_abbrev: str) -> int:
    lookup = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }

    key = month_abbrev.strip().lower()
    if key not in lookup:
        raise ValueError(f"Invalid month abbreviation: {month_abbrev!r}")
    return lookup[key]

def extract_number(s: str) -> int:
    digits = ''.join(ch for ch in s if ch.isdigit())
    if not digits:
        raise ValueError(f"No digits in {s!r}")
    return int(digits)


# Define dance class levels in order of length (longest first)
LEVELS = [
    "All Levels Floorwork",  # if you ever have multi-word levels like this
    "Adv. Beginner/Int.",
    "Beg./Adv, Beg.",
    "Beg/Adv. Beg.",
    "Beg./Adv.-Beg.",
    "Beg./Adv. Beginner",
    "Adv. Beginner/Int.",
    "Adv.-Beg./Int.",
    "Beg./Adv. Beginner",
    "Adv. Beginner/Int.",
    "Beg./Adv. Beg.",
    "All Levels",
    "Beg./Adv.",
    "Int./Adv.",
    "Beginner",
    "Intermediate",
    "Advanced",
    "Intro to",
    "Intro",
    "Open"

]
# Sort by length in descending order to match longest level first
LEVELS.sort(key=len, reverse=True)


# Mapping the levels to your descriptions
UNIFIED_LEVELS = {
    "Absolute Beginner": [
        "Beg./Adv. Beg.",
        "Beg./Adv.-Beg.",
        "Beg./Adv. Beginner",
        "Beginner"
    ],
    "Beginner": [
        "Beginner",
        "Beg./Adv, Beg.",
        "Beg./Adv.-Beg.",
        "Beg./Adv. Beginner"
    ],
    "Beginner/Intermediate": [
        "Beg./Adv. Beg.",
        "Beg./Adv.-Beg.",
        "Beg./Adv. Beginner",
        "Adv. Beginner/Int.",
        "Adv.-Beg./Int."
    ],
    "Intermediate": [
        "Intermediate",
        "Int./Adv.",
        "Adv. Beginner/Int.",
        "Adv.-Beg./Int."
    ],
    "Advanced Beginner": [
        "Adv. Beginner/Int.",
        "Adv.-Beg./Int.",
        "Adv. Beginner",
        "Beg./Adv. Beg."
    ],
    "Advanced Intermediate": [
        "Adv. Beginner/Int.",
        "Adv.-Beg./Int.",
        "Int./Adv."
    ],
    "Advanced": [
        "Advanced",
        "Int./Adv.",
    ],
    "Professional": [
        "Advanced"
    ],
    "Open Level": [
        "All Levels",
        "All Levels Floorwork",
        "Open"
    ],
    "Intro": [
        "Intro",
        "Intro to"
    ],
    "Basic": [
        "Basic"
    ]
}

def match_unified_level(input_str: str) -> str:
    unified_levels = []
    # Get the associated unified levels for the given description
    for unified_level, level in UNIFIED_LEVELS.items():
        for level in level:
            if input_str == level:
                unified_levels.append(unified_level)
    return unified_levels



def parse_level_and_style(input_str: str) -> tuple[str | None, str]:
    """
    Splits an input like "Beg./Adv. Beginner Choreography" into:
      level = "Beg./Adv."
      style = "Beginner Choreography"
    Or returns (None, input_str) if no known level prefix matches.
    """
    for level in LEVELS:
        if input_str.startswith(level):
            style = input_str[len(level):].strip()
            return level, style

    # fallback: no recognized level prefix
    return None, input_str


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
            day_text, month_text, date_text = date_text.split()
            year_text = datetime.datetime.now().year

            print(f"Day: {day_text} Date: {month_text}, {date_text}, {year_text}")
            
            # Find all class cards within this day
            class_cards = day_element.query_selector_all("div.class-list__card")
            print(f"Found {len(class_cards)} class sessions for {date_text}")
            
            for card_index, card in enumerate(class_cards):
                print(f"  Processing class {card_index + 1} of {len(class_cards)}...")
                
                # Initialize class data
                class_data = {
                    "time_start": date_text,
                    "time_end": "",
                    "style": "",
                    "level": "",
                    "instructor": "",
                    "studio": "Modega",
                    "address": "11-05 44th Ave, Queens, NY 11101",
                    "link":"",
                    "description": "",
                    "unified_level": ""
                }
                
                # Extract class time
                time_element = card.query_selector("p.dateTimeText")
                if time_element:
                    time_element = time_element.inner_text().strip()
                    # Split to get just the time part
                    time_duration = int((time_element.split("•")[1].strip()).split()[0][1:])
                    time_element = time_element.split("•")[0].strip()
                    # Drop the time zone token
                    time_element = " ".join(time_element.split()[:2])
                    # Turn into datetime object
                    time_obj = datetime.datetime.strptime(time_element, "%I:%M %p")

                    year = int(year_text)
                    month = int(month_str_to_int(month_text))
                    day = int(extract_number(date_text))
                    hour = int(time_obj.hour)
                    minute = int(time_obj.minute)
                
                    
                    time_start_oject = datetime.datetime(
                        year,
                        month,
                        day,
                        hour,
                        minute
                    )

                    time_start_iso_string = time_start_oject.isoformat()
                    class_data["time_start"] = time_start_iso_string

                    time_end_object = time_start_oject + timedelta(minutes=time_duration)
                    time_end_iso_string = time_end_object.isoformat()
                    class_data["time_end"] = time_end_iso_string

                    print(f"    Time Start: {class_data['time_start']}")
                    print(f"    Time End: {class_data['time_end']}")
                
                #Extract class link
                link_element = card.query_selector("a.btn")
                if link_element:
                    href = link_element.get_attribute("href")
                    if href:
                        class_data["link"] = href
                        print(f"    Link: {class_data['link']}")
                
                # Extract class name
                name_element = card.query_selector("div.card-title")
                if name_element:
                    name_text = name_element.inner_text().strip()
                    level, style = parse_level_and_style(name_text)
                    unified_level = match_unified_level(level)
                    class_data["style"] = style
                    class_data["level"] = level
                    class_data["unified_level"] = unified_level
                    print(f"   Style and Level: {class_data['level']} {class_data['style']}")
                
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

