from playwright.sync_api import sync_playwright
import json
import traceback
import datetime
import re



# Define dance class levels in order of length (longest first)
LEVELS = [
    "All Levels",
    "[MONTHLY] Beg",
    "[Guest] Adv Beg",
    "Beg/Adv Beg",
    "Adv Beg/Int",
    "Adv Beg",
    "[Pop Up] Open Level",
    "Open Level",
    "Open",
    "Basic",
    "Beg",
    "Int",
    "Foundations"
]
# Sort by length in descending order to match longest level first
LEVELS.sort(key=len, reverse=True)

def parse_level_and_style(input_str: str) -> tuple[str | None, str]:
    """
    Splits an input into a level and style. If no known level prefix matches,
    it tries to match a level at the end of the input string.
    """
    print("Input String:", input_str)

    # First, check if the level is at the beginning of the string
    for level in LEVELS:
        print(f"Checking if '{input_str[:len(level)]}' starts with '{level}'")  # Debug: Print the substring being checked
        if input_str.startswith(level):
            style = input_str[len(level):].strip()
            print(f"Matched! Level: '{level}', Style: '{style}'")
            return level, style

    # If no match at the beginning, check if the level is at the end
    for level in LEVELS:
        print(f"Checking if '{input_str}' ends with '{level}'")
        if input_str.endswith(level):
            style = input_str[:-len(level)].strip()  # Remove the level from the end
            print(f"Matched! Level: '{level}', Style: '{style}'")
            return level, style

    # Fallback: no recognized level prefix
    print("No match found!")
    return None, input_str

UNIFIED_LEVELS = {
    "Open Level": [
        "All Levels",
        "[Pop Up] Open Level",
        "Open Level",
        "Open",
    ],
    "Advanced Beginner": [
        "Adv Beg",
        "[Guest] Adv Beg",
        "Beg/Adv Beg",
        "Adv Beg/Int"
    ],
    "Basic": [
        "Basic",
        "Foundations"
    ],
    "Beginner": [
        "Beg",
        "[MONTHLY] Beg",
        "Beg/Adv Beg"
    ],
    "Intermediate": [
        "Int",
        "Adv Beg/Int"
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

def main():
    url = "https://www.versd.co/profile/pjm"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print("Navigating to PJM Dance NYC website...")
            page.goto(url, timeout=30000)
            print("Page loaded successfully")
            
            print(f"Current URL: {page.url}")
            page.screenshot(path="initial_page.png")
            print("Screenshot saved as 'initial_page.png'")
            
            # Wait for the page content to finish processing
            page.wait_for_selector("td[role='gridcell']", timeout=30000)
            print("Page content is fully loaded.")
            
            # Create a list to store all class data
            all_class_data = []
            
            # Function to extract class data from the current page
            def extract_data(date_element:str):
                class_elements = page.query_selector_all("td[role='gridcell'][style*='width: 100%'] > div > div")
                print(f"Found {len(class_elements)} class elements")
                
                day_class_data = []
                
                for i, class_element in enumerate(class_elements):
                    class_data = {
                        "time_start": "",
                        "time_end": "",
                        "style": "",
                        "level": "",    
                        "instructor": "",
                        "studio": "PJM",
                        "address": "LIC Art Center, 44-02 23rd St 3rd Fl, 309, Long Island City, NY 11101",
                        "link": "https://www.versd.co/profile/pjm",
                        "unified_level": "",
                        "description": ""
                    }
                    
                    # Extract data from each class element
                    time_element = class_element.query_selector("div > div > :nth-child(4)")
                    if time_element:
                        time_element = time_element.inner_text().strip()
                        print("Time Element: ", time_element)
                        time_parts = re.findall(r'(\d{1,2}:\d{2})(am|pm)?', time_element)
                        # Flatten the result so that 'pm' or 'am' is in its own element
                        flattened_time_parts = [item for sublist in time_parts for item in sublist if item]  # Flatten and remove empty values
                        print("Time Parts: ", flattened_time_parts)
                        time_start_string = flattened_time_parts[0] + flattened_time_parts[2]
                        print("Time Start: ", time_start_string)
                        time_start_obj = datetime.datetime.strptime(time_start_string, "%I:%M%p")
                        time_end_string = flattened_time_parts[1] + flattened_time_parts[2]
                        time_end_obj = datetime.datetime.strptime(time_end_string, "%I:%M%p")

                        # Remove known prefixes (like "Today,", "Yesterday,", etc.)
                        date_str = re.sub(r"^(Today|Tomorrow|Yesterday),\s*", "", date_element)
                        # Remove 'selected' from string 
                        date_str = date_str.replace(' selected', '')

                        date_obj = datetime.datetime.strptime(date_str, "%A, %B %d, %Y")

                        year = int(date_obj.year)
                        month = int(date_obj.month)
                        day = int(date_obj.day)
                        start_hour = int(time_start_obj.hour)
                        start_minute = int(time_start_obj.minute)
                        end_hour = int(time_end_obj.hour)
                        end_minute = int(time_end_obj.minute)

                        print("Time Start: " + str(time_start_obj.hour) + str(time_start_obj.minute))

                        time_start_date_object = datetime.datetime(
                            year,
                            month, 
                            day,
                            start_hour, 
                            start_minute
                        )

                        time_end_date_object = datetime.datetime(
                            year,
                            month,
                            day,
                            end_hour,
                            end_minute
                        )

                        time_start_iso_string = time_start_date_object.isoformat()
                        class_data["time_start"] = time_start_iso_string
                        print(f"    Time Start: {class_data['time_start']}")

                        time_end_iso_string = time_end_date_object.isoformat()
                        class_data["time_end"] = time_end_iso_string
                        print(f"    Time End: {class_data['time_end']}")


                                    

                    

                    
                    name_element = class_element.query_selector("div > div > a")
                    if name_element:
                        print("Name Element: " + name_element.inner_text().strip())
                        level, style = parse_level_and_style(name_element.inner_text().strip())
                        unified_level = match_unified_level(level)
                        class_data["level"] = level
                        class_data["style"] = style
                        class_data["unified_level"] = unified_level

                    
                    instructor_element = class_element.query_selector("div > div > :nth-child(2)")
                    if instructor_element:
                        instructor_text = instructor_element.inner_text().strip()
                        instructor_text = re.sub(r"Teacher:\s*\n?", "", instructor_text)
                        class_data["instructor"] = instructor_text

                      
                    
                    description_element = class_element.query_selector("div > div > :nth-child(3)")
                    if description_element:
                        class_data["description"] = description_element.inner_text().strip()       

                    day_class_data.append(class_data)
                
                return day_class_data

            def navigate_days():
                # Get all the grid cells (td elements with role="gridcell")
                days = page.query_selector_all('td[role="gridcell"]')[:-1]  # Exclude the last cell if it's not a day
                print("Number of gridcells:", len(days))

                # Loop through each of the 7 days
                for index, day in enumerate(days[:7]):  # We assume the first 7 are the days
                    print(f"Clicking on day {index + 1}...")

                    # Click the button inside the grid cell for the current day
                    day_button = day.query_selector('button')  # Assuming the button is inside the <td> element
                    if day_button:
                        print(f"Clicking on button for day {index + 1}")
                        day_button.click()
                        page.wait_for_selector('td[role="gridcell"][aria-selected="true"]')  # Wait for the day to be selected
                        page.wait_for_timeout(2000)  # Adding a 2-second delay to ensure the content is fully loaded
                        print(f"Day {index + 1} selected and loaded.")

                        # Extract the aria-label attribute instead of the inner text
                        date_element = day_button.get_attribute('aria-label').strip()
                        print("Date:", date_element)
                        # Ensure date_element is a string before passing to extract_data
                        if date_element:
                            day_class_data = extract_data(date_element)
                            all_class_data.extend(day_class_data)
                        else:
                            print("Date element is empty or None!")


                 

            
                        

                        # Save intermediate data to a file (optional)
                        with open("pjm_classes.json", "w", encoding="utf-8") as f:
                            json.dump(all_class_data, f, indent=2, ensure_ascii=False)

                        print(f"Day {index + 1} classes extracted. Total classes so far: {len(all_class_data)}")

                    else:
                        print(f"Button for day {index + 1} not found.")
                    
                # After going through all seven days, we have the full week's data.
                print(f"Week data collected for {index + 1} days.")
                


            
            def navigate_weeks():
                next_week_button = page.query_selector('button[aria-label="Next"]')
                next_week_button.click()
                print("Clicking to the next week")
                page.wait_for_timeout(2000)  # Adding a small delay to ensure the next week content is loaded
                page.wait_for_selector('td[role="gridcell"]', timeout=30000)  # Wait for the first day of the next week to load
                print("Week navigation complete")

            # Start the process of scraping classes for multiple weeks
            for week in range(1, 4):  # Adjust the range for more weeks if needed
                print(f"\nExtracting classes for Week {week}...")

                # Extract data for the entire week by navigating through all 7 days
                navigate_days()  # This will click through all 7 days of the current week

                # After extracting data for a week, navigate to the next week
                print(f"Week {week} complete. Moving to the next week...")
                navigate_weeks()

          
            
            # Save all the data to a single JSON file at the end
            print(f"\nSaving all extracted class data to pjm_classes.json...")
            with open("pjm_classes.json", "w", encoding="utf-8") as f:
                json.dump(all_class_data, f, indent=2, ensure_ascii=False)
            print("All data saved to pjm_classes.json")

            # Take a final screenshot of the last page
            page.screenshot(path="pjm_final_page.png")
            print("Screenshot of the final page saved as 'pjm_final_page.png'")

            input("Press Enter to close the browser window...")

        except Exception as e:
            print(f"An error occurred: {e}")
            print(traceback.format_exc())
            input("Press Enter to close the browser window...")
        finally:
            browser.close()
            print("Browser closed successfully")

if __name__ == "__main__":
    main()
